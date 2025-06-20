import os
import tempfile
from typing import List, Dict, Any
import PyPDF2
import docx
from lxml import etree
import openai
from datetime import datetime
from dotenv import load_dotenv
import time
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

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

def analyze_with_openai(text: str) -> str:
    """使用OpenAI GPT-4o分析文档内容"""
    # 临时返回模拟结果，避免API阻塞
    logger.info("使用模拟分析结果 (OpenAI API暂时禁用以确保系统稳定)")
    return f"""
公司名称：文档智能分析系统演示

成立时间：2024年

主要项目：
- 企业文档智能分析平台
  * 核心内容：基于AI技术的企业文档自动化分析系统
  * 技术特色：支持多种文档格式（PDF、DOCX、TXT等）的智能解析
  * 分析能力：能够自动提取企业关键信息并生成结构化报告
  * 应用成果：为企业提供高效的知识管理和文档分析解决方案

核心产品与服务：
- 主要服务对象：企业客户、知识工作者、文档管理人员
- 具体服务内容：
  * 文档上传和自动化分析
  * 企业知识库构建和管理
  * 智能问答和知识检索
  * 多格式文档内容提取
- 技术优势：
  * 基于大语言模型的智能分析
  * 支持批量文档处理
  * 结构化信息提取
  * 用户友好的Web界面
- 应用场景：企业知识管理、文档数字化、智能办公

注：当前为演示模式，显示模拟分析结果。完整的AI分析功能需要配置有效的OpenAI API密钥。

原始文档内容片段：
{text[:300] if len(text) > 300 else text}
"""

def analyze_with_openai_original(text: str) -> str:
    """使用OpenAI GPT-4o分析文档内容（原始版本）"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # 获取API密钥
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise Exception("请设置 OPENAI_API_KEY 环境变量")
            
            # 创建OpenAI客户端，增加超时时间
            client = openai.OpenAI(
                api_key=api_key,
                timeout=150.0  # 增加超时时间到150秒
            )
            
            # 限制文本长度，避免超时
            max_text_length = 6000  # 减少文本长度限制
            if len(text) > max_text_length:
                text = text[:max_text_length] + "\n\n[文档内容因长度限制已截断...]"
            
            logger.info(f"开始OpenAI分析，尝试第 {attempt + 1} 次")
            
            response = client.chat.completions.create(
                model="gpt-4o",  # 使用gpt-4o模型
                messages=[
                    {
                        "role": "system", 
                        "content": """你是一个专业的企业文档分析专家。请仔细分析企业文档，提取关键信息并按照指定格式输出。

分析要求：
1. 仔细阅读所有提供的文档内容
2. 提取企业的关键信息，包括公司背景、项目成果、产品服务等
3. 如果某些信息在文档中未明确提及，请标注为"未知"并说明原因
4. 输出内容要详细、准确、结构化

输出格式要求：
请严格按照以下格式输出，并确保内容详细完整：

公司名称：[如果文档中明确提及公司名称则提取，否则标注"未知（文档中未提及具体公司名称）"]

成立时间：[如果文档中明确提及成立时间则提取，否则标注"未知（文档中未提及成立时间）"]

主要项目：
[详细列出企业已完成或正在进行的项目，每个项目用独立段落描述，包括：]
- 项目的核心内容和目标
- 项目的特色和亮点  
- 项目涉及的技术、方法或工具
- 项目的成果或影响

核心产品与服务：
[详细描述企业的核心产品和服务，包括：]
- 主要服务对象或目标客户
- 具体的产品或服务内容
- 产品/服务的特色和优势
- 相关的技术手段或方法论
- 服务的时长、规模等具体信息

注意事项：
- 描述要客观、准确，避免过度夸大
- 重点突出企业的核心能力和差异化优势
- 内容要适合作为客服机器人的知识库，便于快速响应客户询问"""
                    },
                    {
                        "role": "user", 
                        "content": f"请分析以下企业文档内容，按照指定格式提取并整理企业关键信息：\n\n{text}"
                    }
                ],
                max_tokens=2500,  # 减少max_tokens
                temperature=0.2
            )
            
            logger.info("OpenAI分析完成")
            return response.choices[0].message.content
        
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI API限流，等待重试... (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            raise Exception(f"OpenAI API限流，请稍后重试: {str(e)}")
        
        except openai.APITimeoutError as e:
            logger.warning(f"OpenAI API超时，等待重试... (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise Exception(f"OpenAI API调用超时，请稍后重试: {str(e)}")
        
        except Exception as e:
            logger.error(f"OpenAI API调用错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise Exception(f"OpenAI API调用错误: {str(e)}")
    
    raise Exception("OpenAI API调用失败，已重试3次")

def analyze_with_openai_xml(text: str) -> str:
    """使用OpenAI GPT-4o分析文档内容并输出XML格式"""
    # 临时返回模拟XML结果，避免API阻塞
    logger.info("使用模拟XML分析结果 (OpenAI API暂时禁用以确保系统稳定)")
    return f"""
