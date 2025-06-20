from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from app.config.timeout_config import DB_TIMEOUT, DB_CONNECTION_TIMEOUT

load_dotenv()

# 数据库连接配置
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://hsx@localhost:5432/dataanalays"
)

# 创建数据库引擎，配置超时设置
engine = create_engine(
    DATABASE_URL,
    pool_timeout=DB_CONNECTION_TIMEOUT,
    pool_recycle=3600,  # 1小时回收连接
    pool_pre_ping=True,  # 连接前检查
    connect_args={
        "connect_timeout": int(DB_CONNECTION_TIMEOUT)
    } if "postgresql" in DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 元数据
metadata = MetaData()

# 数据库依赖注入
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 