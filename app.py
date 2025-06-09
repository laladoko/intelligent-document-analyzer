import os
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import openai
from dotenv import load_dotenv
import PyPDF2
import docx
from lxml import etree
import json
from datetime import datetime

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('results', exist_ok=True)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path, filename):
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
        raise Exception(f"文件读取错误: {str(e)}")

def analyze_with_openai(text):
    """使用OpenAI分析文档内容"""
    try:
        # 获取API密钥
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception("请设置 OPENAI_API_KEY 环境变量")
        
        # 创建OpenAI客户端
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "你是一个文档分析专家。请分析提供的文档内容，提取关键信息，包括：主题、核心观点、重要细节、结论等。请用简洁明了的中文回复。"
                },
                {
                    "role": "user", 
                    "content": f"请分析以下文档内容并提取核心信息：\n\n{text[:4000]}..."  # 限制长度避免token超限
                }
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        raise Exception(f"OpenAI API调用错误: {str(e)}")

def generate_xml_summary(filename, original_text, ai_summary):
    """将分析结果生成XML格式文件"""
    root = etree.Element("document_analysis")
    
    # 基本信息
    metadata = etree.SubElement(root, "metadata")
    etree.SubElement(metadata, "filename").text = filename
    etree.SubElement(metadata, "analysis_date").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    etree.SubElement(metadata, "file_size").text = str(len(original_text))
    
    # 原文档信息
    original = etree.SubElement(root, "original_content")
    etree.SubElement(original, "text_preview").text = original_text[:500] + "..." if len(original_text) > 500 else original_text
    etree.SubElement(original, "word_count").text = str(len(original_text.split()))
    
    # AI分析结果
    analysis = etree.SubElement(root, "ai_analysis")
    etree.SubElement(analysis, "summary").text = ai_summary
    etree.SubElement(analysis, "model_used").text = "gpt-3.5-turbo"
    
    # 格式化XML
    xml_str = etree.tostring(root, pretty_print=True, encoding='unicode')
    return xml_str

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式，请上传 TXT、PDF、DOCX 文件'}), 400
    
    try:
        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 提取文本内容
        text_content = extract_text_from_file(file_path, filename)
        
        if not text_content.strip():
            return jsonify({'error': '文件内容为空或无法读取'}), 400
        
        # 使用OpenAI分析
        ai_summary = analyze_with_openai(text_content)
        
        # 生成XML格式结果
        xml_content = generate_xml_summary(filename, text_content, ai_summary)
        
        # 保存XML文件
        xml_filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename.rsplit('.', 1)[0]}.xml"
        xml_path = os.path.join('results', xml_filename)
        
        with open(xml_path, 'w', encoding='utf-8') as xml_file:
            xml_file.write(xml_content)
        
        # 清理上传的原文件
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': '文档分析完成',
            'xml_file': xml_filename,
            'summary': ai_summary
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """下载生成的XML文件"""
    try:
        file_path = os.path.join('results', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def list_results():
    """列出所有分析结果文件"""
    try:
        files = []
        for filename in os.listdir('results'):
            if filename.endswith('.xml'):
                file_path = os.path.join('results', filename)
                stat = os.stat(file_path)
                files.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        files.sort(key=lambda x: x['created'], reverse=True)
        return jsonify(files)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/batch_upload', methods=['POST'])
def batch_upload_files():
    """批量上传文件并生成单个综合分析XML"""
    if 'files' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    files = request.files.getlist('files')
    if len(files) == 0:
        return jsonify({'error': '没有选择文件'}), 400
    
    try:
        all_texts = []
        file_summaries = []
        total_word_count = 0
        
        # 处理每个文件
        for file in files:
            if file.filename == '':
                continue
                
            if not allowed_file(file.filename):
                return jsonify({'error': f'文件 "{file.filename}" 格式不支持，请上传 TXT、PDF、DOCX 文件'}), 400
            
            # 保存临时文件
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
            file.save(file_path)
            
            try:
                # 提取文本内容
                text_content = extract_text_from_file(file_path, filename)
                
                if not text_content.strip():
                    return jsonify({'error': f'文件 "{filename}" 内容为空或无法读取'}), 400
                
                # 添加到总文本中
                all_texts.append({
                    'filename': filename,
                    'content': text_content,
                    'word_count': len(text_content.split())
                })
                
                total_word_count += len(text_content.split())
                
                # 清理临时文件
                os.remove(file_path)
                
            except Exception as e:
                # 清理临时文件
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({'error': f'处理文件 "{filename}" 时出错: {str(e)}'}), 500
        
        if len(all_texts) == 0:
            return jsonify({'error': '没有有效的文件内容'}), 400
        
        # 合并所有文本内容进行分析
        combined_content = combine_texts_for_analysis(all_texts)
        
        # 使用OpenAI分析合并后的内容
        ai_summary = analyze_with_openai(combined_content)
        
        # 生成综合XML格式结果
        xml_content = generate_batch_xml_summary(all_texts, ai_summary, total_word_count)
        
        # 保存XML文件
        xml_filename = f"batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(all_texts)}files.xml"
        xml_path = os.path.join('results', xml_filename)
        
        with open(xml_path, 'w', encoding='utf-8') as xml_file:
            xml_file.write(xml_content)
        
        return jsonify({
            'success': True,
            'message': f'批量文档分析完成，共处理 {len(all_texts)} 个文件',
            'xml_file': xml_filename,
            'summary': ai_summary,
            'file_count': len(all_texts),
            'total_words': total_word_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def combine_texts_for_analysis(all_texts):
    """将多个文件的内容合并为适合AI分析的格式"""
    combined = "以下是需要综合分析的多个文档内容：\n\n"
    
    for i, text_info in enumerate(all_texts, 1):
        combined += f"=== 文档 {i}: {text_info['filename']} ===\n"
        combined += f"字数: {text_info['word_count']} 字\n"
        combined += f"内容: {text_info['content'][:2000]}...\n\n"  # 限制每个文件的长度
    
    combined += "请对以上所有文档进行综合分析，提取共同主题、关键观点和整体结论。"
    
    return combined

def generate_batch_xml_summary(all_texts, ai_summary, total_word_count):
    """生成批量分析的XML格式文件"""
    root = etree.Element("batch_document_analysis")
    
    # 基本信息
    metadata = etree.SubElement(root, "metadata")
    etree.SubElement(metadata, "analysis_date").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    etree.SubElement(metadata, "file_count").text = str(len(all_texts))
    etree.SubElement(metadata, "total_word_count").text = str(total_word_count)
    etree.SubElement(metadata, "analysis_type").text = "batch_analysis"
    
    # 文件列表信息
    files_info = etree.SubElement(root, "source_files")
    for i, text_info in enumerate(all_texts, 1):
        file_elem = etree.SubElement(files_info, f"file_{i}")
        etree.SubElement(file_elem, "filename").text = text_info['filename']
        etree.SubElement(file_elem, "word_count").text = str(text_info['word_count'])
        etree.SubElement(file_elem, "content_preview").text = text_info['content'][:300] + "..." if len(text_info['content']) > 300 else text_info['content']
    
    # AI综合分析结果
    analysis = etree.SubElement(root, "comprehensive_analysis")
    etree.SubElement(analysis, "summary").text = ai_summary
    etree.SubElement(analysis, "model_used").text = "gpt-3.5-turbo"
    etree.SubElement(analysis, "analysis_scope").text = f"综合分析了 {len(all_texts)} 个文档"
    
    # 格式化XML
    xml_str = etree.tostring(root, pretty_print=True, encoding='unicode')
    return xml_str

if __name__ == '__main__':
    if not os.getenv('OPENAI_API_KEY'):
        print("警告: 请在 .env 文件中设置 OPENAI_API_KEY")
    
    app.run(debug=True, host='0.0.0.0', port=8080) 