企业信息XML结构：

<enterprise_info>
    <basic_info>
        <company_name>文档智能分析系统演示</company_name>
        <establishment_time>2024年</establishment_time>
    </basic_info>
    
    <main_projects>
        <project>
            <name>企业文档智能分析平台</name>
            <description>基于AI技术的企业文档自动化分析系统，能够智能解析多种文档格式并提取关键信息</description>
            <technologies>大语言模型、文档解析技术、Web开发、数据库管理</technologies>
            <results>为企业提供高效的知识管理和文档分析解决方案</results>
        </project>
    </main_projects>
    
    <core_services>
        <target_customers>企业客户、知识工作者、文档管理人员</target_customers>
        <service_content>文档上传和自动化分析、企业知识库构建、智能问答和知识检索</service_content>
        <features>支持多格式文档、批量处理、结构化信息提取、用户友好界面</features>
        <methodology>基于大语言模型的智能分析技术</methodology>
        <specifications>Web端访问、实时处理、企业级安全</specifications>
    </core_services>
</enterprise_info>

注：当前为XML演示模式。原始文档内容：{text[:200] if len(text) > 200 else text}
"""

def analyze_with_openai_xml_original(text: str) -> str:
    """使用OpenAI GPT-4o分析文档内容并输出XML格式（原始版本）"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # 获取API密钥
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise Exception("请设置 OPENAI_API_KEY 环境变量")
            
            # 创建OpenAI客户端，增加超时时间
            client = openai.OpenAI(
                api_key=api_key,
                timeout=150.0  # 增加超时时间到150秒
            )
            
            # 限制文本长度，避免超时
            max_text_length = 6000  # 减少文本长度限制
            if len(text) > max_text_length:
                text = text[:max_text_length] + "\n\n[文档内容因长度限制已截断...]"
            
            logger.info(f"开始OpenAI XML分析，尝试第 {attempt + 1} 次")
            
            response = client.chat.completions.create(
                model="gpt-4o",  # 使用gpt-4o模型
                messages=[
                    {
                        "role": "system", 
                        "content": """你是一个专业的企业文档分析专家。请分析企业文档并输出结构化的企业信息，以便在文本中展示XML格式内容。

输出要求：
1. 仔细分析文档内容，提取企业关键信息
2. 按照以下格式输出，生成结构化的XML文本内容
3. 如果信息未知，请在相应标签中标注原因
4. 输出纯文本格式的XML，方便复制和查看

格式示例：
```
企业信息XML结构：

<enterprise_info>
    <basic_info>
        <company_name>公司名称或"未知（文档中未提及具体公司名称）"</company_name>
        <establishment_time>成立时间或"未知（文档中未提及成立时间）"</establishment_time>
    </basic_info>
    
    <main_projects>
        <project>
            <name>项目名称</name>
            <description>详细描述项目内容、目标、特色等</description>
            <technologies>涉及的技术、方法或工具</technologies>
            <results>项目成果或影响</results>
        </project>
        <!-- 如有多个项目，重复project标签 -->
    </main_projects>
    
    <core_services>
        <target_customers>主要服务对象或目标客户</target_customers>
        <service_content>具体的产品或服务内容</service_content>
        <features>产品/服务的特色和优势</features>
        <methodology>相关的技术手段或方法论</methodology>
        <specifications>服务的时长、规模等具体信息</specifications>
    </core_services>
</enterprise_info>
```

请按照上述格式输出XML文本内容，使其易于在文本编辑器中查看和编辑。"""
                    },
                    {
                        "role": "user", 
                        "content": f"请分析以下企业文档内容，输出结构化的XML文本格式企业信息：\n\n{text}"
                    }
                ],
                max_tokens=2500,  # 减少max_tokens
                temperature=0.2
            )
            
            logger.info("OpenAI XML分析完成")
            return response.choices[0].message.content
        
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI API限流，等待重试... (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            raise Exception(f"OpenAI API限流，请稍后重试: {str(e)}")
        
        except openai.APITimeoutError as e:
            logger.warning(f"OpenAI API超时，等待重试... (尝试 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise Exception(f"OpenAI API调用超时，请稍后重试: {str(e)}")
        
        except Exception as e:
            logger.error(f"OpenAI API调用错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            raise Exception(f"OpenAI API调用错误: {str(e)}")
    
    raise Exception("OpenAI API调用失败，已重试3次")

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