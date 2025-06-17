#!/usr/bin/env python3
"""
数据库初始化脚本
创建默认角色和管理员用户
"""

import asyncio
from sqlalchemy.orm import Session
from app.models.database import engine, SessionLocal
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

def init_database():
    """初始化数据库，创建默认数据"""
    db = SessionLocal()
    
    try:
        print("🚀 开始初始化数据库...")
        
        # 创建默认角色
        print("📝 创建默认用户角色...")
        
        # 超级管理员角色
        admin_role = db.query(UserRole).filter(UserRole.name == "admin").first()
        if not admin_role:
            admin_role = UserRole(
                name="admin",
                display_name="超级管理员",
                description="系统超级管理员，拥有所有权限",
                permissions='["read", "write", "delete", "admin", "user_management", "system_config"]'
            )
            db.add(admin_role)
            print("✅ 创建超级管理员角色")
        
        # 普通用户角色
        user_role = db.query(UserRole).filter(UserRole.name == "user").first()
        if not user_role:
            user_role = UserRole(
                name="user",
                display_name="普通用户",
                description="系统普通用户，基础权限",
                permissions='["read", "write"]'
            )
            db.add(user_role)
            print("✅ 创建普通用户角色")
        
        # 分析师角色
        analyst_role = db.query(UserRole).filter(UserRole.name == "analyst").first()
        if not analyst_role:
            analyst_role = UserRole(
                name="analyst",
                display_name="数据分析师",
                description="数据分析师，拥有分析和报告权限",
                permissions='["read", "write", "analyze", "report"]'
            )
            db.add(analyst_role)
            print("✅ 创建数据分析师角色")
        
        db.commit()
        
        # 创建默认管理员用户
        print("👤 创建默认管理员用户...")
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@dataanalays.com",
                full_name="系统管理员",
                role_id=admin_role.id,
                is_active=True,
                is_verified=True,
                is_superuser=True,
                department="技术部",
                position="系统管理员"
            )
            admin_user.set_password("admin123456")  # 默认密码
            db.add(admin_user)
            print("✅ 创建管理员用户: admin / admin123456")
        
        # 创建测试用户
        print("👥 创建测试用户...")
        test_user = db.query(User).filter(User.username == "testuser").first()
        if not test_user:
            test_user = User(
                username="testuser",
                email="test@dataanalays.com",
                full_name="测试用户",
                role_id=user_role.id,
                is_active=True,
                is_verified=True,
                department="测试部",
                position="测试工程师"
            )
            test_user.set_password("test123456")  # 默认密码
            db.add(test_user)
            print("✅ 创建测试用户: testuser / test123456")
        
        # 创建分析师用户
        analyst_user = db.query(User).filter(User.username == "analyst").first()
        if not analyst_user:
            analyst_user = User(
                username="analyst",
                email="analyst@dataanalays.com",
                full_name="数据分析师",
                role_id=analyst_role.id,
                is_active=True,
                is_verified=True,
                department="数据部",
                position="高级数据分析师"
            )
            analyst_user.set_password("analyst123456")  # 默认密码
            db.add(analyst_user)
            print("✅ 创建分析师用户: analyst / analyst123456")
        
        db.commit()
        
        print("\n🎉 数据库初始化完成！")
        print("\n📋 默认用户账户:")
        print("┌─────────────┬─────────────┬──────────────┬────────────┐")
        print("│ 用户名      │ 密码        │ 角色         │ 邮箱       │")
        print("├─────────────┼─────────────┼──────────────┼────────────┤")
        print("│ admin       │ admin123456 │ 超级管理员   │ admin@...  │")
        print("│ testuser    │ test123456  │ 普通用户     │ test@...   │")
        print("│ analyst     │ analyst123456│ 数据分析师   │ analyst@...│")
        print("└─────────────┴─────────────┴──────────────┴────────────┘")
        print("\n⚠️  请在生产环境中修改默认密码！")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database() 