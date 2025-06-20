#!/usr/bin/env python3
"""
数据库连接测试脚本
测试PostgreSQL数据库连接是否正常
"""

import os
import sys
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import create_engine, text

# 加载环境变量
load_dotenv('backend/.env')

def test_database_connection():
    """测试数据库连接"""
    
    # 获取数据库URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ 错误：未找到DATABASE_URL配置")
        return False
    
    print(f"🔗 数据库URL: {database_url.replace('password', '***')}")
    
    try:
        # 创建数据库引擎
        engine = create_engine(database_url)
        
        print("📡 测试数据库连接...")
        
        # 测试连接
        with engine.connect() as connection:
            # 执行简单查询
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
            print("✅ 数据库连接成功!")
            print(f"📝 PostgreSQL版本: {version}")
            
            # 检查数据库是否为空
            result = connection.execute(text("""
                SELECT count(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.fetchone()[0]
            
            print(f"📊 当前数据库表数量: {table_count}")
            
            if table_count == 0:
                print("⚠️  数据库为空，需要初始化表结构")
            else:
                print("✅ 数据库已包含表结构")
            
            return True
            
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("💡 请运行: pip install psycopg2-binary sqlalchemy")
        return False
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 数据库连接失败: {error_msg}")
        
        if "authentication" in error_msg.lower():
            print("💡 建议：检查数据库用户名和密码")
        elif "does not exist" in error_msg.lower():
            print("💡 建议：检查数据库名称是否正确")
        elif "connection refused" in error_msg.lower():
            print("💡 建议：检查PostgreSQL服务是否启动")
        elif "timeout" in error_msg.lower():
            print("💡 建议：检查网络连接和数据库服务器状态")
        else:
            print("💡 建议：检查数据库配置和网络连接")
        
        return False

def show_database_info():
    """显示数据库配置信息"""
    database_url = os.getenv('DATABASE_URL', 'Not configured')
    
    if database_url.startswith('postgresql://'):
        # 解析PostgreSQL URL
        parts = database_url.replace('postgresql://', '').split('@')
        if len(parts) == 2:
            user_pass = parts[0]
            host_db = parts[1]
            
            user = user_pass.split(':')[0]
            host_port_db = host_db.split('/')
            host_port = host_port_db[0]
            database = host_port_db[1] if len(host_port_db) > 1 else 'unknown'
            
            print("📋 数据库配置信息:")
            print(f"   类型: PostgreSQL")
            print(f"   主机: {host_port}")
            print(f"   用户: {user}")
            print(f"   数据库: {database}")
    else:
        print(f"📋 数据库配置: {database_url}")

if __name__ == "__main__":
    print("🧪 数据库连接测试")
    print("=" * 40)
    
    show_database_info()
    print()
    
    success = test_database_connection()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 数据库连接测试通过")
        print("💡 可以继续初始化数据库表结构")
    else:
        print("⚠️  数据库连接失败")
        print("🔧 请检查PostgreSQL服务和配置")
    
    sys.exit(0 if success else 1) 