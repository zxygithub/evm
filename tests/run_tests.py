#!/usr/bin/env python3
"""
Test runner for EVM test case files.
This script helps test EVM with the sample configuration files.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print description."""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"命令: {cmd}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"错误: {result.stderr}", file=sys.stderr)
    return result.returncode == 0


def main():
    """Run test cases."""
    test_case_dir = Path(__file__).parent / "test_case"

    if not test_case_dir.exists():
        print(f"错误: 测试目录不存在: {test_case_dir}")
        sys.exit(1)

    print("EVM 测试文件演示")
    print(f"测试文件目录: {test_case_dir}")

    # 测试1：清空环境
    run_command("evm clear", "清空所有环境变量")

    # 测试2：导入 JSON 配置
    json_file = test_case_dir / "test_config.json"
    if json_file.exists():
        run_command(f"evm load {json_file}", f"导入 JSON 配置文件")
    else:
        print(f"警告: {json_file} 不存在")

    # 测试3：查看导入的变量
    run_command("evm list", "查看所有环境变量")

    # 测试4：导入 .env 文件（替换模式）
    env_file = test_case_dir / "test_config.env"
    if env_file.exists():
        run_command(f"evm load {env_file} --replace", f"导入 .env 文件（替换模式）")
    else:
        print(f"警告: {env_file} 不存在")

    # 测试5：清空并导入多环境配置
    run_command("evm clear", "清空环境")

    # 开发环境
    dev_file = test_case_dir / "dev_config.json"
    if dev_file.exists():
        run_command(f"evm load {dev_file} --group dev", "导入开发环境配置")
    else:
        print(f"警告: {dev_file} 不存在")

    # 生产环境
    prod_file = test_case_dir / "prod_config.json"
    if prod_file.exists():
        run_command(f"evm load {prod_file} --group prod", "导入生产环境配置")
    else:
        print(f"警告: {prod_file} 不存在")

    # 测试环境
    test_env_file = test_case_dir / "test_config.json"
    if test_env_file.exists():
        run_command(f"evm load {test_env_file} --group test", "导入测试环境配置")
    else:
        print(f"警告: {test_env_file} 不存在")

    # 测试6：查看分组
    run_command("evm list --show-groups", "查看所有分组")

    # 测试7：导入备份文件
    backup_file = test_case_dir / "test_backup.json"
    if backup_file.exists():
        run_command(f"evm load {backup_file} --format backup", "导入备份文件")
    else:
        print(f"警告: {backup_file} 不存在")

    # 测试8：最终统计
    run_command("evm groups", "列出所有分组")

    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    print("\n提示：使用 'evm clear' 清空所有变量")


if __name__ == '__main__':
    main()
