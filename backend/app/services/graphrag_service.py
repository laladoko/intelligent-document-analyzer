"""
GraphRAG 服务模块
基于 Microsoft GraphRAG 项目提供知识图谱构建和查询功能

参考文档: https://microsoft.github.io/graphrag/
GitHub: https://github.com/microsoft/graphrag
"""

import os
import asyncio
import logging
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import subprocess

try:
    from graphrag.query.indexer_adapters import read_indexer_entities, read_indexer_reports
    from graphrag.query.llm.oai.chat_openai import ChatOpenAI
    from graphrag.query.llm.oai.typing import OpenaiApiType
    from graphrag.query.structured_search.global_search.community_context import GlobalCommunityContext
    from graphrag.query.structured_search.global_search.search import GlobalSearch
    from graphrag.query.structured_search.local_search.mixed_context import LocalSearchMixedContext
    from graphrag.query.structured_search.local_search.search import LocalSearch
    from graphrag.index.main import run_pipeline_with_config
    from graphrag.index.config import PipelineConfig
    GRAPHRAG_AVAILABLE = True
except ImportError as e:
    GRAPHRAG_AVAILABLE = False
    logging.warning(f"GraphRAG not available in main environment: {str(e)}")
    logging.info("GraphRAG is installed in dedicated environment: backend/graphrag_venv")
    logging.info("GraphRAG functions will use subprocess calls to dedicated environment")

