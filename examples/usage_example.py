#!/usr/bin/env python3
"""
演示如何在 Python 代码中使用 EVM 的示例脚本。

新版 API 说明：
- 业务方法返回消息字符串或数据，不直接打印
- 错误通过异常抛出，不使用 sys.exit()
- 使用 formatters 模块进行终端输出
"""

from evm.manager import EnvironmentManager
from evm.formatters import (
    print_vars_table,
    print_vars_by_group,
    print_search_results,
    print_groups,
)
from evm.exceptions import EVMError
import os


def main():
    """演示 EVM 在 Python 代码中的用法。"""

    manager = EnvironmentManager()

    print("=== EVM Python API 演示 ===\n")

    # 1. 设置环境变量
    print("1. 设置环境变量...")
    print(manager.set('APP_NAME', 'My Application'))
    print(manager.set('APP_VERSION', '1.0.0'))
    print(manager.set('DEBUG', 'true'))
    print()

    # 2. 获取环境变量
    print("2. 获取环境变量...")
    try:
        app_name = manager.get('APP_NAME')
        print(f"应用程序名称: {app_name}")
    except EVMError as e:
        print(f"错误: {e}")
    print()

    # 3. 列出所有变量
    print("3. 列出所有变量...")
    print_vars_table(manager.list_vars())
    print()

    # 4. 搜索变量
    print("4. 搜索 'APP'...")
    print_search_results(manager.search('APP'), 'APP')
    print()

    # 5. 复制变量
    print("5. 复制变量...")
    print(manager.copy('APP_NAME', 'APP'))
    print()

    # 6. 重命名变量
    print("6. 重命名变量...")
    print(manager.rename('DEBUG', 'DEBUG_MODE'))
    print()

    # 7. 导出为不同格式
    print("7. 导出为不同格式...")
    print(manager.export('json', 'output/config.json'))
    print(manager.export('env', 'output/config.env'))
    print(manager.export('sh', 'output/export.sh'))
    print()

    # 8. 从文件加载
    print("8. 从 .env 文件加载...")
    print(manager.load('examples/example.env'))
    print()

    # 9. 再次列出所有变量
    print("9. 更新后的变量列表...")
    print_vars_table(manager.list_vars())
    print()

    # 10. 备份
    print("10. 创建备份...")
    print(manager.backup('output/backup.json'))
    print()

    # 11. 在值中搜索
    print("11. 在值中搜索...")
    print_search_results(manager.search('localhost', search_value=True), 'localhost', True)
    print()

    # 12. 删除变量
    print("12. 删除变量...")
    print(manager.delete('APP'))
    print()

    # 13. 在组中设置变量
    print("13. 在组中设置变量...")
    print(manager.set_grouped('dev', 'DATABASE_URL', 'localhost:5432'))
    print(manager.set_grouped('dev', 'API_KEY', 'dev_key_123'))
    print(manager.set_grouped('prod', 'DATABASE_URL', 'prod.example.com:5432'))
    print(manager.set_grouped('prod', 'API_KEY', 'prod_key_456'))
    print()

    # 14. 从组中获取变量
    print("14. 从组中获取变量...")
    try:
        dev_db = manager.get_grouped('dev', 'DATABASE_URL')
        print(f"开发数据库URL: {dev_db}")
    except EVMError as e:
        print(f"错误: {e}")
    print()

    # 15. 按组列出变量
    print("15. 列出 'dev' 组中的变量...")
    print_vars_table(manager.list_vars(group='dev'))
    print()

    # 16. 列出所有组
    print("16. 列出所有组...")
    print_groups(manager.list_groups())
    print()

    # 17. 按命名空间分组列出变量
    print("17. 按命名空间分组列出所有变量...")
    print_vars_by_group(manager.list_vars())
    print()

    # 18. 将变量移动到组
    print("18. 将变量移动到组...")
    print(manager.move_to_group('APP_NAME', 'prod'))
    print()

    # 19. 从组中删除变量
    print("19. 从组中删除变量...")
    print(manager.delete_grouped('dev', 'API_KEY'))
    print()

    # 20. 删除整个组
    print("20. 删除整个组...")
    print(manager.delete_group('dev'))
    print()

    # 21. 从备份恢复
    print("21. 从备份恢复...")
    print(manager.restore('output/backup.json', merge=True))
    print()

    # 22. 查看工具信息
    print("22. 查看工具信息...")
    from evm.formatters import print_info
    print_info(manager.info())
    print()

    # 23. 清空所有变量
    print("23. 清空所有变量...")
    print(manager.clear())
    print()

    print("=== 演示完成 ===")


if __name__ == '__main__':
    os.makedirs('output', exist_ok=True)
    main()
