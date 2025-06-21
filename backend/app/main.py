from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import asyncio
import time
import logging
from contextlib import asynccontextmanager
from app.api.document import router as document_router
from app.api.auth import router as auth_router
from app.api.knowledge import router as knowledge_router
from app.api.graphrag import router as graphrag_router
from app.config.timeout_config import SERVER_TIMEOUT
# 导入bcrypt配置以解决兼容性警告
from app.config import bcrypt_config

# 导入防阻塞配置
from app.config.anti_blocking_config import (
    health_checker, task_queue, config, 
    ServiceStatus, with_timeout_and_fallback,
    openai_circuit_breaker, database_circuit_breaker
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 健康检查函数
async def check_database_health():
    """检查数据库健康状态"""
    try:
        from app.models.database import engine
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return False

async def check_openai_health():
    """检查OpenAI服务健康状态"""
    try:
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return False
        # 简单检查API key格式
        return api_key.startswith('sk-') and len(api_key) > 20
    except Exception as e:
        logger.error(f"OpenAI健康检查失败: {e}")
        return False

# FastAPI生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的生命周期管理"""
    # 启动时
    logger.info("🚀 正在启动防阻塞架构...")
    
    # 启动任务队列
    await task_queue.start_workers(worker_count=3)
    logger.info("✅ 任务队列已启动")
    
    # 启动健康检查后台任务
    health_task = asyncio.create_task(background_health_check())
    logger.info("✅ 健康检查服务已启动")
    
    logger.info("🎉 防阻塞架构启动完成！")
    
    yield
    
    # 关闭时
    logger.info("🛑 正在停止防阻塞架构...")
    health_task.cancel()
    await task_queue.stop()
    logger.info("✅ 防阻塞架构已停止")

async def background_health_check():
    """后台健康检查任务"""
    while True:
        try:
            # 检查各个服务
            await health_checker.check_service("database", check_database_health)
            await health_checker.check_service("openai", check_openai_health)
            
            # 每30秒检查一次
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"健康检查后台任务出错: {e}")
            await asyncio.sleep(10)

app = FastAPI(
    title="企业文档智能分析系统 (防阻塞版)",
    description="基于 OpenAI GPT-4o 的企业文档智能分析 API - 防阻塞架构",
    version="2.0.0",
    lifespan=lifespan
)

# 防阻塞中间件
@app.middleware("http")
async def anti_blocking_middleware(request: Request, call_next):
    """防阻塞中间件"""
    start_time = time.time()
    
    try:
        # 根据请求类型设置不同超时
        path = str(request.url.path)
        if any(endpoint in path for endpoint in ["/upload", "/batch-upload", "/ask", "/build-index"]):
            timeout = config.DEFAULT_TIMEOUT * 2  # 长时间操作
        elif "/health" in path or "/ping" in path:
            timeout = config.QUICK_TIMEOUT  # 快速健康检查
        else:
            timeout = config.DEFAULT_TIMEOUT  # 普通操作
        
        # 执行请求，带超时保护
        response = await asyncio.wait_for(call_next(request), timeout=timeout)
        
        # 添加响应头
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        response.headers["X-Timeout-Used"] = f"{timeout}"
        
        return response
        
    except asyncio.TimeoutError:
        logger.warning(f"请求超时: {path} ({timeout}s)")
        return JSONResponse(
            status_code=408,
            content={
                "error": "request_timeout",
                "message": f"请求处理超时 ({timeout}秒)",
                "path": path,
                "suggestion": "请稍后重试，或联系管理员检查服务状态"
            }
        )
    except Exception as e:
        logger.error(f"中间件处理出错: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "middleware_error",
                "message": "服务器内部错误",
                "suggestion": "请稍后重试"
            }
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
async def root():
    """根路径 - 系统信息和状态"""
    health_status = health_checker.get_overall_health()
    
    return {
        "message": "企业文档智能分析系统 (防阻塞版)",
        "version": "2.0.0",
        "architecture": "anti-blocking",
        "description": "基于 OpenAI GPT-4o 的企业文档智能分析 API - 防阻塞架构",
        "health": health_status,
        "features": {
            "anti_blocking": True,
            "circuit_breaker": True,
            "task_queue": True,
            "health_monitoring": True,
            "timeout_protection": True,
            "graceful_degradation": True
        },
        "endpoints": {
            "health_simple": "/ping",
            "health_detailed": "/health",
            "health_circuit_breakers": "/health/circuit-breakers",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "status": "running",
        "uptime": time.time()
    }

@app.get("/ping")
async def ping():
    """快速健康检查 - 5秒内必须响应"""
    try:
        return await asyncio.wait_for(
            _quick_health_check(), 
            timeout=config.QUICK_TIMEOUT
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="服务响应超时")

async def _quick_health_check():
    """内部快速健康检查"""
    return {
        "message": "pong", 
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0-anti-blocking"
    }

@app.get("/health")
async def detailed_health():
    """详细健康检查"""
    try:
        health_status = health_checker.get_overall_health()
        
        return {
            "status": health_status["status"],
            "services": health_status["services"],
            "summary": {
                "healthy_services": health_status["healthy_count"],
                "total_services": health_status["total_count"],
                "last_check": health_status["last_check"]
            },
            "system": {
                "task_queue_size": task_queue.queue.qsize(),
                "worker_count": len(task_queue.workers),
                "uptime": time.time(),
                "version": "2.0.0"
            },
            "configuration": {
                "timeouts": {
                    "quick": config.QUICK_TIMEOUT,
                    "default": config.DEFAULT_TIMEOUT,
                    "openai": config.OPENAI_TIMEOUT,
                    "database": config.DATABASE_TIMEOUT
                },
                "circuit_breakers": {
                    "failure_threshold": config.circuit_breaker.failure_threshold,
                    "recovery_timeout": config.circuit_breaker.recovery_timeout
                },
                "task_queue": {
                    "max_size": config.MAX_QUEUE_SIZE,
                    "task_timeout": config.TASK_TIMEOUT
                }
            }
        }
    except Exception as e:
        logger.error(f"详细健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "message": "健康检查系统故障"
            }
        )

@app.get("/health/circuit-breakers")
async def circuit_breaker_status():
    """熔断器状态检查"""
    return {
        "circuit_breakers": {
            "openai": {
                "name": openai_circuit_breaker.name,
                "state": openai_circuit_breaker.state.value,
                "failure_count": openai_circuit_breaker.failure_count,
                "last_failure_time": openai_circuit_breaker.last_failure_time
            },
            "database": {
                "name": database_circuit_breaker.name,
                "state": database_circuit_breaker.state.value,
                "failure_count": database_circuit_breaker.failure_count,
                "last_failure_time": database_circuit_breaker.last_failure_time
            }
        },
        "healthy_breakers": sum(1 for cb in [openai_circuit_breaker, database_circuit_breaker] 
                               if cb.state == ServiceStatus.HEALTHY),
        "total_breakers": 2
    }

# 异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "服务器内部错误，请稍后重试",
            "path": str(request.url.path),
            "timestamp": time.time()
        }
    )

# 如果需要手动测试
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=False,  # 生产环境关闭reload
        timeout_keep_alive=30,
        timeout_graceful_shutdown=10,
        limit_concurrency=100
    )
