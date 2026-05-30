#!/usr/bin/env python3
"""
cli.py 边界测试

覆盖 _confirm、main() 异常处理器、各命令的 quiet/json/dry-run 分支、
_dispatch unknown command、_dispatch_schema 全子命令。
"""

import argparse
import json
import os
import shutil
import tempfile
from unittest.mock import patch

import pytest

from evm.cli import _confirm, _dispatch, _exit_code_for, main
from evm.exceptions import EVMError

# ── 辅助函数 ──────────────────────────────────────────────

def _setup_mgr(env_file):
    """创建并返回一个干净的 EnvironmentManager"""
    from evm.manager import EnvironmentManager
    return EnvironmentManager(env_file)


class TestConfirm:
    """_confirm: 交互式确认函数边界条件"""

    def test_non_tty_returns_false(self):
        """非 TTY 模式 → 返回 False"""
        assert _confirm("Continue?") is False

    def test_tty_with_yes(self):
        """TTY 模式 + 'y' → True"""
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = True
            with patch('builtins.input', return_value='y'):
                assert _confirm("Continue?") is True

    def test_tty_with_yes_uppercase(self):
        """TTY 模式 + 'Y' → True"""
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = True
            with patch('builtins.input', return_value='Y'):
                assert _confirm("Continue?") is True

    def test_tty_with_yes_full(self):
        """TTY 模式 + 'yes' → True"""
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = True
            with patch('builtins.input', return_value='yes'):
                assert _confirm("Continue?") is True

    def test_tty_with_no(self):
        """TTY 模式 + 'n' → False"""
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = True
            with patch('builtins.input', return_value='n'):
                assert _confirm("Continue?") is False

    def test_tty_with_empty(self):
        """TTY 模式 + 空输入 → False"""
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = True
            with patch('builtins.input', return_value=''):
                assert _confirm("Continue?") is False

    def test_tty_eof_returns_false(self):
        """TTY 模式 + EOFError → False"""
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = True
            with patch('builtins.input', side_effect=EOFError):
                assert _confirm("Continue?") is False

    def test_tty_keyboard_interrupt_returns_false(self):
        """TTY 模式 + KeyboardInterrupt → False"""
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = True
            with patch('builtins.input', side_effect=KeyboardInterrupt):
                assert _confirm("Continue?") is False


