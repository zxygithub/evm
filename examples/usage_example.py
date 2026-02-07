#!/usr/bin/env python3
"""
演示如何在 Python 代码中使用 EVM 的示例脚本。
"""

from evm.python.main import EnvironmentManager
import os


def main():
    """演示 EVM 在 Python 代码中的用法。"""

    # 使用默认位置初始化 (~/.evm/env.json)
    manager = EnvironmentManager()

    print("=== EVM Python API 演示 ===\n")

    # 设置环境变量
    print("1. 设置环境变量...")
    manager.set('APP_NAME', 'My Application')
    manager.set('APP_VERSION', '1.0.0')
    manager.set('DEBUG', 'true')
    print()

    # 获取环境变量
    print("2. 获取环境变量...")
    app_name = manager.get('APP_NAME')
    print(f"应用程序名称: {app_name}")
    print()

    # 列出所有变量
    print("3. 列出所有变量...")
    manager.list()
    print()

    # 搜索变量
    print("4. 搜索 'APP'...")
    manager.search('APP')
    print()

    # 复制变量
    print("5. 复制变量...")
    manager.copy('APP_NAME', 'APP')
    print()

    # 重命名变量
    print("6. 重命名变量...")
    manager.rename('DEBUG', 'DEBUG_MODE')
    print()

    # 导出为不同格式
    print("7. 导出为不同格式...")
    manager.export('json', 'output/config.json')
    manager.export('env', 'output/config.env')
    manager.export('sh', 'output/export.sh')
    print()

    # 从文件加载
    print("8. 从 .env 文件加载...")
    manager.load('examples/example.env')
    print()

    # 再次列出所有变量
    print("9. 更新后的变量列表...")
    manager.list()
    print()

    # 备份
    print("10. 创建备份...")
    manager.backup('output/backup.json')
    print()

    # 在值中搜索
    print("11. 在值中搜索...")
    manager.search('localhost', search_value=True)
    print()

    # 删除变量
    print("12. 删除变量...")
    manager.delete('APP')
    print()

    # 在组中设置变量
    print("13. 在组中设置变量...")
    manager.set_grouped('dev', 'DATABASE_URL', 'localhost:5432')
    manager.set_grouped('dev', 'API_KEY', 'dev_key_123')
    manager.set_grouped('prod', 'DATABASE_URL', 'prod.example.com:5432')
    manager.set_grouped('prod', 'API_KEY', 'prod_key_456')
    print()

    # 从组中获取变量
    print("14. 从组中获取变量...")
    dev_db = manager.get_grouped('dev', 'DATABASE_URL')
    print(f"开发数据库URL: {dev_db}")
    print()

    # 按组列出变量
    print("15. 列出 'dev' 组中的变量...")
    manager.list(group='dev')
    print()

    # 列出所有组
    print("16. 列出所有组...")
    manager.list_groups()
    print()

    # 按命名空间分组列出变量
    print("17. 按命名空间分组列出所有变量...")
    manager.list(show_groups=True)
    print()

    # 将变量移动到组
    print("18. 将变量移动到组...")
    manager.move_to_group('APP_NAME', 'prod')
    print()

    # 从组中删除变量
    print("19. 从组中删除变量...")
    manager.delete_grouped('dev', 'API_KEY')
    print()

    # 删除整个组
    print("20. 删除整个组...")
    manager.delete_group('dev')
    print()

    # 从备份恢复
    print("21. 从备份恢复...")
    manager.restore('output/backup.json', merge=True)
    print()

    # 使用环境变量执行命令 (示例: 打印 APP_NAME)
    print("22. 使用环境变量执行命令...")
    try:
        manager.execute(['sh', '-c', 'echo "APP_NAME=$APP_NAME"'])
    except SystemExit:
        pass  # exec 会退出进程，这是预期的行为
    print()

    # 清空所有变量
    print("23. 清空所有变量...")
    manager.clear()
    print()

    print("=== 演示完成 ===")


if __name__ == '__main__':
    # 创建输出目录
    os.makedirs('output', exist_ok=True)
    main()
