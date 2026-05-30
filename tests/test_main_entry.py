#!/usr/bin/env python3
"""
测试 __main__.py 入口点
"""

import subprocess
import sys


class TestMainEntryPoint:
    """测试 python -m evm 入口"""

    def test_module_help(self):
        """测试 python -m evm --help"""
        result = subprocess.run(
            [sys.executable, '-m', 'evm', '--help'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert 'Environment Variable Manager' in result.stdout
        assert 'usage:' in result.stdout

    def test_module_version(self):
        """测试 python -m evm --version"""
        result = subprocess.run(
            [sys.executable, '-m', 'evm', '--version'],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # 版本号格式应该是 evm X.Y.Z
        assert 'evm' in result.stdout
        # 检查版本号格式（至少有一个数字）
        import re
        assert re.search(r'\d+\.\d+\.\d+', result.stdout)

    def test_module_list_empty(self):
        """测试 python -m evm list（使用临时环境文件）"""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            result = subprocess.run(
                [sys.executable, '-m', 'evm', '--env-file', env_file, 'list'],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert 'No environment variables set' in result.stdout

    def test_module_set_and_get(self):
        """测试 python -m evm set 和 get"""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')

            # 设置变量
            result = subprocess.run(
                [sys.executable, '-m', 'evm', '--env-file', env_file,
                 'set', 'TEST_KEY', 'test_value'],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert 'Set: TEST_KEY' in result.stdout

            # 获取变量
            result = subprocess.run(
                [sys.executable, '-m', 'evm', '--env-file', env_file,
                 'get', 'TEST_KEY'],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert 'test_value' in result.stdout

    def test_module_json_output(self):
        """测试 python -m evm --json 输出"""
        import json
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')

            # 设置变量
            subprocess.run(
                [sys.executable, '-m', 'evm', '--env-file', env_file,
                 'set', 'JSON_KEY', 'json_value'],
                capture_output=True,
            )

            # 获取变量（JSON 格式）
            result = subprocess.run(
                [sys.executable, '-m', 'evm', '--env-file', env_file,
                 'get', 'JSON_KEY', '--json'],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0

            # 解析 JSON
            data = json.loads(result.stdout)
            assert data['status'] == 'ok'
            assert data['data']['key'] == 'JSON_KEY'
            assert data['data']['value'] == 'json_value'

    def test_module_error_exit_code(self):
        """测试 python -m evm 错误退出码"""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')

            # 获取不存在的变量应该返回退出码 2
            result = subprocess.run(
                [sys.executable, '-m', 'evm', '--env-file', env_file,
                 'get', 'NONEXISTENT_KEY'],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 2

    def test_module_invalid_command(self):
        """测试 python -m evm 无效命令"""
        result = subprocess.run(
            [sys.executable, '-m', 'evm', 'invalid_command'],
            capture_output=True,
            text=True,
        )
        # argparse 应该返回非零退出码
        assert result.returncode != 0

    def test_module_quiet_mode(self):
        """测试 python -m evm --quiet 模式"""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')

            # 设置变量（quiet 模式）
            result = subprocess.run(
                [sys.executable, '-m', 'evm', '--env-file', env_file,
                 'set', 'QUIET_KEY', 'quiet_value', '--quiet'],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            # quiet 模式应该没有输出
            assert result.stdout.strip() == ''
