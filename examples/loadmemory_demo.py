#!/usr/bin/env python3
"""
演示如何使用 evm loadmemory 功能
将 EVM 存储的环境变量加载到系统内存中
"""

import os
import subprocess
import sys


def main():
    """演示 loadmemory 功能。"""
    
    print("=== EVM Load Memory 演示 ===\n")
    
    # 1. 显示当前环境变量状态
    print("1. 检查当前系统环境变量:")
    test_vars = ['EVM:DEMO_API_KEY', 'EVM:DEMO_DATABASE_URL', 'DEMO_API_KEY']
    for var in test_vars:
        value = os.environ.get(var, 'NOT SET')
        if value != 'NOT SET' and len(value) > 30:
            value = value[:30] + '...'
        print(f"   {var}: {value}")
    print()
    
    # 2. 使用 EVM 设置一些变量
    print("2. 使用 EVM 设置示例变量:")
    subprocess.run([sys.executable, '-m', 'evm.python', 'set', 'DEMO_API_KEY', 'sk-demo-12345'], 
                   capture_output=True)
    subprocess.run([sys.executable, '-m', 'evm.python', 'set', 'DEMO_DATABASE_URL', 'postgres://localhost:5432/demo'],
                   capture_output=True)
    print("   ✓ 已设置 DEMO_API_KEY 和 DEMO_DATABASE_URL")
    print()
    
    # 3. 加载到内存（带 EVM: 前缀）
    print("3. 加载到内存（自动添加 EVM: 前缀）:")
    
    test_script = '''
import os
import sys

# 先显示加载前的状态
print("   加载前:")
print(f"     EVM:DEMO_API_KEY: {os.environ.get('EVM:DEMO_API_KEY', 'NOT SET')}")

# 导入 EVM 并加载到内存
from evm.python.main import EnvironmentManager
mgr = EnvironmentManager()
mgr.load_to_memory()  # 默认添加 EVM: 前缀

# 显示加载后的状态
print("   加载后:")
print(f"     EVM:DEMO_API_KEY: {os.environ.get('EVM:DEMO_API_KEY', 'NOT SET')}")
print(f"     EVM:DEMO_DATABASE_URL: {os.environ.get('EVM:DEMO_DATABASE_URL', 'NOT SET')}")
'''
    
    result = subprocess.run([sys.executable, '-c', test_script], 
                           capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"   错误: {result.stderr}")
    print()
    
    # 4. 使用 --no-prefix 加载
    print("4. 使用 --no-prefix 加载（不添加前缀）:")
    
    test_script_no_prefix = '''
import os
from evm.python.main import EnvironmentManager

mgr = EnvironmentManager()
mgr.load_to_memory(add_evm_prefix=False)  # 不添加前缀

print("   加载的变量:")
for key in sorted(os.environ.keys()):
    if key.startswith('DEMO_'):
        print(f"     {key}: {os.environ[key][:40]}...")
'''
    
    result = subprocess.run([sys.executable, '-c', test_script_no_prefix],
                           capture_output=True, text=True)
    print(result.stdout)
    print()
    
    # 5. 使用 prefix 过滤 + EVM 前缀
    print("5. 使用 prefix 过滤 + EVM 前缀:")
    
    test_script_filter = '''
import os
from evm.python.main import EnvironmentManager

mgr = EnvironmentManager()

# 只加载以 DEMO_ 开头的变量，并添加 EVM: 前缀
mgr.load_to_memory(filter_prefix='DEMO_')

print("   加载的变量:")
for key in sorted(os.environ.keys()):
    if key.startswith('EVM:DEMO_'):
        print(f"     {key}: {os.environ[key][:40]}...")
'''
    
    result = subprocess.run([sys.executable, '-c', test_script_filter],
                           capture_output=True, text=True)
    print(result.stdout)
    print()
    
    # 6. 使用 evm exec 运行命令
    print("6. 使用 'evm exec' 运行命令（自动加载环境变量）:")
    result = subprocess.run([sys.executable, '-m', 'evm.python', 'exec', '--',
                            sys.executable, '-c', 
                            "import os; print(f\"   API_KEY: {os.environ.get('API_KEY', 'NOT SET')[:30]}...\")"],
                           capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"   错误: {result.stderr}")
    print()
    
    # 7. 清理
    print("7. 清理演示变量:")
    subprocess.run([sys.executable, '-m', 'evm.python', 'delete', 'DEMO_API_KEY'],
                   capture_output=True)
    subprocess.run([sys.executable, '-m', 'evm.python', 'delete', 'DEMO_DATABASE_URL'],
                   capture_output=True)
    print("   ✓ 已删除演示变量")
    print()
    
    print("=== 演示完成 ===")
    print("\n使用说明:")
    print("  evm loadmemory                    # 加载所有变量，添加 EVM: 前缀")
    print("  evm loadmemory --no-prefix        # 加载所有变量，不添加前缀")
    print("  evm loadmemory --prefix DEMO_     # 只加载以 DEMO_ 开头的变量")
    print("  evm exec -- python script.py      # 运行命令并自动加载环境变量")


if __name__ == '__main__':
    main()
