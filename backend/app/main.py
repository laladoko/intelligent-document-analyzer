from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import asyncio
import time
from app.api.document import router as document_router
from app.api.auth import router as auth_router
from app.api.knowledge import router as knowledge_router
from app.api.graphrag import router as graphrag_router
from app.config.timeout_config import SERVER_TIMEOUT
# 导入bcrypt配置以解决兼容性警告
from app.config import bcrypt_config

app = FastAPI(
    title="企业文档智能分析系统",
    description="基于 OpenAI GPT-4o 的企业文档智能分析 API",
    version="1.0.0"
)

# 添加超时中间件
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """请求超时中间件"""
    try:
        # 为长时间运行的操作设置更长的超时时间
        if any(path in str(request.url) for path in ["/upload", "/batch-upload", "/ask"]):
            timeout = SERVER_TIMEOUT
        else:
            timeout = 60.0  # 普通请求60秒超时
        
        start_time = time.time()
        response = await asyncio.wait_for(call_next(request), timeout=timeout)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except asyncio.TimeoutError:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=408,
            content={"detail": f"请求超时，处理时间超过 {timeout} 秒"}
        )
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": f"服务器内部错误: {str(e)}"}
        )

# 允许所有来源跨域，便于前端本地开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(document_router)
app.include_router(auth_router)
app.include_router(knowledge_router)
app.include_router(graphrag_router)

@app.get("/")
def root():
    """根路径欢迎页面"""
    return {
        "message": "欢迎使用企业文档智能分析系统",
        "version": "1.0.0",
        "description": "基于 OpenAI GPT-4o 的企业文档智能分析 API",
        "endpoints": {
            "health": "/ping",
            "docs": "/docs",
            "redoc": "/redoc",
            "login": "/api/auth/login",
            "register": "/api/auth/register",
            "logout": "/api/auth/logout",
            "me": "/api/auth/me",
            "upload": "/api/document/upload",
            "upload_xml": "/api/document/upload-xml",
            "batch_upload": "/api/document/batch-upload",
            "batch_upload_xml": "/api/document/batch-upload-xml",
            "results": "/api/document/results",
            "download": "/api/document/download/{filename}",
            "knowledge_search": "/api/knowledge/search",
            "knowledge_ask": "/api/knowledge/ask",
            "knowledge_preset": "/api/knowledge/preset-questions",
            "knowledge_stats": "/api/knowledge/stats"
        },
        "features": [
            "用户认证和权限管理",
            "单文档上传分析",
            "批量文档分析",
            "XML格式输出",
            "结果文件下载",
            "分析历史记录",
            "智能知识库存储",
            "知识库问答系统",
            "预设问题快速查询",
            "知识搜索和统计"
        ],
        "status": "running"
    }

@app.get("/ping")
def ping():
    """健康检查接口"""
    return {"message": "pong", "status": "healthy"}

# 后续会引入各API路由
