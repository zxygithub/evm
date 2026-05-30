#!/usr/bin/env python3
"""
补充 CLI 测试以提高覆盖率

这个文件专注于覆盖 cli.py 中缺失的代码路径。
"""

import json
import os
import tempfile

from evm.cli import main


class TestCLIExec:
    """测试 exec 命令"""

    def test_exec_simple_command(self, capsys):
        """测试执行简单命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'TEST_VAR', 'test_value'])
            capsys.readouterr()  # 清理输出

            exit_code = main([
                '--env-file', env_file,
                'exec', '--', 'echo', 'hello'
            ])
            assert exit_code == 0

    def test_exec_command_with_env(self, capsys):
        """测试执行命令时使用环境变量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'MY_VAR', 'my_value'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file,
                'exec', '--', 'python', '-c',
                'import os; print(os.environ.get("MY_VAR"))'
            ])
            assert exit_code == 0

    def test_exec_command_failure(self, capsys):
        """测试执行失败的命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'KEY', 'val'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file,
                'exec', '--', 'python', '-c', 'exit(42)'
            ])
            assert exit_code == 42

    def test_exec_command_not_found(self, capsys):
        """测试执行不存在的命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'KEY', 'val'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file,
                'exec', '--', 'nonexistent_command_xyz123'
            ])
            # CommandNotFoundError 应该返回退出码 10
            assert exit_code == 10


class TestCLIListAdvanced:
    """测试 list 命令的高级选项"""

    def test_list_show_groups(self, capsys):
        """测试 --show-groups 选项"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'setg', 'dev', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'setg', 'prod', 'KEY2', 'val2'])
            capsys.readouterr()

            exit_code = main(['--env-file', env_file, 'list', '--show-groups'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert '[dev]' in captured.out
            assert '[prod]' in captured.out

    def test_list_show_groups_json(self, capsys):
        """测试 --show-groups 与 --json"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'setg', 'dev', 'KEY1', 'val1'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file, 'list', '--show-groups', '--json'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data['status'] == 'ok'

    def test_list_show_groups_with_group_filter(self, capsys):
        """测试 --show-groups 与 --group"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'setg', 'dev', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'setg', 'prod', 'KEY2', 'val2'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file, 'list', '--show-groups', '--group', 'dev'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'KEY1' in captured.out
            assert 'KEY2' not in captured.out

    def test_list_show_groups_with_pattern(self, capsys):
        """测试 --show-groups 与 pattern"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'API_KEY', 'key1'])
            main(['--env-file', env_file, 'set', 'DB_HOST', 'host1'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file, 'list', '--show-groups', 'API'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'API_KEY' in captured.out
            assert 'DB_HOST' not in captured.out

    def test_list_no_prefix(self, capsys):
        """测试 --no-prefix 选项"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'setg', 'dev', 'KEY1', 'val1'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file, 'listg', 'dev', '--no-prefix'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            # 应该显示 KEY1 而不是 dev:KEY1
            assert 'KEY1' in captured.out


class TestCLIExportAdvanced:
    """测试 export 命令的高级选项"""

    def test_export_with_group(self, capsys):
        """测试导出特定分组"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'setg', 'dev', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'setg', 'prod', 'KEY2', 'val2'])
            capsys.readouterr()

            output_file = os.path.join(tmpdir, 'export.json')
            exit_code = main([
                '--env-file', env_file,
                'export', '--group', 'dev', '--output', output_file
            ])
            assert exit_code == 0

            with open(output_file) as f:
                data = json.load(f)
            assert 'dev:KEY1' in data
            assert 'prod:KEY2' not in data

    def test_export_sh_format(self, capsys):
        """测试导出为 shell 格式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'API_KEY', 'secret123'])
            capsys.readouterr()

            output_file = os.path.join(tmpdir, 'export.sh')
            exit_code = main([
                '--env-file', env_file,
                'export', '--format', 'sh', '--output', output_file
            ])
            assert exit_code == 0

            with open(output_file) as f:
                content = f.read()
            assert 'export API_KEY=' in content

    def test_export_env_format(self, capsys):
        """测试导出为 .env 格式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'DB_HOST', 'localhost'])
            capsys.readouterr()

            output_file = os.path.join(tmpdir, 'export.env')
            exit_code = main([
                '--env-file', env_file,
                'export', '--format', 'env', '--output', output_file
            ])
            assert exit_code == 0

            with open(output_file) as f:
                content = f.read()
            assert 'DB_HOST=localhost' in content


