from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.database import get_db
from app.models.knowledge_schemas import (
    KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseList,
    KnowledgeSearchRequest, KnowledgeSearchResult, KnowledgeQACreate, 
    KnowledgeQAResponse, KnowledgeQAFeedback, PresetQuestion, PresetQuestionCreate,
    KnowledgeStats
)
from app.services.knowledge_service import KnowledgeService
from app.services.auth_service import get_current_active_user
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
    current_user: User = Depends(get_current_active_user),
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
            is_guest=is_guest
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
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(get_current_active_user),
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