from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Depends
from fastapi.responses import FileResponse
from typing import List
from sqlalchemy.orm import Session
import os
import tempfile
import shutil
from datetime import datetime
from app.services.document_service import (
    allowed_file, 
    extract_text_from_file, 
    analyze_with_openai, 
    analyze_with_openai_xml,
    generate_xml_summary,
    combine_texts_for_analysis,
    generate_batch_xml_summary
)
from app.services.auth_service import get_current_active_user, get_current_user_or_guest
from app.services.knowledge_service import KnowledgeService
from app.models.user import User
from app.models.database import get_db
from typing import Union

router = APIRouter(prefix="/api/document", tags=["文档分析"])

# 确保必要的目录存在
UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: Union[User, dict] = Depends(get_current_user_or_guest),
    db: Session = Depends(get_db)
):
    """上传单个文档进行分析"""
    try:
        # 检查文件类型
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型。支持的格式: txt, pdf, docx, doc"
            )
        
        # 保存上传的文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 提取文本内容
        text_content = extract_text_from_file(file_path, file.filename)
        
        # 使用OpenAI分析
        ai_analysis = analyze_with_openai(text_content)
        
        # 生成XML摘要
        xml_summary = generate_xml_summary(file.filename, text_content, ai_analysis)
        
        # 保存分析结果
        result_filename = f"analysis_{timestamp}_{file.filename.rsplit('.', 1)[0]}.xml"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(xml_summary)
        
        # 将分析结果存储到知识库（仅对注册用户）
        knowledge_id = None
        if isinstance(current_user, User):
            try:
                # 创建知识条目
                knowledge_item = KnowledgeService.create_knowledge_from_analysis(
                    db=db,
                    title=f"文档分析：{file.filename}",
                    content=text_content,
                    analysis=ai_analysis,
                    source_file=file.filename,
                    user_id=current_user.id
                )
                knowledge_id = knowledge_item.id
                
            except Exception as e:
                # 知识库存储失败不影响主流程
                print(f"知识库存储失败: {str(e)}")
        
        return {
            "message": "文档分析完成",
            "filename": file.filename,
            "size": file.size,
            "analysis": ai_analysis,
            "xml_file": result_filename,
            "download_url": f"/api/document/download/{result_filename}",
            "knowledge_id": knowledge_id,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"文档上传分析错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档分析失败: {str(e)}")

@router.post("/upload-xml")
async def upload_document_xml(
    file: UploadFile = File(...),
    current_user: Union[User, dict] = Depends(get_current_user_or_guest),
    db: Session = Depends(get_db)
):
    """上传单个文档进行分析，返回XML格式结果"""
    try:
        # 检查文件类型
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型。支持的格式: txt, pdf, docx, doc"
            )
        
        # 保存上传的文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 提取文本内容
        text_content = extract_text_from_file(file_path, file.filename)
        
        # 使用OpenAI分析（XML格式）
        ai_analysis_xml = analyze_with_openai_xml(text_content)
        
        # 生成完整的XML摘要
        xml_summary = generate_xml_summary(file.filename, text_content, ai_analysis_xml)
        
        # 保存分析结果
        result_filename = f"xml_analysis_{timestamp}_{file.filename.rsplit('.', 1)[0]}.xml"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(xml_summary)
        
        # 将分析结果存储到知识库（仅对注册用户）
        knowledge_id = None
        if isinstance(current_user, User):
            try:
                # 创建知识条目
                knowledge_item = KnowledgeService.create_knowledge_from_analysis(
                    db=db,
                    title=f"XML文档分析：{file.filename}",
                    content=text_content,
                    analysis=ai_analysis_xml,
                    source_file=file.filename,
                    user_id=current_user.id
                )
                knowledge_id = knowledge_item.id
                
            except Exception as e:
                # 知识库存储失败不影响主流程
                print(f"知识库存储失败: {str(e)}")
        
        return {
            "message": "文档XML分析完成",
            "filename": file.filename,
            "size": file.size,
            "xml_analysis": ai_analysis_xml,
            "xml_file": result_filename,
            "download_url": f"/api/document/download/{result_filename}",
            "knowledge_id": knowledge_id,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"文档XML上传分析错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文档XML分析失败: {str(e)}")

