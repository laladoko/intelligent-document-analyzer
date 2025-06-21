# -*- coding: utf-8 -*-
"""
防阻塞配置
防止服务器因为各种原因卡死的配置文件
"""

import asyncio
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """服务状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"

@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5  # 失败阈值
    recovery_timeout: int = 60  # 恢复超时（秒）
    half_open_max_calls: int = 3  # 半开状态最大调用次数

@dataclass
class AntiBlockingConfig:
    """防阻塞总配置"""
    # 超时配置 - 缩短超时时间方便测试
    DEFAULT_TIMEOUT: float = 20.0   # 缩短默认超时
    QUICK_TIMEOUT: float = 5.0      # 快速响应超时
    OPENAI_TIMEOUT: float = 30.0    # 缩短OpenAI超时时间
    DATABASE_TIMEOUT: float = 8.0   # 缩短数据库超时
    
    # 重试配置
    MAX_RETRIES: int = 2  # 减少重试次数
    RETRY_DELAY: float = 1.0  # 缩短重试间隔
    
    # 连接池配置
    MAX_CONNECTIONS: int = 10
    CONNECTION_TIMEOUT: float = 5.0  # 缩短连接超时
    
    # 任务队列配置
    MAX_QUEUE_SIZE: int = 100
    TASK_TIMEOUT: float = 180.0  # 缩短任务超时到3分钟
    
    # 熔断器配置 - 使用field(default_factory=...)修复dataclass问题
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)

# 全局配置实例
config = AntiBlockingConfig()

class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = ServiceStatus.HEALTHY
        self._lock = asyncio.Lock()
    
    async def call(self, func, *args, **kwargs):
        """执行被熔断器保护的调用"""
        async with self._lock:
            # 检查熔断器状态
            if self.state == ServiceStatus.CIRCUIT_OPEN:
                if time.time() - self.last_failure_time > self.config.recovery_timeout:
                    self.state = ServiceStatus.DEGRADED
                    logger.info(f"熔断器 {self.name} 进入半开状态")
                else:
                    raise Exception(f"熔断器 {self.name} 开启中，拒绝请求")
        
        try:
            result = await func(*args, **kwargs)
            # 成功后重置
            if self.state == ServiceStatus.DEGRADED:
                self.state = ServiceStatus.HEALTHY
                self.failure_count = 0
                logger.info(f"熔断器 {self.name} 恢复正常")
            return result
            
        except Exception as e:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.config.failure_threshold:
                    self.state = ServiceStatus.CIRCUIT_OPEN
                    logger.error(f"熔断器 {self.name} 开启，失败次数: {self.failure_count}")
                
            raise e

class ServiceHealthChecker:
    """服务健康检查器"""
    
    def __init__(self):
        self.services: Dict[str, ServiceStatus] = {}
        self.last_check: Dict[str, float] = {}
        self.check_interval = 30  # 30秒检查一次
    
    async def check_service(self, service_name: str, check_func) -> ServiceStatus:
        """检查特定服务的健康状态"""
        try:
            start_time = time.time()
            await asyncio.wait_for(check_func(), timeout=config.QUICK_TIMEOUT)
            response_time = time.time() - start_time
            
            if response_time > config.QUICK_TIMEOUT * 0.8:
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.HEALTHY
                
        except asyncio.TimeoutError:
            status = ServiceStatus.UNHEALTHY
            logger.warning(f"服务 {service_name} 健康检查超时")
            
        except Exception as e:
            status = ServiceStatus.UNHEALTHY
            logger.error(f"服务 {service_name} 健康检查失败: {e}")
        
        self.services[service_name] = status
        self.last_check[service_name] = time.time()
        return status
    
    def get_overall_health(self) -> Dict[str, Any]:
        """获取整体健康状态"""
        healthy_count = sum(1 for status in self.services.values() 
                          if status == ServiceStatus.HEALTHY)
        total_count = len(self.services)
        
        if healthy_count == total_count:
            overall_status = ServiceStatus.HEALTHY
        elif healthy_count > total_count // 2:
            overall_status = ServiceStatus.DEGRADED
        else:
            overall_status = ServiceStatus.UNHEALTHY
        
        return {
            "status": overall_status.value,
            "services": {name: status.value for name, status in self.services.items()},
            "healthy_count": healthy_count,
            "total_count": total_count,
            "last_check": max(self.last_check.values()) if self.last_check else 0
        }

# 全局实例
health_checker = ServiceHealthChecker()

# 服务熔断器实例
openai_circuit_breaker = CircuitBreaker("openai", config.circuit_breaker)
database_circuit_breaker = CircuitBreaker("database", config.circuit_breaker)

async def with_timeout_and_fallback(func, timeout: float, fallback_func=None, *args, **kwargs):
    """
    带超时和降级的函数执行器
    """
    try:
        return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"函数 {func.__name__} 执行超时 ({timeout}s)")
        if fallback_func:
            return await fallback_func(*args, **kwargs)
        raise
    except Exception as e:
        logger.error(f"函数 {func.__name__} 执行失败: {e}")
        if fallback_func:
            return await fallback_func(*args, **kwargs)
        raise

class TaskQueue:
    """异步任务队列"""
    
    def __init__(self, max_size: int = 100):
        self.queue = asyncio.Queue(maxsize=max_size)
        self.workers = []
        self.running = False
    
    async def start_workers(self, worker_count: int = 3):
        """启动工作者"""
        self.running = True
        for i in range(worker_count):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        logger.info(f"启动了 {worker_count} 个任务队列工作者")
    
    async def _worker(self, name: str):
        """工作者协程"""
        while self.running:
            try:
                task_func, args, kwargs, future = await self.queue.get()
                logger.debug(f"工作者 {name} 处理任务: {task_func.__name__}")
                
                try:
                    result = await task_func(*args, **kwargs)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
                
                self.queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"工作者 {name} 处理任务时出错: {e}")
    
    async def submit_task(self, func, *args, **kwargs):
        """提交异步任务"""
        future = asyncio.Future()
        await self.queue.put((func, args, kwargs, future))
        return await future
    
    async def stop(self):
        """停止任务队列"""
        self.running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)

# 全局任务队列
task_queue = TaskQueue(max_size=config.MAX_QUEUE_SIZE) 