class TestMainErrorHandlers:
    """main(): 顶层异常处理器边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_no_command_shows_help(self, capsys):
        """无子命令 → 显示 help，退出码 0"""
        code = main(['--env-file', self.env_file])
        assert code == 0
        captured = capsys.readouterr()
        assert 'usage:' in captured.out.lower() or 'evm' in captured.out.lower()

    def test_verbose_mode_text(self, capsys):
        """--verbose 文本模式"""
        code = main(['--env-file', self.env_file, '-v'])
        assert code == 0
        captured = capsys.readouterr()
        assert 'EVM' in captured.out

    def test_verbose_mode_json(self, capsys):
        """--verbose --json 模式"""
        code = main(['--env-file', self.env_file, '-v', '--json'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'

    def test_evMError_returns_mapped_code(self, capsys):
        """EVMError → 映射退出码 + stderr 消息"""
        code = main(['--env-file', self.env_file, 'get', 'NONEXISTENT'])
        assert code == 2
        captured = capsys.readouterr()
        assert 'Error' in captured.err

    def test_evMError_json_mode(self, capsys):
        """EVMError + --json → JSON 错误输出"""
        code = main(['--env-file', self.env_file, '--json', 'get', 'NONEXISTENT'])
        assert code == 2
        captured = capsys.readouterr()
        data = json.loads(captured.err)
        assert data['status'] == 'error'

    def test_keyboard_interrupt_returns_1(self, capsys):
        """KeyboardInterrupt → 退出码 1"""
        with patch('evm.cli.EnvironmentManager') as mock_cls:
            mock_cls.side_effect = KeyboardInterrupt
            code = main(['--env-file', self.env_file, 'list'])
            assert code == 1
            captured = capsys.readouterr()
            assert 'cancelled' in captured.err.lower()

    def test_keyboard_interrupt_quiet_no_output(self, capsys):
        """KeyboardInterrupt + --quiet → 无输出"""
        with patch('evm.cli.EnvironmentManager') as mock_cls:
            mock_cls.side_effect = KeyboardInterrupt
            code = main(['--env-file', self.env_file, '--quiet', 'list'])
            assert code == 1
            captured = capsys.readouterr()
            assert captured.err == ''

    def test_unexpected_exception_returns_1(self, capsys):
        """非 EVM 异常 → 退出码 1 + stderr"""
        with patch('evm.cli.EnvironmentManager') as mock_cls:
            mock_cls.side_effect = RuntimeError("unexpected boom")
            code = main(['--env-file', self.env_file, 'list'])
            assert code == 1
            captured = capsys.readouterr()
            assert 'unexpected boom' in captured.err

    def test_unexpected_exception_json_mode(self, capsys):
        """非 EVM 异常 + --json → JSON stderr"""
        with patch('evm.cli.EnvironmentManager') as mock_cls:
            mock_cls.side_effect = RuntimeError("boom")
            code = main(['--env-file', self.env_file, '--json', 'list'])
            assert code == 1
            captured = capsys.readouterr()
            data = json.loads(captured.err)
            assert data['status'] == 'error'
            assert 'boom' in data['error']


class TestExitCodeFor:
    """_exit_code_for: 异常类型到退出码的映射"""

    def test_unknown_evMError_returns_1(self):
        """未映射的 EVMError 子类 → 1"""
        class CustomError(EVMError):
            pass
        assert _exit_code_for(CustomError("test")) == 1

    def test_mapped_error_returns_correct_code(self):
        """映射的异常类型 → 正确退出码"""
        from evm.exceptions import KeyNotFoundError, StorageError
        assert _exit_code_for(KeyNotFoundError("X")) == 2
        assert _exit_code_for(StorageError("X")) == 3


class TestCmdClearBoundaries:
    """_cmd_clear: clear 命令边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_clear_empty_vars_no_confirm(self, capsys):
        """清空空存储 → 不需要确认"""
        code = main(['--env-file', self.env_file, 'clear'])
        assert code == 0

    def test_clear_dry_run(self, capsys):
        """--dry-run clear"""
        main(['--env-file', self.env_file, 'set', 'A', '1'])
        capsys.readouterr()  # 清除 set 输出
        code = main(['--env-file', self.env_file, 'clear', '--dry-run'])
        assert code == 0
        captured = capsys.readouterr()
        assert 'DRY-RUN' in captured.out

    def test_clear_force_json(self, capsys):
        """--force --json clear"""
        main(['--env-file', self.env_file, 'set', 'A', '1'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', '--force', 'clear'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['data']['cleared'] == 1

    def test_clear_quiet_mode(self, capsys):
        """--quiet --force clear → 无输出"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'A', '1'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', '--force', 'clear'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''


class TestCmdSetBoundaries:
    """_cmd_set: set 命令 quiet 模式"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_set_quiet(self, capsys):
        """set --quiet → 无输出"""
        code = main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'V'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''

    def test_set_secret_quiet(self, capsys):
        """set --secret --quiet → 无输出"""
        code = main(['--env-file', self.env_file, '--quiet', 'set', '--secret', 'K', 'V'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''


class TestCmdGetBoundaries:
    """_cmd_get: get 命令 quiet 模式"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_get_quiet(self, capsys):
        """get --quiet → 无输出"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', 'get', 'K'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''


class TestCmdGroupBoundaries:
    """分组命令边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_deleteg_quiet(self, capsys):
        """deleteg --quiet → 无输出"""
        main(['--env-file', self.env_file, '--quiet', 'setg', 'dev', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', 'deleteg', 'dev', 'K'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''

    def test_listg_no_prefix_json(self, capsys):
        """listg --no-prefix --json"""
        main(['--env-file', self.env_file, '--quiet', 'setg', 'dev', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', 'listg', 'dev', '--no-prefix'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'
        assert 'K' in data['data']

    def test_listg_quiet(self, capsys):
        """listg --quiet → 无输出"""
        main(['--env-file', self.env_file, '--quiet', 'setg', 'dev', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', 'listg', 'dev'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''

    def test_delete_group_force_json(self, capsys):
        """delete-group --force --json"""
        main(['--env-file', self.env_file, '--quiet', 'setg', 'dev', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', '--force', 'delete-group', 'dev'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['data']['deleted'] is True

    def test_delete_group_dry_run(self, capsys):
        """delete-group --dry-run"""
        main(['--env-file', self.env_file, '--quiet', 'setg', 'dev', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, 'delete-group', 'dev', '--dry-run'])
        assert code == 0
        captured = capsys.readouterr()
        assert 'DRY-RUN' in captured.out

    def test_delete_group_quiet(self, capsys):
        """delete-group --force --quiet → 无输出"""
        main(['--env-file', self.env_file, '--quiet', 'setg', 'dev', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', '--force', 'delete-group', 'dev'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''


class TestCmdRestoreBoundaries:
    """restore 命令边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_restore_json_mode(self, capsys):
        """restore --json"""
        backup_path = os.path.join(self.temp_dir, 'backup.json')
        with open(backup_path, 'w') as f:
            json.dump({'timestamp': '2026-01-01', 'variables': {'K': 'V'}}, f)

        code = main(['--env-file', self.env_file, '--json', 'restore', backup_path])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'

    def test_restore_merge_flag(self, capsys):
        """restore --merge"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'EXISTING', 'old'])
        capsys.readouterr()
        backup_path = os.path.join(self.temp_dir, 'merge.json')
        with open(backup_path, 'w') as f:
            json.dump({'variables': {'NEW': 'val'}}, f)

        code = main(['--env-file', self.env_file, 'restore', backup_path, '--merge'])
        assert code == 0
        captured = capsys.readouterr()
        assert 'Merged' in captured.out

    def test_restore_quiet(self, capsys):
        """restore --quiet → 无输出"""
        backup_path = os.path.join(self.temp_dir, 'backup.json')
        with open(backup_path, 'w') as f:
            json.dump({'variables': {'K': 'V'}}, f)

        code = main(['--env-file', self.env_file, '--quiet', 'restore', backup_path])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''


class TestCmdHistoryBoundaries:
    """history 命令边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_history_clear_json(self, capsys):
        """history --clear --json"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', 'history', '--clear'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'

    def test_history_clear_quiet(self, capsys):
        """history --clear --quiet"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', 'history', '--clear'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''

    def test_history_json_mode(self, capsys):
        """history --json"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', 'history'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'
        assert isinstance(data['data'], list)

    def test_history_quiet(self, capsys):
        """history --quiet → 无输出"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', 'history'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''


class TestCmdLoadmemoryBoundaries:
    """loadmemory 命令边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_loadmemory_quiet(self, capsys):
        """loadmemory --quiet → 无输出"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', 'loadmemory'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''

    def test_loadmemory_json(self, capsys):
        """loadmemory --json"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', 'loadmemory'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'
        assert data['data']['loaded'] >= 1


class TestCmdEditBoundaries:
    """edit 命令边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_edit_json_mode(self, capsys):
        """edit --json → 结构化输出"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'original'])
        capsys.readouterr()
        with patch('evm.manager.subprocess.run') as mock_run:
            mock_run.return_value = type('Result', (), {'returncode': 0})()
            code = main(['--env-file', self.env_file, '--json', 'edit', 'K'])
            assert code == 0
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data['status'] == 'ok'
            assert 'key' in data['data']


class TestSchemaDispatch:
    """_dispatch_schema: schema 子命令全路径"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_schema_set_json(self, capsys):
        """schema set --json"""
        code = main(['--env-file', self.env_file, '--json', 'schema', 'set', 'API_URL', '--format', 'url'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'

    def test_schema_set_quiet(self, capsys):
        """schema set --quiet"""
        code = main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'KEY', '--format', 'integer'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''

    def test_schema_set_with_required(self, capsys):
        """schema set --required"""
        code = main(['--env-file', self.env_file, '--json', 'schema', 'set', 'KEY', '--required'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'

    def test_schema_get_key_json(self, capsys):
        """schema get KEY --json"""
        main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'KEY', '--format', 'port'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', 'schema', 'get', 'KEY'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'

    def test_schema_get_all_quiet(self, capsys):
        """schema get (all) --quiet"""
        code = main(['--env-file', self.env_file, '--quiet', 'schema', 'get'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''

    def test_schema_delete_json(self, capsys):
        """schema delete --json"""
        main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'KEY', '--format', 'url'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', 'schema', 'delete', 'KEY'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'

    def test_schema_delete_quiet(self, capsys):
        """schema delete --quiet"""
        main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'KEY', '--format', 'url'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', 'schema', 'delete', 'KEY'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''

    def test_schema_list_json(self, capsys):
        """schema list --json"""
        main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'KEY', '--format', 'url'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', 'schema', 'list'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'

    def test_schema_list_quiet(self, capsys):
        """schema list --quiet"""
        code = main(['--env-file', self.env_file, '--quiet', 'schema', 'list'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''

    def test_schema_validate_key_json(self, capsys):
        """schema validate KEY --json"""
        main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'PORT', '--format', 'port'])
        main(['--env-file', self.env_file, '--quiet', 'set', 'PORT', '8080'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', 'schema', 'validate', 'PORT'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'

    def test_schema_validate_all_json(self, capsys):
        """schema validate (all) --json"""
        main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'PORT', '--format', 'port'])
        main(['--env-file', self.env_file, '--quiet', 'set', 'PORT', '8080'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', 'schema', 'validate'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'

    def test_schema_validate_all_quiet(self, capsys):
        """schema validate (all) --quiet"""
        main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'PORT', '--format', 'port'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', 'schema', 'validate'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''

    def test_schema_no_subcommand_json(self, capsys):
        """schema (no subcommand) --json → 显示全部 schema"""
        main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'K', '--format', 'url'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', 'schema'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'

    def test_schema_no_subcommand_quiet(self, capsys):
        """schema (no subcommand) --quiet"""
        code = main(['--env-file', self.env_file, '--quiet', 'schema'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''


class TestDispatchUnknownCommand:
    """_dispatch: 未知命令"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_unknown_command_raises(self):
        """未知命令 → EVMError"""
        from evm.manager import EnvironmentManager
        mgr = EnvironmentManager(self.env_file)
        args = argparse.Namespace(command='nonexistent_command')
        with pytest.raises(EVMError, match='Unknown command'):
            _dispatch(mgr, args, False, False, False, False)


class TestCmdValidateBoundaries:
    """validate 命令边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_validate_all_quiet(self, capsys):
        """validate (all) --quiet → 无输出"""
        main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'PORT', '--format', 'port'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', 'validate'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''


class TestCmdDiffBoundaries:
    """diff 命令边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_diff_quiet(self, capsys):
        """diff --quiet → 无输出"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'V'])
        capsys.readouterr()
        backup_path = os.path.join(self.temp_dir, 'backup.json')
        with open(backup_path, 'w') as f:
            json.dump({'K': 'V'}, f)
        code = main(['--env-file', self.env_file, '--quiet', 'diff', backup_path])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''


class TestCmdSearchBoundaries:
    """search 命令边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_search_value_quiet(self, capsys):
        """search --value --quiet → 无输出"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', 'search', 'K', '--value'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''


class TestCmdExpandBoundaries:
    """expand 命令边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_expand_quiet(self, capsys):
        """expand --quiet → 无输出"""
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'val'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--quiet', 'expand', 'K'])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out == ''
