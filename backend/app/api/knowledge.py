from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import io
import zipfile
from xml.dom.minidom import parseString

from app.models.database import get_db
from app.models.knowledge_schemas import (
    KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseList,
    KnowledgeSearchRequest, KnowledgeSearchResult, KnowledgeQACreate, 
    KnowledgeQAResponse, KnowledgeQAFeedback, PresetQuestion, PresetQuestionCreate,
    KnowledgeStats
)
from app.services.knowledge_service import KnowledgeService
from app.services.auth_service import get_current_active_user, get_current_registered_user
from app.models.user import User

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])

@router.post("/items", response_model=KnowledgeBase)
async def create_knowledge_item(
    knowledge_data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建知识条目"""
    try:
        # 只有注册用户可以创建知识条目
        user_id = current_user.id
        knowledge_item = KnowledgeService.create_knowledge_item(db, knowledge_data, user_id)
        
        return knowledge_item
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建知识条目失败: {str(e)}")

@router.get("/items/{knowledge_id}", response_model=KnowledgeBase)
async def get_knowledge_item(
    knowledge_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取知识条目详情"""
    knowledge_item = KnowledgeService.get_knowledge_by_id(db, knowledge_id)
    
    if not knowledge_item:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    
    return knowledge_item

@router.post("/search", response_model=KnowledgeSearchResult)
async def search_knowledge(
    search_request: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_registered_user),
    db: Session = Depends(get_db)
):
    """搜索知识库"""
    try:
        result = KnowledgeService.search_knowledge(db, search_request)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/ask", response_model=KnowledgeQAResponse)
