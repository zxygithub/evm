#!/usr/bin/env python3
"""
测试 __main__.py 模块

这些测试直接导入并运行 __main__.py 的代码以提高覆盖率。
注意：实际使用 `python -m evm` 的测试在 test_main_entry.py 中。
"""

import os
import tempfile

import pytest


class TestMainModule:
    """测试 __main__.py 模块的直接调用"""

    def test_main_module_import(self):
        """测试 __main__ 模块可以被导入"""
        import evm.__main__
        assert hasattr(evm.__main__, 'main')

    def test_main_module_help(self, capsys):
        """测试通过 __main__ 模块显示帮助"""
        from evm.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main(['--help'])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert 'Environment Variable Manager' in captured.out

    def test_main_module_version(self, capsys):
        """测试通过 __main__ 模块显示版本"""
        from evm.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main(['--version'])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert 'evm' in captured.out

    def test_main_module_no_args(self, capsys):
        """测试无参数时显示帮助"""
        from evm.__main__ import main

        exit_code = main([])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert 'usage:' in captured.out

    def test_main_module_list_empty(self, capsys):
        """测试通过 __main__ 模块列出空环境"""
        from evm.__main__ import main

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main(['--env-file', env_file, 'list'])

            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'No environment variables set' in captured.out

    def test_main_module_set_and_get(self, capsys):
        """测试通过 __main__ 模块设置和获取变量"""
        from evm.__main__ import main

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')

            # 设置变量
            exit_code = main(['--env-file', env_file, 'set', 'TEST_KEY', 'test_value'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Set: TEST_KEY' in captured.out

            # 获取变量
            exit_code = main(['--env-file', env_file, 'get', 'TEST_KEY'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'test_value' in captured.out

    def test_main_module_error_exit_code(self):
        """测试通过 __main__ 模块返回错误退出码"""
        from evm.__main__ import main

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')

            # 获取不存在的变量应该返回退出码 2
            exit_code = main(['--env-file', env_file, 'get', 'NONEXISTENT_KEY'])
            assert exit_code == 2

    def test_main_module_error_handling(self, capsys):
        """测试错误处理"""
        from evm.__main__ import main

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')

            # 尝试删除不存在的变量，应该返回错误码 2
            exit_code = main(['--env-file', env_file, 'delete', 'NONEXISTENT_KEY'])
            assert exit_code == 2

    def test_main_module_verbose_mode(self, capsys):
        """测试 verbose 模式"""
        from evm.__main__ import main

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main(['--env-file', env_file, '--verbose'])

            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'EVM (Environment Variable Manager)' in captured.out

    def test_main_module_json_mode(self, capsys):
        """测试 JSON 输出模式"""
        import json

        from evm.__main__ import main

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')

            # 设置变量
            main(['--env-file', env_file, 'set', 'JSON_KEY', 'json_value'])
            capsys.readouterr()  # 清理输出

            # 获取变量（JSON 格式）
            exit_code = main(['--env-file', env_file, '--json', 'get', 'JSON_KEY'])
            assert exit_code == 0

            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data['status'] == 'ok'
            assert data['data']['key'] == 'JSON_KEY'
            assert data['data']['value'] == 'json_value'

    def test_main_module_quiet_mode(self, capsys):
        """测试 quiet 模式"""
        from evm.__main__ import main

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')

            # 设置变量（quiet 模式）
            exit_code = main(['--env-file', env_file, '--quiet', 'set', 'QUIET_KEY', 'quiet_value'])
            assert exit_code == 0

            # quiet 模式应该没有输出
            captured = capsys.readouterr()
            assert captured.out.strip() == ''

    def test_main_module_dry_run_mode(self, capsys):
        """测试 dry-run 模式"""
        from evm.__main__ import main

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')

            # 设置变量（dry-run 模式）
            exit_code = main(['--env-file', env_file, '--dry-run', 'set', 'DRY_KEY', 'dry_value'])
            assert exit_code == 0

            captured = capsys.readouterr()
            assert '[DRY-RUN]' in captured.out

            # 变量不应该被实际设置
            exit_code = main(['--env-file', env_file, 'get', 'DRY_KEY'])
            assert exit_code == 2  # KeyNotFoundError

    def test_main_module_force_mode(self, capsys):
        """测试 force 模式（跳过确认）"""
        from evm.__main__ import main

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')

            # 设置一些变量
            main(['--env-file', env_file, 'set', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'set', 'KEY2', 'val2'])

            # 清空（force 模式，不提示确认）
            exit_code = main(['--env-file', env_file, '--force', 'clear'])
            assert exit_code == 0

            captured = capsys.readouterr()
            assert 'Cleared' in captured.out or 'cleared' in captured.out.lower()