class TestCLILoadAdvanced:
    """测试 load 命令的高级选项"""

    def test_load_with_group(self, capsys):
        """测试加载到特定分组"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            input_file = os.path.join(tmpdir, 'input.json')

            with open(input_file, 'w') as f:
                json.dump({'KEY1': 'val1', 'KEY2': 'val2'}, f)

            exit_code = main([
                '--env-file', env_file,
                'load', input_file, '--group', 'dev'
            ])
            assert exit_code == 0

            # 验证变量被添加到 dev 分组
            exit_code = main(['--env-file', env_file, 'get', 'dev:KEY1'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'val1' in captured.out

    def test_load_with_replace(self, capsys):
        """测试替换模式加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            input_file = os.path.join(tmpdir, 'input.json')

            # 先设置一些变量
            main(['--env-file', env_file, 'set', 'OLD_KEY', 'old_val'])
            capsys.readouterr()

            # 准备新配置
            with open(input_file, 'w') as f:
                json.dump({'NEW_KEY': 'new_val'}, f)

            # 使用替换模式加载
            exit_code = main([
                '--env-file', env_file,
                'load', input_file, '--replace'
            ])
            assert exit_code == 0

            # 验证旧变量被删除，新变量存在
            exit_code = main(['--env-file', env_file, 'get', 'OLD_KEY'])
            assert exit_code == 2  # KeyNotFoundError

            exit_code = main(['--env-file', env_file, 'get', 'NEW_KEY'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'new_val' in captured.out

    def test_load_with_nest(self, capsys):
        """测试嵌套 JSON 加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            input_file = os.path.join(tmpdir, 'nested.json')

            # 准备嵌套配置
            with open(input_file, 'w') as f:
                json.dump({
                    'dev': {'KEY1': 'val1'},
                    'prod': {'KEY2': 'val2'}
                }, f)

            exit_code = main([
                '--env-file', env_file,
                'load', input_file, '--nest'
            ])
            assert exit_code == 0

            # 验证变量被正确分组
            exit_code = main(['--env-file', env_file, 'get', 'dev:KEY1'])
            assert exit_code == 0

            exit_code = main(['--env-file', env_file, 'get', 'prod:KEY2'])
            assert exit_code == 0


class TestCLISchemaAdvanced:
    """测试 schema 子命令"""

    def test_schema_get_all(self, capsys):
        """测试获取所有 schema"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main([
                '--env-file', env_file,
                'schema', 'set', 'API_URL', '--format', 'url'
            ])
            main([
                '--env-file', env_file,
                'schema', 'set', 'DB_PORT', '--format', 'port'
            ])
            capsys.readouterr()

            exit_code = main(['--env-file', env_file, 'schema', 'get'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'API_URL' in captured.out
            assert 'DB_PORT' in captured.out

    def test_schema_get_specific(self, capsys):
        """测试获取特定 schema"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main([
                '--env-file', env_file,
                'schema', 'set', 'API_URL', '--format', 'url', '--required'
            ])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file, 'schema', 'get', 'API_URL'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'API_URL' in captured.out
            assert 'url' in captured.out

    def test_schema_delete(self, capsys):
        """测试删除 schema"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main([
                '--env-file', env_file,
                'schema', 'set', 'API_URL', '--format', 'url'
            ])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file, 'schema', 'delete', 'API_URL'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Schema removed' in captured.out

    def test_schema_list(self, capsys):
        """测试列出所有 schema"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main([
                '--env-file', env_file,
                'schema', 'set', 'KEY1', '--format', 'url'
            ])
            main([
                '--env-file', env_file,
                'schema', 'set', 'KEY2', '--format', 'email'
            ])
            capsys.readouterr()

            exit_code = main(['--env-file', env_file, 'schema', 'list'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'KEY1' in captured.out
            assert 'KEY2' in captured.out

    def test_schema_validate_single(self, capsys):
        """测试验证单个变量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main([
                '--env-file', env_file,
                'schema', 'set', 'API_URL', '--format', 'url'
            ])
            main([
                '--env-file', env_file,
                'set', 'API_URL', 'https://api.example.com'
            ])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file, 'schema', 'validate', 'API_URL'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'valid' in captured.out.lower()

    def test_schema_validate_all(self, capsys):
        """测试验证所有变量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main([
                '--env-file', env_file,
                'schema', 'set', 'API_URL', '--format', 'url'
            ])
            main([
                '--env-file', env_file,
                'schema', 'set', 'DB_PORT', '--format', 'port'
            ])
            main([
                '--env-file', env_file,
                'set', 'API_URL', 'https://api.example.com'
            ])
            main([
                '--env-file', env_file,
                'set', 'DB_PORT', '5432'
            ])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file, 'schema', 'validate'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'API_URL' in captured.out
            assert 'DB_PORT' in captured.out

    def test_schema_set_with_pattern(self, capsys):
        """测试设置带正则表达式的 schema"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main([
                '--env-file', env_file,
                'schema', 'set', 'API_KEY',
                '--pattern', r'^[a-zA-Z0-9]{32}$'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'API_KEY' in captured.out

    def test_schema_set_with_description(self, capsys):
        """测试设置带描述的 schema"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            exit_code = main([
                '--env-file', env_file,
                'schema', 'set', 'API_URL',
                '--format', 'url',
                '--description', 'API endpoint URL'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'API_URL' in captured.out


class TestCLIValidateAdvanced:
    """测试 validate 命令"""

    def test_validate_single_key(self, capsys):
        """测试验证单个变量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main([
                '--env-file', env_file,
                'schema', 'set', 'API_URL', '--format', 'url'
            ])
            main([
                '--env-file', env_file,
                'set', 'API_URL', 'https://api.example.com'
            ])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file, 'validate', 'API_URL'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'valid' in captured.out.lower()

    def test_validate_single_key_json(self, capsys):
        """测试验证单个变量（JSON 输出）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main([
                '--env-file', env_file,
                'schema', 'set', 'API_URL', '--format', 'url'
            ])
            main([
                '--env-file', env_file,
                'set', 'API_URL', 'https://api.example.com'
            ])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file, 'validate', 'API_URL', '--json'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data['status'] == 'ok'
            assert data['data']['valid'] is True

    def test_validate_all(self, capsys):
        """测试验证所有变量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main([
                '--env-file', env_file,
                'schema', 'set', 'KEY1', '--format', 'url'
            ])
            main([
                '--env-file', env_file,
                'set', 'KEY1', 'https://example.com'
            ])
            capsys.readouterr()

            exit_code = main(['--env-file', env_file, 'validate'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'KEY1' in captured.out


class TestCLIHistoryAdvanced:
    """测试 history 命令"""

    def test_history_json(self, capsys):
        """测试历史记录 JSON 输出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'set', 'KEY2', 'val2'])
            capsys.readouterr()

            exit_code = main(['--env-file', env_file, 'history', '--json'])
            assert exit_code == 0
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data['status'] == 'ok'
            assert isinstance(data['data'], list)
            assert len(data['data']) >= 2

    def test_history_with_limit(self, capsys):
        """测试限制历史记录数量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            for i in range(10):
                main(['--env-file', env_file, 'set', f'KEY{i}', f'val{i}'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file, 'history', '--limit', '5'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            # 应该只显示最近 5 条记录
            assert 'Operation History' in captured.out


class TestCLIBackupRestore:
    """测试 backup 和 restore 命令"""

    def test_backup_and_restore(self, capsys):
        """测试备份和恢复"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            backup_file = os.path.join(tmpdir, 'backup.json')

            # 设置一些变量
            main(['--env-file', env_file, 'set', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'set', 'KEY2', 'val2'])
            capsys.readouterr()

            # 创建备份
            exit_code = main([
                '--env-file', env_file,
                'backup', '--file', backup_file
            ])
            assert exit_code == 0
            assert os.path.exists(backup_file)

            # 修改变量
            main(['--env-file', env_file, 'set', 'KEY1', 'new_val'])
            main(['--env-file', env_file, 'delete', 'KEY2'])
            capsys.readouterr()

            # 恢复备份
            exit_code = main([
                '--env-file', env_file,
                'restore', backup_file
            ])
            assert exit_code == 0

            # 验证恢复成功
            exit_code = main(['--env-file', env_file, 'get', 'KEY1'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'val1' in captured.out

            exit_code = main(['--env-file', env_file, 'get', 'KEY2'])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'val2' in captured.out

    def test_restore_with_merge(self, capsys):
        """测试合并模式恢复"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            backup_file = os.path.join(tmpdir, 'backup.json')

            # 设置一些变量并备份
            main(['--env-file', env_file, 'set', 'KEY1', 'val1'])
            capsys.readouterr()

            main(['--env-file', env_file, 'backup', '--file', backup_file])
            capsys.readouterr()

            # 添加新变量
            main(['--env-file', env_file, 'set', 'KEY2', 'val2'])
            capsys.readouterr()

            # 合并模式恢复
            exit_code = main([
                '--env-file', env_file,
                'restore', backup_file, '--merge'
            ])
            assert exit_code == 0

            # 验证两个变量都存在
            exit_code = main(['--env-file', env_file, 'get', 'KEY1'])
            assert exit_code == 0

            exit_code = main(['--env-file', env_file, 'get', 'KEY2'])
            assert exit_code == 0


class TestCLIDiff:
    """测试 diff 命令"""

    def test_diff_with_changes(self, capsys):
        """测试有变化的 diff"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            backup_file = os.path.join(tmpdir, 'backup.json')

            # 设置初始变量并备份
            main(['--env-file', env_file, 'set', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'backup', '--file', backup_file])
            capsys.readouterr()

            # 修改变量
            main(['--env-file', env_file, 'set', 'KEY1', 'new_val'])
            main(['--env-file', env_file, 'set', 'KEY2', 'val2'])
            capsys.readouterr()

            # 比较差异
            exit_code = main([
                '--env-file', env_file,
                'diff', backup_file
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Changed' in captured.out or 'Added' in captured.out

    def test_diff_json(self, capsys):
        """测试 JSON 格式的 diff"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            backup_file = os.path.join(tmpdir, 'backup.json')

            main(['--env-file', env_file, 'set', 'KEY1', 'val1'])
            main(['--env-file', env_file, 'backup', '--file', backup_file])
            main(['--env-file', env_file, 'set', 'KEY1', 'new_val'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file,
                'diff', backup_file, '--json'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert data['status'] == 'ok'
            assert 'added' in data['data'] or 'changed' in data['data']


class TestCLICopyRename:
    """测试 copy 和 rename 命令"""

    def test_copy_command(self, capsys):
        """测试 copy 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'SOURCE', 'value'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file,
                'copy', 'SOURCE', 'DEST'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Copied: SOURCE -> DEST' in captured.out

            # 验证两个变量都存在
            exit_code = main(['--env-file', env_file, 'get', 'SOURCE'])
            assert exit_code == 0

            exit_code = main(['--env-file', env_file, 'get', 'DEST'])
            assert exit_code == 0

    def test_rename_command(self, capsys):
        """测试 rename 命令"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'OLD_NAME', 'value'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file,
                'rename', 'OLD_NAME', 'NEW_NAME'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'Renamed: OLD_NAME -> NEW_NAME' in captured.out

            # 验证旧变量不存在，新变量存在
            exit_code = main(['--env-file', env_file, 'get', 'OLD_NAME'])
            assert exit_code == 2  # KeyNotFoundError

            exit_code = main(['--env-file', env_file, 'get', 'NEW_NAME'])
            assert exit_code == 0


class TestCLISearch:
    """测试 search 命令"""

    def test_search_by_key(self, capsys):
        """测试按键名搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'API_KEY', 'key1'])
            main(['--env-file', env_file, 'set', 'API_SECRET', 'key2'])
            main(['--env-file', env_file, 'set', 'DB_HOST', 'host'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file,
                'search', 'API'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'API_KEY' in captured.out
            assert 'API_SECRET' in captured.out
            assert 'DB_HOST' not in captured.out

    def test_search_by_value(self, capsys):
        """测试按值搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'KEY1', 'secret123'])
            main(['--env-file', env_file, 'set', 'KEY2', 'password456'])
            main(['--env-file', env_file, 'set', 'KEY3', 'other'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file,
                'search', 'secret', '--value'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'KEY1' in captured.out
            assert 'KEY2' not in captured.out
            assert 'KEY3' not in captured.out


class TestCLIExpand:
    """测试 expand 命令"""

    def test_expand_with_template(self, capsys):
        """测试模板展开"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'HOST', 'localhost'])
            main(['--env-file', env_file, 'set', 'PORT', '8080'])
            main(['--env-file', env_file, 'set', 'URL', 'http://{{HOST}}:{{PORT}}'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file,
                'expand', 'URL'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'http://localhost:8080' in captured.out

    def test_expand_no_template(self, capsys):
        """测试无模板的展开"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'test_env.json')
            main(['--env-file', env_file, 'set', 'PLAIN', 'plain_value'])
            capsys.readouterr()

            exit_code = main([
                '--env-file', env_file,
                'expand', 'PLAIN'
            ])
            assert exit_code == 0
            captured = capsys.readouterr()
            assert 'plain_value' in captured.out