@router.post("/batch-upload")
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    current_user: Union[User, dict] = Depends(get_current_user_or_guest),
    db: Session = Depends(get_db)
):
    """批量上传文档进行分析"""
    try:
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="最多支持同时上传10个文件")
        
        all_texts = []
        processed_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for file in files:
            # 检查文件类型
            if not allowed_file(file.filename):
                continue
                
            # 保存文件
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 提取文本
            text_content = extract_text_from_file(file_path, file.filename)
            all_texts.append(text_content)
            processed_files.append(file.filename)
        
        if not all_texts:
            raise HTTPException(status_code=400, detail="没有有效的文档可以分析")
        
        # 合并所有文本进行分析
        combined_text = combine_texts_for_analysis(all_texts)
        
        # 使用OpenAI分析
        ai_analysis = analyze_with_openai(combined_text)
        
        # 生成批量分析的XML摘要
        total_word_count = sum(len(text) for text in all_texts)
        xml_summary = generate_batch_xml_summary(all_texts, ai_analysis, total_word_count)
        
        # 保存分析结果
        result_filename = f"batch_analysis_{timestamp}.xml"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(xml_summary)
        
        # 将分析结果存储到知识库（仅对注册用户）
        knowledge_id = None
        if isinstance(current_user, User):
            try:
                # 创建知识条目
                knowledge_item = KnowledgeService.create_knowledge_from_analysis(
                    db=db,
                    title=f"批量文档分析：{len(processed_files)}个文件",
                    content=combined_text,
                    analysis=ai_analysis,
                    source_file=", ".join(processed_files),
                    user_id=current_user.id,
                    tags="批量分析,多文档"
                )
                knowledge_id = knowledge_item.id
                
            except Exception as e:
                # 知识库存储失败不影响主流程
                print(f"知识库存储失败: {str(e)}")
        
        return {
            "message": f"批量分析完成，共处理 {len(processed_files)} 个文件",
            "processed_files": processed_files,
            "total_files": len(processed_files),
            "analysis": ai_analysis,
            "xml_file": result_filename,
            "download_url": f"/api/document/download/{result_filename}",
            "knowledge_id": knowledge_id,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")

@router.post("/batch-upload-xml")
async def batch_upload_documents_xml(
    files: List[UploadFile] = File(...),
    current_user: Union[User, dict] = Depends(get_current_user_or_guest),
    db: Session = Depends(get_db)
):
    """批量上传文档进行XML格式分析"""
    try:
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="最多支持同时上传10个文件")
        
        all_texts = []
        processed_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for file in files:
            # 检查文件类型
            if not allowed_file(file.filename):
                continue
                
            # 保存文件
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 提取文本
            text_content = extract_text_from_file(file_path, file.filename)
            all_texts.append(text_content)
            processed_files.append(file.filename)
        
        if not all_texts:
            raise HTTPException(status_code=400, detail="没有有效的文档可以分析")
        
        # 合并所有文本进行分析
        combined_text = combine_texts_for_analysis(all_texts)
        
        # 使用OpenAI分析（XML格式）
        ai_analysis_xml = analyze_with_openai_xml(combined_text)
        
        # 生成批量分析的XML摘要
        total_word_count = sum(len(text) for text in all_texts)
        xml_summary = generate_batch_xml_summary(all_texts, ai_analysis_xml, total_word_count)
        
        # 保存分析结果
        result_filename = f"batch_xml_analysis_{timestamp}.xml"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(xml_summary)
        
        # 将分析结果存储到知识库（仅对注册用户）
        knowledge_id = None
        if isinstance(current_user, User):
            try:
                # 创建知识条目
                knowledge_item = KnowledgeService.create_knowledge_from_analysis(
                    db=db,
                    title=f"批量XML文档分析：{len(processed_files)}个文件",
                    content=combined_text,
                    analysis=ai_analysis_xml,
                    source_file=", ".join(processed_files),
                    user_id=current_user.id,
                    tags="批量分析,多文档,XML"
                )
                knowledge_id = knowledge_item.id
                
            except Exception as e:
                # 知识库存储失败不影响主流程
                print(f"知识库存储失败: {str(e)}")
        
        return {
            "message": f"批量XML分析完成，共处理 {len(processed_files)} 个文件",
            "processed_files": processed_files,
            "total_files": len(processed_files),
            "xml_analysis": ai_analysis_xml,
            "xml_file": result_filename,
            "download_url": f"/api/document/download/{result_filename}",
            "knowledge_id": knowledge_id,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量XML分析失败: {str(e)}")

@router.get("/download/{filename}")
async def download_file(
    filename: str,
    current_user: Union[User, dict] = Depends(get_current_user_or_guest)
):
    """下载分析结果文件"""
    file_path = os.path.join(RESULTS_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/xml'
    )

@router.get("/results")
async def list_analysis_results(
    current_user: Union[User, dict] = Depends(get_current_user_or_guest)
):
    """获取分析结果列表"""
    try:
        # 游客用户返回空列表
        if isinstance(current_user, dict) and current_user.get("is_guest"):
            return {
                "message": "游客模式下无历史记录",
                "total": 0,
                "results": []
            }
        
        results = []
        
        if os.path.exists(RESULTS_FOLDER):
            for filename in os.listdir(RESULTS_FOLDER):
                if filename.endswith('.xml'):
                    file_path = os.path.join(RESULTS_FOLDER, filename)
                    file_stat = os.stat(file_path)
                    
                    results.append({
                        "filename": filename,
                        "size": file_stat.st_size,
                        "created_time": datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                        "download_url": f"/api/document/download/{filename}"
                    })
        
        # 按创建时间倒序排列
        results.sort(key=lambda x: x["created_time"], reverse=True)
        
        return {
            "message": "分析结果列表",
            "total": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取结果列表失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "upload_folder_exists": os.path.exists(UPLOAD_FOLDER),
        "results_folder_exists": os.path.exists(RESULTS_FOLDER),
        "openai_key_configured": bool(os.getenv('OPENAI_API_KEY'))
    }

@router.get("/debug/auth")
async def debug_auth(
    current_user: Union[User, dict] = Depends(get_current_user_or_guest)
):
    """调试认证信息"""
    if isinstance(current_user, User):
        return {
            "user_type": "authenticated_user",
            "user_id": current_user.id,
            "username": current_user.username,
            "is_active": current_user.is_active
        }
    else:
        return {
            "user_type": "guest_user",
            "user_data": current_user
        } 