#!/usr/bin/env python3
"""
读取环境变量示例程序
演示如何使用 EVM Python API 读取和管理环境变量
"""

from evm.python.main import EnvironmentManager


def main():
    """演示如何读取和操作环境变量。"""
    
    # 初始化环境管理器
    manager = EnvironmentManager()
    
    print("=== EVM 读取环境变量演示 ===\n")
    
    # 1. 列出所有环境变量
    print("1. 当前所有环境变量:")
    manager.list()
    print()
    
    # 2. 设置一些示例变量用于演示
    print("2. 设置示例环境变量...")
    manager.set('DEMO_APP_NAME', 'My Demo Application')
    manager.set('DEMO_VERSION', '1.0.0')
    manager.set('DEMO_DEBUG', 'true')
    print()
    
    # 3. 读取单个环境变量
    print("3. 读取单个环境变量:")
    try:
        app_name = manager.get('DEMO_APP_NAME')
        print(f"   应用名称已读取")
    except SystemExit:
        print("   应用名称未找到")
    print()
    
    # 4. 检查环境变量是否存在
    print("4. 检查环境变量是否存在:")
    exists = manager.exists('DEMO_VERSION')
    print(f"   DEMO_VERSION 存在: {exists}")
    
    exists = manager.exists('NON_EXISTENT_VAR')
    print(f"   NON_EXISTENT_VAR 存在: {exists}")
    print()
    
    # 5. 搜索环境变量
    print("5. 搜索包含 'DEMO' 的变量:")
    manager.search('DEMO')
    print()
    
    # 6. 搜索变量值
    print("6. 在值中搜索 '1.0.0':")
    manager.search('1.0.0', search_value=True)
    print()
    
    # 7. 按组读取变量
    print("7. 设置一些分组变量...")
    manager.set_grouped('demo_group', 'API_URL', 'https://api.example.com')
    manager.set_grouped('demo_group', 'API_KEY', 'demo_key_123')
    print()
    
    print("8. 读取分组变量:")
    try:
        api_url = manager.get_grouped('demo_group', 'API_URL')
        print(f"   API_URL 已读取")
    except SystemExit:
        print("   API_URL 未找到")
    print()
    
    print("9. 列出 'demo_group' 组中的所有变量:")
    manager.list_group('demo_group', no_prefix=False)
    print()
    
    # 10. 列出所有组
    print("10. 列出所有组:")
    manager.list_groups()
    print()
    
    # 11. 导出到不同格式
    print("11. 导出环境变量到不同格式...")
    manager.export('json', 'output/demo_config.json')
    manager.export('env', 'output/demo_config.env')
    print()
    
    # 12. 清理演示变量
    print("12. 清理演示变量...")
    manager.delete('DEMO_APP_NAME')
    manager.delete('DEMO_VERSION')
    manager.delete('DEMO_DEBUG')
    manager.delete_grouped('demo_group', 'API_URL')
    manager.delete_grouped('demo_group', 'API_KEY')
    print()
    
    print("=== 演示完成 ===")
    print("\n提示: 导出的配置文件保存在 output/ 目录中")


if __name__ == '__main__':
    import os
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)
    main()