async def ask_question(
    qa_request: KnowledgeQACreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """基于知识库回答问题"""
    try:
        # 只有注册用户可以使用
        user_id = current_user.id
        session_id = None
        is_guest = False
        
        result = KnowledgeService.ask_question(
            db=db,
            question=qa_request.question,
            user_id=user_id,
            session_id=session_id,
            is_guest=is_guest,
            knowledge_ids=qa_request.knowledge_ids
        )
        
        return KnowledgeQAResponse(
            id=result["qa_id"],
            question=result["question"],
            answer=result["answer"],
            knowledge_id=result["related_knowledge"][0] if result["related_knowledge"] else None,
            session_id=session_id,
            is_guest=is_guest,
            response_time=result["response_time"],
            created_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")

@router.post("/feedback")
async def submit_feedback(
    feedback_data: KnowledgeQAFeedback,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """提交问答反馈"""
    try:
        success = KnowledgeService.submit_feedback(db, feedback_data)
        
        if success:
            return {"message": "反馈提交成功"}
        else:
            raise HTTPException(status_code=404, detail="问答记录不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")

@router.get("/preset-questions", response_model=List[PresetQuestion])
async def get_preset_questions(
    category: Optional[str] = Query(None, description="问题分类"),
    current_user: User = Depends(get_current_registered_user),
    db: Session = Depends(get_db)
):
    """获取预设问题列表"""
    try:
        questions = KnowledgeService.get_preset_questions(db, category)
        return questions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预设问题失败: {str(e)}")

@router.post("/preset-questions/{question_id}/click")
async def click_preset_question(
    question_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """记录预设问题点击"""
    try:
        question = KnowledgeService.click_preset_question(db, question_id)
        
        if question:
            return {"message": "点击记录成功", "question": question.question}
        else:
            raise HTTPException(status_code=404, detail="预设问题不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录点击失败: {str(e)}")

@router.get("/stats", response_model=KnowledgeStats)
async def get_knowledge_stats(
    current_user: User = Depends(get_current_registered_user),
    db: Session = Depends(get_db)
):
    """获取知识库统计信息"""
    try:
        stats = KnowledgeService.get_knowledge_stats(db)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/qa-history")
async def get_qa_history(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取问答历史"""
    try:
        # 只有注册用户可以查看历史
        user_id = current_user.id
        session_id = None
        
        history = KnowledgeService.get_user_qa_history(
            db=db,
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
        
        return {
            "history": history,
            "total": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")

# 管理员接口
@router.post("/preset-questions", response_model=PresetQuestion)
async def create_preset_question(
    question_data: PresetQuestionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建预设问题（管理员）"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        question = KnowledgeService.create_preset_question(db, question_data)
        return question
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建预设问题失败: {str(e)}")

@router.post("/init-preset-questions")
async def init_preset_questions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """初始化预设问题（管理员）"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        KnowledgeService.init_preset_questions(db)
        return {"message": "预设问题初始化成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")

@router.delete("/items/{knowledge_id}")
async def delete_knowledge_item(
    knowledge_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除知识条目"""
    try:
        # 获取知识条目
        knowledge_item = KnowledgeService.get_knowledge_by_id(db, knowledge_id)
        
        if not knowledge_item:
            raise HTTPException(status_code=404, detail="知识条目不存在")
        
        # 检查权限：只有创建者或管理员可以删除
        if knowledge_item.created_by != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足，只能删除自己创建的文档")
        
        # 软删除：将is_active设为False
        knowledge_item.is_active = False
        db.commit()
        
        return {"message": "文档删除成功", "id": knowledge_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/export")
async def export_selected_documents(
    knowledge_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """导出选中的文档分析合集"""
    try:
        if not knowledge_ids:
            raise HTTPException(status_code=400, detail="请选择要导出的文档")
        
        # 获取选中的知识条目
        selected_items = []
        for knowledge_id in knowledge_ids:
            item = KnowledgeService.get_knowledge_by_id(db, knowledge_id)
            if item and item.is_active:
                selected_items.append(item)
        
        if not selected_items:
            raise HTTPException(status_code=404, detail="未找到有效的文档")
        
        # 创建ZIP文件
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 创建综合分析报告
            report_content = generate_comprehensive_report(selected_items, current_user)
            zip_file.writestr("综合分析报告.md", report_content.encode('utf-8'))
            
            # 为每个文档创建单独的文件
            for i, item in enumerate(selected_items, 1):
                # 创建Markdown格式的文档
                doc_content = generate_document_markdown(item, i)
                filename = f"{i:02d}_{sanitize_filename(item.title)}.md"
                zip_file.writestr(filename, doc_content.encode('utf-8'))
                
                # 如果有分析结果，也创建XML格式
                if item.summary and "企业信息XML结构" in item.summary:
                    xml_content = extract_xml_from_summary(item.summary)
                    if xml_content:
                        xml_filename = f"{i:02d}_{sanitize_filename(item.title)}.xml"
                        zip_file.writestr(xml_filename, xml_content.encode('utf-8'))
        
        zip_buffer.seek(0)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"document_analysis_collection_{timestamp}.zip"
        
        # 返回文件流
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
                "Content-Type": "application/zip"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@router.post("/ask-stream")
async def ask_question_stream(
    qa_request: KnowledgeQACreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """基于知识库回答问题（流式输出）"""
    try:
        # 只有注册用户可以使用
        user_id = current_user.id
        session_id = None
        is_guest = False
        
        # 使用生成器函数进行流式输出
        def generate_stream():
            try:
                # 获取相关知识库内容
                context_items = []
                used_knowledge_ids = []
                
                if qa_request.knowledge_ids and len(qa_request.knowledge_ids) > 0:
                    for knowledge_id in qa_request.knowledge_ids:
                        item = KnowledgeService.get_knowledge_by_id(db, knowledge_id)
                        if item and item.is_active:
                            context_items.append(f"文档标题: {item.title}\n文档内容: {item.content}")
                            used_knowledge_ids.append(item.id)
                
                if not context_items:
                    # 如果没有指定文档，搜索相关知识
                    from app.models.knowledge_schemas import KnowledgeSearchRequest
                    search_request = KnowledgeSearchRequest(
                        query=qa_request.question,
                        limit=5
                    )
                    search_result = KnowledgeService.search_knowledge(db, search_request)
                    
                    for item in search_result["knowledge_items"]:
                        context_items.append(f"文档标题: {item.title}\n文档内容: {item.content[:800]}...")
                        used_knowledge_ids.append(item.id)
                
                context = "\n\n=== 分隔符 ===\n\n".join(context_items)
                
                # 流式调用OpenAI API
                answer_chunks = KnowledgeService.ask_question_stream(
                    question=qa_request.question,
                    context=context,
                    context_count=len(context_items)
                )
                
                # 发送流式响应
                for chunk in answer_chunks:
                    yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"
                
                # 发送完成信号
                yield f"data: {json.dumps({'type': 'done', 'data': None}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                error_msg = f"问答失败: {str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'data': error_msg}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式问答失败: {str(e)}")

def generate_comprehensive_report(items: List, user) -> str:
    """生成综合分析报告"""
    report = f"""# 企业文档智能分析综合报告

## 报告信息
- **生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
- **分析用户**: {user.full_name or user.username}
- **文档数量**: {len(items)}个

## 执行摘要

本报告基于{len(items)}个企业文档进行综合分析，通过AI智能提取关键信息，为企业决策提供数据支持。

## 文档清单

"""
    
    for i, item in enumerate(items, 1):
        report += f"""### {i}. {item.title}
- **文件来源**: {item.source_file or '直接输入'}
- **上传时间**: {item.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **查看次数**: {item.view_count}次
- **标签**: {item.tags or '无'}

**内容摘要**:
{item.summary or '无摘要'}

---

"""
    
    report += f"""## 分析结论

基于以上{len(items)}个文档的分析，建议企业关注以下关键领域：

1. **内容整合**: 将各文档中的关键信息进行整合，形成统一的知识体系
2. **知识管理**: 建立完善的企业知识库，提高信息检索效率
3. **持续优化**: 定期更新文档内容，保持信息的时效性和准确性

## 使用说明

本报告包含以下文件：
- 综合分析报告.md - 本文件，包含整体分析结果
- 各单独文档的详细分析文件（Markdown格式）
- XML结构化数据文件（如适用）

---

*本报告由企业文档智能分析系统自动生成*
"""
    
    return report

def generate_document_markdown(item, index: int) -> str:
    """生成单个文档的Markdown格式"""
    content = f"""# 文档分析报告 #{index}: {item.title}

## 基本信息
- **文档标题**: {item.title}
- **源文件**: {item.source_file or '直接输入'}
- **上传时间**: {item.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- **最后更新**: {item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else '未更新'}
- **查看次数**: {item.view_count}次
- **标签**: {item.tags or '无'}

## 内容摘要
{item.summary or '无摘要'}

## 原始内容
```
{item.content}
```

## 元数据
- **文档ID**: {item.id}
- **创建者**: {item.created_by}
- **来源类型**: {item.source_type}
- **状态**: {'活跃' if item.is_active else '已禁用'}

---

*此文档由企业文档智能分析系统处理*
"""
    return content

def extract_xml_from_summary(summary: str) -> str:
    """从摘要中提取XML内容"""
    try:
        # 查找XML结构开始和结束位置
        xml_start = summary.find('<enterprise_info>')
        xml_end = summary.find('</enterprise_info>')
        
        if xml_start != -1 and xml_end != -1:
            xml_content = summary[xml_start:xml_end + len('</enterprise_info>')]
            
            # 格式化XML
            try:
                dom = parseString(xml_content)
                return dom.toprettyxml(indent="  ", encoding=None)
            except:
                return xml_content
        
        return None
    except Exception:
        return None

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    import re
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 限制长度
    if len(filename) > 50:
        filename = filename[:50]
    return filename.strip()