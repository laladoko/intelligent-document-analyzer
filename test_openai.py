#!/usr/bin/env python3
"""
OpenAI API连接测试脚本
测试当前配置的API密钥是否有效
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('backend/.env')

def test_openai_connection():
    """测试OpenAI API连接"""
    
    # 检查API密钥
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key or api_key == 'your_openai_api_key_here':
        print("❌ 错误：未配置有效的OpenAI API密钥")
        print("💡 请运行: ./setup_openai.sh 来配置API密钥")
        return False
    
    print(f"🔑 找到API密钥: {api_key[:20]}...")
    
    try:
        # 导入OpenAI库
        import openai
        from openai import OpenAI
        
        # 创建客户端
        client = OpenAI(api_key=api_key)
        
        print("📡 测试API连接...")
        
        # 发送测试请求
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "请回答：测试"}
            ],
            max_tokens=10,
            timeout=10
        )
        
        print("✅ OpenAI API连接成功!")
        print(f"📝 测试响应: {response.choices[0].message.content}")
        return True
        
    except ImportError:
        print("❌ 错误：未安装openai库")
        print("💡 请运行: pip install openai")
        return False
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ API连接失败: {error_msg}")
        
        if "authentication" in error_msg.lower():
            print("💡 建议：检查API密钥是否正确")
        elif "quota" in error_msg.lower():
            print("💡 建议：检查OpenAI账户余额")
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            print("💡 建议：检查网络连接或代理设置")
        else:
            print("💡 建议：访问 https://platform.openai.com/account/usage 检查账户状态")
        
        return False

if __name__ == "__main__":
    print("🧪 OpenAI API连接测试")
    print("=" * 30)
    
    success = test_openai_connection()
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 测试完成：API连接正常")
        print("💡 现在可以在网页中使用文档分析功能了")
    else:
        print("⚠️  测试失败：需要配置API密钥")
        print("🔧 运行 ./setup_openai.sh 来配置")
    
    sys.exit(0 if success else 1) 