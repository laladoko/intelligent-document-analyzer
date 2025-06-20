"""
bcrypt配置和兼容性处理

解决bcrypt 4.x与passlib的兼容性警告问题

背景:
- bcrypt 4.0+ 改变了版本信息的存储方式，不再使用 __about__.__version__
- passlib 1.7.4 仍然尝试访问旧的版本属性，导致 AttributeError
- 这只是一个警告，不影响实际的密码哈希功能

解决方案:
- 抑制相关警告信息
- 验证bcrypt功能正常工作
- 确保密码哈希和验证功能不受影响

注意: 这是一个临时解决方案，直到passlib发布新版本完全支持bcrypt 4.x
"""

import warnings
import logging

def suppress_bcrypt_warnings():
    """抑制bcrypt版本读取相关的警告"""
    # 抑制passlib中bcrypt版本读取的警告
    warnings.filterwarnings(
        "ignore", 
        message=".*error reading bcrypt version.*",
        category=UserWarning,
        module="passlib.handlers.bcrypt"
    )
    
    # 设置passlib日志级别为ERROR以减少警告输出
    logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)

def configure_bcrypt():
    """配置bcrypt相关设置"""
    suppress_bcrypt_warnings()
    
    # 验证bcrypt是否正常工作
    try:
        import bcrypt
        # 简单测试确保bcrypt功能正常
        test_pwd = b"test"
        hashed = bcrypt.hashpw(test_pwd, bcrypt.gensalt())
        if bcrypt.checkpw(test_pwd, hashed):
            print("✅ bcrypt配置正常")
        else:
            print("⚠️ bcrypt功能测试失败")
    except Exception as e:
        print(f"❌ bcrypt配置错误: {e}")

# 在模块导入时自动配置
configure_bcrypt() 