from app.models.knowledge_base import KnowledgeBase
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class GraphRAGService:
    """GraphRAG 服务类"""
    
    def __init__(self):
        # 获取当前文件的绝对路径，然后构建GraphRAG工作空间路径
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent.parent  # 回到backend目录
        self.workspace_path = backend_dir / "graphrag_workspace"
        self.input_path = self.workspace_path / "input"
        self.output_path = self.workspace_path / "output"
        self.config_path = self.workspace_path / "settings.yaml"
        
        # 确保目录存在
        self.workspace_path.mkdir(exist_ok=True)
        self.input_path.mkdir(exist_ok=True)
        self.output_path.mkdir(exist_ok=True)
        
        # OpenAI和GraphRAG配置
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("GRAPHRAG_MODEL", "gpt-4o")
        self.embedding_model = os.getenv("GRAPHRAG_EMBEDDING_MODEL", "text-embedding-3-small")
        self.concurrent_requests = int(os.getenv("GRAPHRAG_CONCURRENT_REQUESTS", "25"))
        self.tpm = int(os.getenv("GRAPHRAG_TPM", "50000"))
        self.rpm = int(os.getenv("GRAPHRAG_RPM", "500"))
        self.request_timeout = float(os.getenv("GRAPHRAG_REQUEST_TIMEOUT", "180.0"))
        self.max_retries = int(os.getenv("GRAPHRAG_MAX_RETRIES", "10"))
        
        # GraphRAG查询实例
        self._global_search = None
        self._local_search = None
        
        # GraphRAG虚拟环境路径
        self.graphrag_venv_path = backend_dir / "graphrag_venv"
        self.graphrag_python = self.graphrag_venv_path / "bin" / "python"
        self.graphrag_executable = self.graphrag_venv_path / "bin" / "graphrag"
    
    def is_available(self) -> bool:
        """检查GraphRAG是否可用"""
        if GRAPHRAG_AVAILABLE and bool(self.api_key):
            return True
        # 检查专用虚拟环境中的GraphRAG
        return (self.graphrag_executable.exists() and 
                bool(self.api_key) and 
                self.workspace_path.exists())
    
    def _run_graphrag_command(self, cmd: List[str], cwd: str = None) -> Dict[str, Any]:
        """在GraphRAG虚拟环境中运行命令"""
        if cwd is None:
            cwd = str(self.workspace_path)
            
        try:
            # 设置环境变量
            env = os.environ.copy()
            env["GRAPHRAG_API_KEY"] = self.api_key
            
            # 运行命令
            result = subprocess.run(
                [str(self.graphrag_executable)] + cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                env=env,
                timeout=300  # 5分钟超时
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 5 minutes",
                "stderr": "Timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stderr": str(e)
            }
    
    def create_default_config(self) -> Dict[str, Any]:
        """创建默认的GraphRAG配置"""
        config = {
            "llm": {
                "api_key": self.api_key,
                "type": "openai_chat",
                "model": self.model,
                "model_supports_json": True,
                "max_tokens": 4000,
                "temperature": 0.0,
                "top_p": 1.0,
                "n": 1,
                "request_timeout": self.request_timeout,
                "api_base": None,
                "api_version": None,
                "organization": None,
                "proxy": None,
                "cognitive_services_endpoint": None,
                "deployment_name": None,
                "tokens_per_minute": self.tpm,
                "requests_per_minute": self.rpm,
                "max_retries": self.max_retries,
                "max_retry_wait": 10.0,
                "sleep_on_rate_limit_recommendation": True,
                "concurrent_requests": self.concurrent_requests
            },
            "parallelization": {
                "stagger": 0.3,
                "num_threads": 50
            },
            "async_mode": "threaded",
            "embeddings": {
                "llm": {
                    "api_key": self.api_key,
                    "type": "openai_embedding",
                    "model": self.embedding_model,
                    "api_base": None,
                    "api_version": None,
                    "organization": None,
                    "proxy": None,
                    "cognitive_services_endpoint": None,
                    "deployment_name": None,
                    "tokens_per_minute": self.tpm * 3,  # 嵌入模型通常有更高的限制
                    "requests_per_minute": self.rpm * 2,
                    "max_retries": self.max_retries,
                    "max_retry_wait": 10.0,
                    "sleep_on_rate_limit_recommendation": True,
                    "concurrent_requests": self.concurrent_requests
                }
            },
            "chunks": {
                "size": 300,
                "overlap": 100,
                "group_by_columns": ["id"]
            },
            "input": {
                "type": "file",
                "file_type": "text",
                "base_dir": str(self.input_path),
                "file_encoding": "utf-8",
                "file_pattern": ".*\\.txt$"
            },
            "cache": {
                "type": "file",
                "base_dir": str(self.workspace_path / "cache")
            },
            "storage": {
                "type": "file",
                "base_dir": str(self.output_path)
            },
            "reporting": {
                "type": "file",
                "base_dir": str(self.workspace_path / "reports")
            },
            "entity_extraction": {
                "llm": {
                    "api_key": self.api_key,
                    "type": "openai_chat",
                    "model": self.model,
                    "max_tokens": 3000,
                    "temperature": 0.0
                },
                "prompt": "从以下文本中提取重要的实体：人物、组织、地点、概念等。",
                "entity_types": ["人物", "组织", "地点", "概念", "事件"],
                "max_gleanings": 1
            },
            "summarize_descriptions": {
                "llm": {
                    "api_key": self.api_key,
                    "type": "openai_chat",
                    "model": self.model,
                    "max_tokens": 500,
                    "temperature": 0.0
                },
                "prompt": "请简要总结以下描述:",
                "max_length": 500
            },
            "community_reports": {
                "llm": {
                    "api_key": self.api_key,
                    "type": "openai_chat",
                    "model": self.model,
                    "max_tokens": 2000,
                    "temperature": 0.0
                },
                "prompt": "基于以下信息创建一个社区报告:",
                "max_length": 1500,
                "max_input_length": 8000
            },
            "claim_extraction": {
                "llm": {
                    "api_key": self.api_key,
                    "type": "openai_chat",
                    "model": self.model,
                    "max_tokens": 1000,
                    "temperature": 0.0
                },
                "prompt": "从文本中提取重要的声明和观点:",
                "description": "用于提取文档中的关键声明",
                "max_gleanings": 1
            },
            "cluster_graph": {
                "max_cluster_size": 10
            },
            "embed_graph": {
                "enabled": False
            },
            "umap": {
                "enabled": False
            },
            "snapshots": {
                "graphml": False,
                "raw_entities": False,
                "top_level_nodes": False
            },
            "local_search": {
                "text_unit_prop": 0.5,
                "community_prop": 0.1,
                "conversation_history_max_turns": 5,
                "top_k_mapped_entities": 10,
                "top_k_relationships": 10,
                "max_tokens": 12000
            },
            "global_search": {
                "max_tokens": 12000,
                "data_max_tokens": 12000,
                "map_max_tokens": 1000,
                "reduce_max_tokens": 2000,
                "concurrency": 32
            }
        }
        
        return config
    
    async def build_index(self, knowledge_items: List[KnowledgeBase]) -> Dict[str, Any]:
        """构建GraphRAG索引"""
        if not self.is_available():
            raise ValueError("GraphRAG不可用，请检查安装和API密钥配置")
        
        try:
            # 清理输入目录
            if self.input_path.exists():
                shutil.rmtree(self.input_path)
            self.input_path.mkdir(exist_ok=True)
            
            # 准备输入文档
            logger.info(f"准备 {len(knowledge_items)} 个文档用于GraphRAG索引构建")
            
            for i, item in enumerate(knowledge_items):
                # 为每个文档创建文本文件
                doc_file = self.input_path / f"doc_{item.id}_{i}.txt"
                
                # 组合文档内容
                content_parts = []
                if item.title:
                    content_parts.append(f"标题: {item.title}")
                if item.summary:
                    content_parts.append(f"摘要: {item.summary}")
                if item.content:
                    content_parts.append(f"内容: {item.content}")
                if item.ai_analysis:
                    content_parts.append(f"AI分析: {item.ai_analysis}")
                
                full_content = "\n\n".join(content_parts)
                
                with open(doc_file, 'w', encoding='utf-8') as f:
                    f.write(full_content)
            
            logger.info("开始运行GraphRAG索引流水线...")
            
            # 如果GraphRAG直接可用，使用原有方法
            if GRAPHRAG_AVAILABLE:
                # 创建配置文件
                config = self.create_default_config()
                
                # 保存配置为YAML格式
                import yaml
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
                # 运行GraphRAG索引构建
                pipeline_config = PipelineConfig.from_dict(config)
                
                # 异步运行索引构建
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: run_pipeline_with_config(pipeline_config)
                )
            else:
                # 使用subprocess调用专用虚拟环境
                logger.info("使用专用虚拟环境运行GraphRAG索引构建...")
                
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._run_graphrag_command(["index"])
                )
                
                if not result["success"]:
                    raise Exception(f"GraphRAG索引构建失败: {result.get('error', result.get('stderr', '未知错误'))}")
                
                logger.info("GraphRAG索引构建完成")
            
            # 检查输出
            artifacts_path = self.output_path / "artifacts"
            if artifacts_path.exists():
                artifacts = list(artifacts_path.glob("*.parquet"))
                logger.info(f"生成了 {len(artifacts)} 个索引文件")
            
            return {
                "success": True,
                "message": "GraphRAG索引构建成功",
                "documents_processed": len(knowledge_items),
                "output_path": str(self.output_path)
            }
            
        except Exception as e:
            logger.error(f"GraphRAG索引构建失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "GraphRAG索引构建失败"
            }
    
    def _init_search_engines(self):
        """初始化搜索引擎"""
        if not self.is_available():
            return False
        
        try:
            artifacts_path = self.output_path / "artifacts"
            if not artifacts_path.exists():
                logger.warning("GraphRAG artifacts not found. Please build index first.")
                return False
            
            # 初始化LLM
            llm = ChatOpenAI(
                api_key=self.api_key,
                model=self.model,
                api_type=OpenaiApiType.OpenAI,
                max_retries=3,
            )
            
            # 读取实体和报告
            entities = read_indexer_entities(
                str(artifacts_path),
                entity_table="create_final_entities",
                entity_embedding_table="create_final_entities"
            )
            
            reports = read_indexer_reports(
                str(artifacts_path),
                report_table="create_final_community_reports"
            )
            
            # 初始化全局搜索
            context_builder = GlobalCommunityContext(
                community_reports=reports,
                entities=entities,
                token_encoder=llm.get_token_encoder()
            )
            
            self._global_search = GlobalSearch(
                llm=llm,
                context_builder=context_builder,
                token_encoder=llm.get_token_encoder(),
                max_data_tokens=12000,
                map_llm_params={
                    "max_tokens": 1000,
                    "temperature": 0.0,
                },
                reduce_llm_params={
                    "max_tokens": 2000,
                    "temperature": 0.0,
                }
            )
            
            # 初始化本地搜索
            context_builder_local = LocalSearchMixedContext(
                community_reports=reports,
                text_units=None,  # 可以后续添加
                entities=entities,
                relationships=None,  # 可以后续添加
                entity_text_embeddings=None,  # 可以后续添加
                embedding_vectorstore_key="entity_embedding",
                text_embedder=None,  # 可以后续添加
                token_encoder=llm.get_token_encoder()
            )
            
            self._local_search = LocalSearch(
                llm=llm,
                context_builder=context_builder_local,
                token_encoder=llm.get_token_encoder(),
                llm_params={
                    "max_tokens": 2000,
                    "temperature": 0.0,
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"初始化搜索引擎失败: {str(e)}")
            return False
    
    async def global_search(self, query: str) -> Dict[str, Any]:
        """执行全局搜索"""
        if not self._global_search:
            if not self._init_search_engines():
                return {
                    "success": False,
                    "error": "搜索引擎初始化失败",
                    "message": "请先构建GraphRAG索引"
                }
        
        try:
            logger.info(f"执行全局搜索: {query}")
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._global_search.search(query)
            )
            
            return {
                "success": True,
                "query": query,
                "response": result.response,
                "context_data": result.context_data if hasattr(result, 'context_data') else None,
                "search_type": "global"
            }
            
        except Exception as e:
            logger.error(f"全局搜索失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "全局搜索执行失败"
            }
    
    async def local_search(self, query: str) -> Dict[str, Any]:
        """执行本地搜索"""
        if not self._local_search:
            if not self._init_search_engines():
                return {
                    "success": False,
                    "error": "搜索引擎初始化失败",
                    "message": "请先构建GraphRAG索引"
                }
        
        try:
            logger.info(f"执行本地搜索: {query}")
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._local_search.search(query)
            )
            
            return {
                "success": True,
                "query": query,
                "response": result.response,
                "context_data": result.context_data if hasattr(result, 'context_data') else None,
                "search_type": "local"
            }
            
        except Exception as e:
            logger.error(f"本地搜索失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "本地搜索执行失败"
            }
    
    async def hybrid_search(self, query: str) -> Dict[str, Any]:
        """执行混合搜索（全局+本地）"""
        try:
            # 并行执行全局和本地搜索
            global_result, local_result = await asyncio.gather(
                self.global_search(query),
                self.local_search(query),
                return_exceptions=True
            )
            
            return {
                "success": True,
                "query": query,
                "global_search": global_result if not isinstance(global_result, Exception) else {"error": str(global_result)},
                "local_search": local_result if not isinstance(local_result, Exception) else {"error": str(local_result)},
                "search_type": "hybrid"
            }
            
        except Exception as e:
            logger.error(f"混合搜索失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "混合搜索执行失败"
            }
    
    def get_index_status(self) -> Dict[str, Any]:
        """获取索引状态"""
        artifacts_path = self.output_path / "artifacts"
        
        status = {
            "index_exists": artifacts_path.exists(),
            "workspace_path": str(self.workspace_path),
            "graphrag_available": self.is_available(),
            "api_key_configured": bool(self.api_key)
        }
        
        if artifacts_path.exists():
            artifacts = list(artifacts_path.glob("*.parquet"))
            status.update({
                "artifact_count": len(artifacts),
                "artifacts": [f.name for f in artifacts],
                "last_modified": max([f.stat().st_mtime for f in artifacts]) if artifacts else None
            })
        
        return status

# 创建全局实例
graphrag_service = GraphRAGService() 