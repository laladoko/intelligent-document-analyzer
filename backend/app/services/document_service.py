import os
import tempfile
from typing import List, Dict, Any, Optional
import PyPDF2
import docx
from lxml import etree
import openai
from datetime import datetime
from dotenv import load_dotenv
import time
import logging
import asyncio

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

# 导入防阻塞配置
from app.config.anti_blocking_config import (
    openai_circuit_breaker, config, with_timeout_and_fallback
)

def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否被允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path: str, filename: str) -> str:
    """从不同格式的文件中提取文本"""
    file_extension = filename.rsplit('.', 1)[1].lower()
    
    try:
        if file_extension == 'txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        
        elif file_extension == 'pdf':
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        
        elif file_extension in ['docx', 'doc']:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
    
    except Exception as e:
        logger.error(f"文件读取错误: {str(e)}")
        raise Exception(f"文件读取错误: {str(e)}")

# 异步OpenAI客户端
async def get_openai_client() -> Optional[openai.AsyncOpenAI]:
    """获取异步OpenAI客户端"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    
    return openai.AsyncOpenAI(
        api_key=api_key,
        timeout=config.OPENAI_TIMEOUT,
        max_retries=config.MAX_RETRIES
    )

async def analyze_with_openai(text: str) -> str:
    """使用OpenAI GPT-4o分析文档内容，简化版本便于测试"""
    
    # 降级响应 - 当AI不可用时的默认分析
    async def get_fallback_analysis(text: str) -> str:
        word_count = len(text)
        return f"""
公司名称：未知（文档分析中未明确提及）

主要业务：基于文档内容，这是一份企业相关文档，包含业务信息、培训内容或管理制度等内容。

关键特色：
- 文档字数约 {word_count} 字符
- 包含结构化的企业信息
- 涉及业务流程或培训内容

服务对象：企业内部员工或相关业务人员

📝 注意：此分析为系统默认生成（AI服务暂时不可用）。如需完整AI分析，请稍后重试。
"""

    # 快速检查 - 如果文本过短，直接返回降级响应
    if len(text.strip()) < 20:
        return await get_fallback_analysis(text)
    
    # 简化版本：直接调用OpenAI API
    try:
        client = await get_openai_client()
        if not client:
            logger.warning("OpenAI客户端未配置，使用降级分析")
            return await get_fallback_analysis(text)
        
        # 文本长度控制
        max_text_length = 2000
        if len(text) > max_text_length:
            text_to_analyze = text[:max_text_length] + "\n\n[文档内容因长度限制已截断...]"
        else:
            text_to_analyze = text
        
        logger.info("开始OpenAI智能分析（简化版本）")
        
        # 直接调用，设置合理超时
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": """你是专业的企业文档分析专家。请分析文档并按格式输出：

公司名称：[公司名称或"未知"]
主要业务：[核心业务描述]
关键特色：[主要特色列表]
服务对象：[目标客户]

要求简洁、准确、专业。"""
                    },
                    {
                        "role": "user", 
                        "content": f"请分析以下企业文档：\n\n{text_to_analyze}"
                    }
                ],
                max_tokens=800,
                temperature=0.1
            ),
            timeout=25.0  # 25秒超时
        )
        
        logger.info("OpenAI智能分析完成")
        return response.choices[0].message.content
        
    except asyncio.TimeoutError:
        logger.warning("OpenAI API调用超时")
        return await get_fallback_analysis(text) + "\n\n⚠️ API调用超时，请稍后重试"
        
    except openai.RateLimitError as e:
        logger.warning(f"OpenAI API限流: {e}")
        return await get_fallback_analysis(text) + "\n\n⚠️ API调用限流，请稍后重试"
        
    except Exception as e:
        logger.error(f"OpenAI API调用失败: {type(e).__name__}: {e}")
        return await get_fallback_analysis(text) + f"\n\n⚠️ 分析失败: {type(e).__name__}"

async def analyze_with_openai_xml(text: str) -> str:
    """使用OpenAI分析文档并输出XML格式，带防阻塞保护"""
    
    # 降级XML响应
    async def get_fallback_xml_analysis(text: str) -> str:
        word_count = len(text)
        return f"""
<enterprise_info>
    <basic_info>
        <company_name>未知（文档中未明确提及）</company_name>
        <main_business>企业文档，包含业务或培训相关内容</main_business>
    </basic_info>
    <key_features>
        <feature>文档字数约 {word_count} 字符</feature>
        <feature>包含结构化企业信息</feature>
        <feature>涉及业务流程或培训内容</feature>
    </key_features>
    <target_customers>企业内部员工或业务相关人员</target_customers>
    <analysis_note>系统默认分析（AI服务暂时不可用）</analysis_note>
