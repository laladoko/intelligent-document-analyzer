"""
GraphRAG API 端点
基于 Microsoft GraphRAG 项目的知识图谱API
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from app.models.database import get_db
from app.models.knowledge_base import KnowledgeBase
from app.services.auth_service import get_current_user_or_guest
from app.services.graphrag_service import graphrag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graphrag", tags=["GraphRAG知识图谱"])

# 请求模型
class GraphRAGBuildRequest(BaseModel):
    knowledge_ids: Optional[List[int]] = Field(None, description="指定知识库ID列表，为空则使用所有")
    rebuild: bool = Field(False, description="是否重新构建索引")

class GraphRAGSearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    search_type: str = Field("hybrid", description="搜索类型：global, local, hybrid")
    max_tokens: int = Field(2000, description="最大token数")

class GraphRAGStatusResponse(BaseModel):
    graphrag_available: bool
    api_key_configured: bool
    index_exists: bool
    workspace_path: str
    artifact_count: Optional[int] = None
    last_modified: Optional[float] = None

# API端点
@router.get("/status", response_model=GraphRAGStatusResponse)
async def get_graphrag_status(
    current_user = Depends(get_current_user_or_guest)
):
    """获取GraphRAG状态"""
    try:
        status = graphrag_service.get_index_status()
        return GraphRAGStatusResponse(**status)
    except Exception as e:
        logger.error(f"获取GraphRAG状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}"
        )

@router.post("/build-index")
async def build_graphrag_index(
    request: GraphRAGBuildRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user_or_guest),
    db: Session = Depends(get_db)
):
    """构建GraphRAG知识图谱索引"""
    try:
        # 检查GraphRAG是否可用
        if not graphrag_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GraphRAG不可用，请检查安装和API密钥配置"
            )
        
        # 获取知识库数据
        query = db.query(KnowledgeBase)
        
        if request.knowledge_ids:
            query = query.filter(KnowledgeBase.id.in_(request.knowledge_ids))
        
        # 如果不是游客用户，只获取用户自己的数据
        if not current_user.get("is_guest", False):
            query = query.filter(KnowledgeBase.user_id == current_user.id)
        
        knowledge_items = query.all()
        
        if not knowledge_items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到可用的知识库数据"
            )
        
        logger.info(f"开始构建GraphRAG索引，包含 {len(knowledge_items)} 个文档")
        
        # 后台任务构建索引
        background_tasks.add_task(
            build_index_background,
            knowledge_items
        )
        
        return {
            "message": "GraphRAG索引构建已启动",
            "documents_count": len(knowledge_items),
            "status": "building"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动GraphRAG索引构建失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"索引构建失败: {str(e)}"
        )

async def build_index_background(knowledge_items: List[KnowledgeBase]):
    """后台构建索引任务"""
    try:
        result = await graphrag_service.build_index(knowledge_items)
        logger.info(f"GraphRAG索引构建完成: {result}")
    except Exception as e:
        logger.error(f"后台索引构建失败: {str(e)}")

@router.post("/search")
async def graphrag_search(
    request: GraphRAGSearchRequest,
    current_user = Depends(get_current_user_or_guest)
):
    """执行GraphRAG搜索"""
    try:
        # 检查GraphRAG是否可用
        if not graphrag_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GraphRAG不可用，请检查安装和API密钥配置"
            )
        
        # 检查索引是否存在
        status_info = graphrag_service.get_index_status()
        if not status_info.get("index_exists", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GraphRAG索引不存在，请先构建索引"
            )
        
        logger.info(f"执行GraphRAG搜索: {request.query} (类型: {request.search_type})")
        
        # 根据搜索类型执行搜索
        if request.search_type == "global":
            result = await graphrag_service.global_search(request.query)
        elif request.search_type == "local":
            result = await graphrag_service.local_search(request.query)
        elif request.search_type == "hybrid":
            result = await graphrag_service.hybrid_search(request.query)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的搜索类型，支持: global, local, hybrid"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GraphRAG搜索失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )

@router.get("/health")
async def graphrag_health():
    """GraphRAG健康检查"""
    try:
        status_info = graphrag_service.get_index_status()
        
        health_status = {
            "status": "healthy" if graphrag_service.is_available() else "unavailable",
            "graphrag_available": status_info["graphrag_available"],
            "api_key_configured": status_info["api_key_configured"],
            "index_exists": status_info["index_exists"],
            "workspace_path": status_info["workspace_path"]
        }
        
        if status_info["index_exists"]:
            health_status["artifact_count"] = status_info.get("artifact_count", 0)
        
        return health_status
        
    except Exception as e:
        logger.error(f"GraphRAG健康检查失败: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "graphrag_available": False
        }

@router.delete("/index")
async def delete_graphrag_index(
    current_user = Depends(get_current_user_or_guest)
):
    """删除GraphRAG索引"""
    try:
        import shutil
        from pathlib import Path
        
        # 只有管理员或真实用户可以删除索引
        if current_user.get("is_guest", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="游客用户无权删除索引"
            )
        
        workspace_path = Path("backend/graphrag_workspace")
        
        # 删除输出和缓存目录
        if (workspace_path / "output").exists():
            shutil.rmtree(workspace_path / "output")
        if (workspace_path / "cache").exists():
            shutil.rmtree(workspace_path / "cache")
        if (workspace_path / "reports").exists():
            shutil.rmtree(workspace_path / "reports")
        
        # 重新创建空目录
        (workspace_path / "output").mkdir(exist_ok=True)
        
        logger.info("GraphRAG索引已删除")
        
        return {
            "message": "GraphRAG索引已成功删除",
            "status": "deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除GraphRAG索引失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除索引失败: {str(e)}"
        )

@router.get("/info")
async def get_graphrag_info():
    """获取GraphRAG项目信息"""
    return {
        "name": "Microsoft GraphRAG",
        "description": "基于图的检索增强生成(RAG)系统",
        "github": "https://github.com/microsoft/graphrag",
        "documentation": "https://microsoft.github.io/graphrag/",
        "license": "MIT",
        "features": [
            "知识图谱构建",
            "实体提取和关系分析", 
            "社区检测和层次结构",
            "全局和本地搜索",
            "多文档推理",
            "上下文感知问答"
        ],
        "version": "集成版本",
        "integration_author": "徐洪森 (lala)"
    } 