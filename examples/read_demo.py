#!/usr/bin/env python3
"""
直接读取系统环境变量的示例程序
不使用 EnvironmentManager，直接使用 os.environ 读取环境变量
"""

import os
import json


def main():
    """演示如何直接读取系统环境变量。"""
    
    print("=== 直接读取系统环境变量演示 ===\n")
    
    # 1. 读取单个环境变量
    print("1. 读取单个环境变量:")
    home = os.environ.get('HOME')
    print(f"   HOME: {home}")
    
    path = os.environ.get('PATH')
    print(f"   PATH (前50字符): {path[:50]}...")
    
    user = os.environ.get('USER')
    print(f"   USER: {user}")
    print()
    
    # 2. 读取 EVM 特定的环境变量（从 ~/.evm/env.json 加载）
    print("2. 读取 EVM 存储的环境变量:")
    evm_storage = os.path.expanduser('~/.evm/env.json')
    
    if os.path.exists(evm_storage):
        with open(evm_storage, 'r') as f:
            evm_vars = json.load(f)
        
        if evm_vars:
            print(f"   从 {evm_storage} 读取到 {len(evm_vars)} 个变量")
            
            # 显示前5个变量
            for i, (key, value) in enumerate(list(evm_vars.items())[:5]):
                # 隐藏敏感信息
                if 'KEY' in key or 'PASSWORD' in key or 'SECRET' in key:
                    value = '***'
                print(f"   - {key}: {value}")
            
            if len(evm_vars) > 5:
                print(f"   ... 还有 {len(evm_vars) - 5} 个变量")
        else:
            print("   EVM 存储中没有变量")
    else:
        print(f"   EVM 存储文件不存在: {evm_storage}")
    print()
    
    # 3. 检查特定变量是否存在
    print("3. 检查特定环境变量:")
    check_vars = ['PATH', 'HOME', 'USER', 'SHELL', 'EVM_TEST']
    for var in check_vars:
        exists = var in os.environ
        print(f"   {var}: {'✓ 存在' if exists else '✗ 不存在'}")
    print()
    
    # 4. 获取所有环境变量
    print("4. 环境变量统计:")
    total_vars = len(os.environ)
    print(f"   系统环境变量总数: {total_vars}")
    print(os.environ)  # 打印所有环境变量（可能很多，实际使用中可以选择性打印）
    
    # 统计包含特定关键词的变量
    api_vars = [k for k in os.environ if 'API' in k]
    db_vars = [k for k in os.environ if 'DB' in k or 'DATABASE' in k]
    
    print(f"   包含 'API' 的变量: {len(api_vars)}")
    if api_vars:
        for var in api_vars:
            print(f"     - {var}")
    
    print(f"   包含 'DB/DATABASE' 的变量: {len(db_vars)}")
    if db_vars:
        for var in db_vars:
            print(f"     - {var}")
    print()
    
    # 5. 设置和读取临时环境变量
    print("5. 设置临时环境变量:")
    os.environ['DEMO_TEMP_VAR'] = 'This is a temporary value'
    temp_value = os.environ.get('DEMO_TEMP_VAR')
    print(f"   DEMO_TEMP_VAR: {temp_value}")
    
    # 清理
    del os.environ['DEMO_TEMP_VAR']
    print("   已删除 DEMO_TEMP_VAR")
    print()
    
    # 6. 使用 os.getenv 提供默认值
    print("6. 使用默认值读取:")
    api_key = os.getenv('API_KEY', 'default_api_key')
    debug_mode = os.getenv('DEBUG', 'false')
    timeout = os.getenv('TIMEOUT', '30')
    
    print(f"   API_KEY: {api_key}")
    print(f"   DEBUG: {debug_mode}")
    print(f"   TIMEOUT: {timeout}")
    print()
    
    print("=== 演示完成 ===")


if __name__ == '__main__':
    main()
