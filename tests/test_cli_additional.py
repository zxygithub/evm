#!/usr/bin/env python3
"""
补充 cli.py 的测试用例，提高覆盖率
"""

import os
import tempfile

from evm.cli import main


class TestCLIAdditionalCommands:
    """测试 CLI 额外命令以提高覆盖率"""

    def test_info_command(self, capsys):
        """测试 info 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main(['--env-file', env_file, 'info'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'EVM (Environment Variable Manager)' in captured.out
            assert 'Version:' in captured.out

    def test_info_command_json(self, capsys):
        """测试 info 命令 JSON 输出"""
        import json
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main(['--env-file', env_file, 'info', '--json'])
            assert exit_code == 0
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data['status'] == 'ok'
            assert 'version' in data['data']

    def test_groups_command_empty(self, capsys):
        """测试空分组列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main(['--env-file', env_file, 'groups'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'No groups found' in captured.out

    def test_groups_command_with_groups(self, capsys):
        """测试有分组的列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            # 设置一些分组变量
            main(['--env-file', env_file, 'setg', 'dev', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'setg', 'prod', 'KEY2', 'val2'])

            exit_code = main(['--env-file', env_file, 'groups'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'dev' in captured.out
            assert 'prod' in captured.out

    def test_setg_command(self, capsys):
        """测试 setg 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main(['--env-file', env_file, 'setg', 'dev', 'API_KEY', 'dev-key'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Set: [dev]API_KEY' in captured.out

    def test_getg_command(self, capsys):
        """测试 getg 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'setg', 'dev', 'API_KEY', 'dev-key'])

            exit_code = main(['--env-file', env_file, 'getg', 'dev', 'API_KEY'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'dev-key' in captured.out

    def test_getg_command_not_found(self):
        """测试 getg 命令变量不存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main(['--env-file', env_file, 'getg', 'dev', 'NONEXISTENT'])
            assert exit_code == 2  # KeyNotFoundError

    def test_deleteg_command(self, capsys):
        """测试 deleteg 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'setg', 'dev', 'API_KEY', 'dev-key'])

            exit_code = main(['--env-file', env_file, 'deleteg', 'dev', 'API_KEY'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Deleted: [dev]API_KEY' in captured.out

    def test_listg_command(self, capsys):
        """测试 listg 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'setg', 'dev', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'setg', 'dev', 'KEY2', 'val2'])

            exit_code = main(['--env-file', env_file, 'listg', 'dev'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'KEY1' in captured.out
            assert 'KEY2' in captured.out

    def test_move_group_command(self, capsys):
        """测试 move-group 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'API_KEY', 'key'])

            exit_code = main(['--env-file', env_file, 'move-group', 'API_KEY', 'dev'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Moved: API_KEY -> dev:API_KEY' in captured.out

    def test_search_command(self, capsys):
        """测试 search 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'API_KEY', 'key1'])
            main(['--env-file', env_file, 'set', 'API_SECRET', 'key2'])

            exit_code = main(['--env-file', env_file, 'search', 'API'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'API_KEY' in captured.out
            assert 'API_SECRET' in captured.out

    def test_rename_command(self, capsys):
        """测试 rename 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'OLD_KEY', 'value'])

            exit_code = main(['--env-file', env_file, 'rename', 'OLD_KEY', 'NEW_KEY'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Renamed: OLD_KEY -> NEW_KEY' in captured.out

    def test_copy_command(self, capsys):
        """测试 copy 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'SOURCE', 'value'])

            exit_code = main(['--env-file', env_file, 'copy', 'SOURCE', 'DEST'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Copied: SOURCE -> DEST' in captured.out

    def test_expand_command(self, capsys):
        """测试 expand 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'HOST', 'localhost'])
            main(['--env-file', env_file, 'set', 'URL', 'http://{{HOST}}:8080'])

            exit_code = main(['--env-file', env_file, 'expand', 'URL'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'http://localhost:8080' in captured.out

    def test_expand_command_no_template(self, capsys):
        """测试 expand 命令无模板"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'PLAIN', 'value'])

            exit_code = main(['--env-file', env_file, 'expand', 'PLAIN'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'value' in captured.out

    def test_history_command_empty(self, capsys):
        """测试空历史"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main(['--env-file', env_file, 'history'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'No history entries found' in captured.out

    def test_history_command_with_entries(self, capsys):
        """测试有历史条目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            # 创建一些历史
            main(['--env-file', env_file, 'set', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'set', 'KEY2', 'val2'])

            exit_code = main(['--env-file', env_file, 'history'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Operation History' in captured.out

    def test_history_clear_command(self, capsys):
        """测试清空历史"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'KEY', 'val'])

            exit_code = main(['--env-file', env_file, 'history', '--clear'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'History cleared' in captured.out

    def test_completion_bash(self, capsys):
        """测试 bash 补全生成"""
        exit_code = main(['completion', 'bash'])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert '_evm_completions()' in captured.out
        assert 'complete -F _evm_completions evm' in captured.out

    def test_completion_zsh(self, capsys):
        """测试 zsh 补全生成"""
        exit_code = main(['completion', 'zsh'])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert '#compdef evm' in captured.out

    def test_completion_fish(self, capsys):
        """测试 fish 补全生成"""
        exit_code = main(['completion', 'fish'])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert 'complete -c evm' in captured.out

    def test_completion_invalid_shell(self):
        """测试无效 shell"""
        import pytest
        # argparse 遇到无效 choices 会调用 sys.exit(2)
        with pytest.raises(SystemExit) as exc_info:
            main(['completion', 'invalid'])
        assert exc_info.value.code == 2

    def test_diff_command(self, capsys):
        """测试 diff 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            backup_file = os.path.join(tmpdir, 'backup.json')

            # 设置初始变量并备份
            main(['--env-file', env_file, 'set', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'backup', '--file', backup_file])

            # 修改变量
            main(['--env-file', env_file, 'set', 'KEY1', 'val2'])
            main(['--env-file', env_file, 'set', 'KEY2', 'val3'])

            # 比较
            exit_code = main(['--env-file', env_file, 'diff', backup_file])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Changed' in captured.out or 'Added' in captured.out

    def test_validate_command_no_schema(self, capsys):
        """测试 validate 命令无 schema"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main(['--env-file', env_file, 'validate'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'No schema definitions found' in captured.out

    def test_verbose_mode(self, capsys):
        """测试 verbose 模式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main(['--env-file', env_file, '--verbose'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'EVM (Environment Variable Manager)' in captured.out