</enterprise_info>
"""

    # 快速检查
    if len(text.strip()) < 50:
        return await get_fallback_xml_analysis(text)
    
    # 异步XML分析函数
    async def _openai_xml_analysis():
        client = await get_openai_client()
        if not client:
            logger.warning("OpenAI客户端未配置，使用降级XML分析")
            return await get_fallback_xml_analysis(text)
        
        # 文本长度控制
        max_text_length = 4000
        if len(text) > max_text_length:
            text_to_analyze = text[:max_text_length] + "\n\n[文档内容因长度限制已截断...]"
        else:
            text_to_analyze = text
        
        logger.info("开始OpenAI XML智能分析")
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": """你是专业的企业文档分析专家。请分析文档并输出详细的XML格式企业信息。

输出XML格式要求：
<enterprise_info>
    <basic_info>
        <company_name>公司名称或"未知"</company_name>
        <main_business>详细的主要业务描述</main_business>
        <establishment_info>成立信息（如有）</establishment_info>
    </basic_info>
    <key_features>
        <feature>主要特色1</feature>
        <feature>主要特色2</feature>
        <feature>主要特色3</feature>
    </key_features>
    <target_customers>目标客户群体描述</target_customers>
    <services>
        <service>具体服务内容1</service>
        <service>具体服务内容2</service>
    </services>
    <additional_info>其他重要信息</additional_info>
</enterprise_info>

请确保XML格式正确，内容详细专业。"""
                },
                {
                    "role": "user", 
                    "content": f"请分析以下企业文档并输出详细的XML格式信息：\n\n{text_to_analyze}"
                }
            ],
            max_tokens=1500,
            temperature=0.2
        )
        
        logger.info("OpenAI XML智能分析完成")
        return response.choices[0].message.content
    
    # 使用熔断器保护的XML分析
    try:
        return await openai_circuit_breaker.call(
            with_timeout_and_fallback,
            _openai_xml_analysis,
            config.OPENAI_TIMEOUT,
            get_fallback_xml_analysis,
            text
        )
    except Exception as e:
        logger.warning(f"OpenAI XML分析完全失败: {str(e)}")
        return await get_fallback_xml_analysis(text)

# 保持向后兼容的同步接口
def analyze_with_openai_sync(text: str) -> str:
    """同步版本的OpenAI分析（向后兼容）"""
    try:
        return asyncio.run(analyze_with_openai(text))
    except Exception as e:
        logger.error(f"同步OpenAI分析失败: {e}")
        word_count = len(text)
        return f"""
公司名称：未知（分析失败）

主要业务：文档分析暂时不可用

关键特色：
- 文档字数约 {word_count} 字符
- 系统繁忙，请稍后重试

服务对象：企业用户

📝 注意：系统繁忙，请稍后重试分析功能。
"""

def analyze_with_openai_xml_sync(text: str) -> str:
    """同步版本的OpenAI XML分析（向后兼容）"""
    try:
        return asyncio.run(analyze_with_openai_xml(text))
    except Exception as e:
        logger.error(f"同步OpenAI XML分析失败: {e}")
        return """
<enterprise_info>
    <basic_info>
        <company_name>未知（分析失败）</company_name>
        <main_business>文档分析暂时不可用</main_business>
    </basic_info>
    <key_features>
        <feature>系统繁忙，请稍后重试</feature>
    </key_features>
    <target_customers>企业用户</target_customers>
    <analysis_note>系统繁忙，请稍后重试分析功能</analysis_note>
</enterprise_info>
"""

def generate_xml_summary(filename: str, original_text: str, ai_summary: str) -> str:
    """生成XML格式的分析摘要"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    word_count = len(original_text)
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<document_analysis>
    <metadata>
        <filename>{filename}</filename>
        <analysis_time>{timestamp}</analysis_time>
        <word_count>{word_count}</word_count>
        <model>gpt-4o</model>
    </metadata>
    <analysis_result>
        <![CDATA[{ai_summary}]]>
    </analysis_result>
</document_analysis>"""
    
    return xml_content

def combine_texts_for_analysis(all_texts: List[str]) -> str:
    """合并多个文档的文本内容用于批量分析"""
    combined = "\n\n=== 文档分隔符 ===\n\n".join(all_texts)
    return combined

def generate_batch_xml_summary(all_texts: List[str], ai_summary: str, total_word_count: int) -> str:
    """生成批量分析的XML格式摘要"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<batch_document_analysis>
    <metadata>
        <analysis_time>{timestamp}</analysis_time>
        <total_documents>{len(all_texts)}</total_documents>
        <total_word_count>{total_word_count}</total_word_count>
        <model>gpt-4o</model>
    </metadata>
    <combined_analysis_result>
        <![CDATA[{ai_summary}]]>
    </combined_analysis_result>
</batch_document_analysis>"""
    
    return xml_content 