#!/usr/bin/env python3
"""
知识库初始化脚本
用于创建数据库表和初始化预设问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base, DATABASE_URL
from app.models.knowledge_base import KnowledgeBase, KnowledgeQA, PresetQuestion
from app.services.knowledge_service import KnowledgeService

def init_database():
    """初始化数据库表"""
    print("🔄 正在初始化数据库表...")
    
    # 创建数据库引擎
    engine = create_engine(DATABASE_URL)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    
    return engine

def init_preset_questions():
    """初始化预设问题"""
    print("🔄 正在初始化预设问题...")
    
    # 创建数据库会话
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # 检查是否已有预设问题
        existing_count = db.query(PresetQuestion).count()
        if existing_count > 0:
            print(f"📋 已存在 {existing_count} 个预设问题，跳过初始化")
            return
        
        # 初始化预设问题
        KnowledgeService.init_preset_questions(db)
        
        # 验证创建结果
        created_count = db.query(PresetQuestion).count()
        print(f"✅ 成功创建 {created_count} 个预设问题")
        
    except Exception as e:
        print(f"❌ 初始化预设问题失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """主函数"""
    print("🚀 开始初始化知识库系统...")
    print("=" * 50)
    
    try:
        # 初始化数据库
        engine = init_database()
        
        # 初始化预设问题
        init_preset_questions()
        
        print("=" * 50)
        print("🎉 知识库系统初始化完成！")
        print()
        print("📊 系统功能:")
        print("  • 文档分析结果自动存储到知识库")
        print("  • 智能问答基于知识库内容")
        print("  • 预设问题快速查询")
        print("  • 知识搜索和统计")
        print()
        print("🔗 相关API端点:")
        print("  • 知识搜索: POST /api/knowledge/search")
        print("  • 智能问答: POST /api/knowledge/ask")
        print("  • 预设问题: GET /api/knowledge/preset-questions")
        print("  • 知识统计: GET /api/knowledge/stats")
        print()
        print("🌐 前端页面:")
        print("  • 知识库问答: http://localhost:3000/knowledge")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 