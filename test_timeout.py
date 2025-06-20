#!/usr/bin/env python3
"""
超时配置测试脚本
用于验证各种超时设置是否正确生效
"""

import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# 测试配置
BASE_URL = "http://localhost:8000"
TIMEOUT_TESTS = [
    {
        "name": "健康检查 - 快速响应",
        "url": f"{BASE_URL}/ping",
        "method": "GET",
        "timeout": 5,
        "expected_status": 200
    },
    {
        "name": "游客登录 - 中等响应",
        "url": f"{BASE_URL}/api/auth/guest-login",
        "method": "POST",
        "timeout": 10,
        "expected_status": 200
    },
    {
        "name": "API文档 - 快速响应",
        "url": f"{BASE_URL}/docs",
        "method": "GET",
        "timeout": 15,
        "expected_status": 200
    }
]

def test_endpoint(test_config):
    """测试单个端点的超时配置"""
    print(f"🔍 测试: {test_config['name']}")
    
    try:
        start_time = time.time()
        
        if test_config['method'] == 'GET':
            response = requests.get(
                test_config['url'], 
                timeout=test_config['timeout']
            )
        elif test_config['method'] == 'POST':
            response = requests.post(
                test_config['url'], 
                timeout=test_config['timeout']
            )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == test_config['expected_status']:
            print(f"   ✅ 成功 - 响应时间: {response_time:.2f}秒")
            return True, response_time
        else:
            print(f"   ❌ 失败 - 状态码: {response.status_code}")
            return False, response_time
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ 超时 - 超过 {test_config['timeout']} 秒")
        return False, test_config['timeout']
    except requests.exceptions.ConnectionError:
        print(f"   🔌 连接错误 - 服务器可能未启动")
        return False, 0
    except Exception as e:
        print(f"   ❌ 错误: {str(e)}")
        return False, 0

def test_concurrent_requests():
    """测试并发请求的超时处理"""
    print("\n🚀 测试并发请求...")
    
    def make_request(i):
        try:
            response = requests.get(f"{BASE_URL}/ping", timeout=5)
            return f"请求 {i}: {response.status_code}"
        except Exception as e:
            return f"请求 {i}: 错误 - {str(e)}"
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(20)]
        results = []
        
        for future in as_completed(futures):
            results.append(future.result())
    
    success_count = sum(1 for r in results if "200" in r)
    print(f"   📊 并发测试结果: {success_count}/20 成功")
    
    return success_count >= 15  # 至少75%成功率

def main():
    """主测试函数"""
    print("=" * 50)
    print("🔧 超时配置测试")
    print("=" * 50)
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        print(f"✅ 服务器运行状态: {response.json()}")
    except:
        print("❌ 服务器未运行，请先启动后端服务")
        return
    
    print("\n📋 开始端点测试...")
    
    # 测试各个端点
    total_tests = len(TIMEOUT_TESTS)
    passed_tests = 0
    total_time = 0
    
    for test_config in TIMEOUT_TESTS:
        success, response_time = test_endpoint(test_config)
        if success:
            passed_tests += 1
        total_time += response_time
    
    # 并发测试
    concurrent_success = test_concurrent_requests()
    
    # 输出结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    print(f"✅ 通过测试: {passed_tests}/{total_tests}")
    print(f"⏱️  总响应时间: {total_time:.2f}秒")
    print(f"📈 平均响应时间: {total_time/total_tests:.2f}秒")
    print(f"🚀 并发测试: {'通过' if concurrent_success else '失败'}")
    
    if passed_tests == total_tests and concurrent_success:
        print("\n🎉 所有超时配置测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查配置")
    
    # 显示超时配置信息
    print("\n🔧 当前超时配置:")
    try:
        from backend.app.config.timeout_config import (
            OPENAI_TIMEOUT, DB_TIMEOUT, HTTP_TIMEOUT, SERVER_TIMEOUT
        )
        print(f"   OpenAI API: {OPENAI_TIMEOUT}秒")
        print(f"   数据库操作: {DB_TIMEOUT}秒") 
        print(f"   HTTP请求: {HTTP_TIMEOUT}秒")
        print(f"   服务器请求: {SERVER_TIMEOUT}秒")
    except ImportError:
        print("   ⚠️  无法导入超时配置")

if __name__ == "__main__":
    main() 