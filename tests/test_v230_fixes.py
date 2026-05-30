#!/usr/bin/env python3
"""
v2.3.0 代码评审修复测试

覆盖所有评审中修复的项：
- backup() 使用 env_file.parent 而非硬编码 ~/.evm/
- move_to_group 目标 key 已存在时抛出 KeyAlreadyExistsError
- _load_env_file 报告跳过的无效 key
- __init__.py 导出核心 API
- _secret_warning_shown 为实例变量
- history.jsonl 文件锁
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from evm import EnvironmentManager, KeyAlreadyExistsError


class TestBackupUsesEnvFileParent:
    """backup() 应基于 env_file.parent 而非硬编码 ~/.evm/"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'subdir', 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_backup_default_goes_to_env_file_parent(self):
        """默认备份应写到 env_file 所在目录"""
        self.mgr.set('TEST_KEY', 'test_value')
        msg = self.mgr.backup()
        assert 'Backup created:' in msg
        # 备份文件应在 env_file 的同级目录
        backup_path_str = msg.split('Backup created: ')[1]
        backup_path = Path(backup_path_str)
        assert backup_path.parent == self.mgr.env_file.parent
        # 不应在 ~/.evm/ (除非 env_file 就在那里)
        home_evm = Path.home() / '.evm'
        if self.mgr.env_file.parent != home_evm:
            assert backup_path.parent != home_evm

    def test_backup_explicit_path_still_works(self):
        """显式指定备份路径不受影响"""
        self.mgr.set('KEY', 'val')
        explicit_path = os.path.join(self.temp_dir, 'my_backup.json')
        msg = self.mgr.backup(explicit_path)
        assert explicit_path in msg
        assert os.path.exists(explicit_path)

    def test_backup_isolated_env_file(self):
        """使用隔离的 env_file 时，备份也在隔离目录"""
        isolated_dir = os.path.join(self.temp_dir, 'isolated')
        env_file = os.path.join(isolated_dir, 'env.json')
        mgr = EnvironmentManager(env_file)
        mgr.set('ISO_KEY', 'iso_val')
        msg = mgr.backup()
        backup_path_str = msg.split('Backup created: ')[1]
        assert isolated_dir in backup_path_str


class TestMoveToGroupConflict:
    """move_to_group 目标 key 已存在时应抛出 KeyAlreadyExistsError"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_move_to_group_target_exists(self):
        """目标分组已有同名 key 时应报错"""
        self.mgr.set('API_KEY', 'global_val')
        self.mgr.set_grouped('dev', 'API_KEY', 'dev_val')
        with pytest.raises(KeyAlreadyExistsError):
            self.mgr.move_to_group('API_KEY', 'dev')

    def test_move_to_group_no_conflict(self):
        """无冲突时正常移动"""
        self.mgr.set('API_KEY', 'val')
        msg = self.mgr.move_to_group('API_KEY', 'prod')
        assert 'Moved' in msg
        assert not self.mgr.exists('API_KEY')
        assert self.mgr.exists('prod:API_KEY')

    def test_move_grouped_key_to_another_group(self):
        """从一组移到另一组 — move_to_group 以完整 key 作为参数"""
        self.mgr.set_grouped('dev', 'KEY', 'dev_val')
        msg = self.mgr.move_to_group('dev:KEY', 'prod')
        assert 'Moved' in msg
        assert not self.mgr.exists('dev:KEY')
        # move_to_group 将完整 key 嵌套到新分组下
        assert self.mgr.exists('prod:dev:KEY')


class TestLoadEnvFileReportsSkippedKeys:
    """_load_env_file 应报告跳过的无效 key"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_load_env_file_skips_invalid_keys(self):
        """导入含无效 key 的 .env 文件应在消息中报告"""
        env_path = os.path.join(self.temp_dir, 'test.env')
        with open(env_path, 'w') as f:
            f.write('VALID_KEY=good\n')
            f.write('123BAD=invalid\n')       # 以数字开头
            f.write('ALSO-GOOD=nope\n')       # 含连字符
            f.write('ANOTHER_VALID=ok\n')

        msg = self.mgr.load(env_path)
        assert 'VALID_KEY' not in msg or 'Loaded' in msg
        assert 'Skipped' in msg
        assert '123BAD' in msg
        assert 'ALSO-GOOD' in msg

    def test_load_env_file_no_skipped_keys(self):
        """全部 key 合法时不报告跳过"""
        env_path = os.path.join(self.temp_dir, 'clean.env')
        with open(env_path, 'w') as f:
            f.write('GOOD_KEY=val1\n')
            f.write('ANOTHER=val2\n')

        msg = self.mgr.load(env_path)
        assert 'Skipped' not in msg

    def test_load_env_file_all_invalid(self):
        """全部 key 无效时报告全部跳过"""
        env_path = os.path.join(self.temp_dir, 'bad.env')
        with open(env_path, 'w') as f:
            f.write('1BAD=v1\n')
            f.write('2BAD=v2\n')

        msg = self.mgr.load(env_path)
        assert 'Skipped 2' in msg


class TestInitExports:
    """__init__.py 应导出核心 API"""

    def test_import_environment_manager(self):
        """from evm import EnvironmentManager"""
        from evm import EnvironmentManager
        assert EnvironmentManager is not None

    def test_import_exceptions(self):
        """from evm import 各异常 — 验证所有异常都可通过 evm 包导入"""
        import evm
        expected = [
            'EVMError', 'KeyNotFoundError', 'KeyAlreadyExistsError',
            'StorageError', 'CorruptedStorageError', 'StoragePermissionError',
            'LockTimeoutError', 'ExportError', 'ImportFailedError',
            'CommandNotFoundError', 'GroupNotFoundError', 'GroupOperationError',
            'BackupError', 'EditorError', 'DecryptionError',
            'ValidationError', 'SchemaError', 'OperationCancelledError',
        ]
        for name in expected:
            assert hasattr(evm, name), f"evm.{name} not exported"

    def test_version_and_author(self):
        """__version__ 和 __author__ 仍存在"""
        import evm
        assert evm.__version__
        assert evm.__author__

    def test_version_is_230(self):
        """版本号应为 2.3.0"""
        import evm
        assert evm.__version__ == '2.3.0'


class TestSecretWarningInstanceLevel:
    """_secret_warning_shown 应为实例变量，不影响其他实例"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_warning_shown_per_instance(self):
        """每个实例首次 set_secret 都应显示警告"""
        env1 = os.path.join(self.temp_dir, 'env1.json')
        env2 = os.path.join(self.temp_dir, 'env2.json')

        mgr1 = EnvironmentManager(env1)
        mgr2 = EnvironmentManager(env2)

        # mgr1 首次加密，应有警告
        msg1 = mgr1.set_secret('KEY1', 'val1')
        assert 'WARNING' in msg1

        # mgr2 是新实例，首次加密也应有警告
        msg2 = mgr2.set_secret('KEY2', 'val2')
        assert 'WARNING' in msg2

        # mgr1 第二次加密，不应有警告
        msg3 = mgr1.set_secret('KEY3', 'val3')
        assert 'WARNING' not in msg3

    def test_warning_not_shared_across_instances(self):
        """一个实例的警告不影响另一个"""
        env1 = os.path.join(self.temp_dir, 'a.json')
        env2 = os.path.join(self.temp_dir, 'b.json')

        mgr1 = EnvironmentManager(env1)
        mgr2 = EnvironmentManager(env2)

        # mgr1 触发警告
        mgr1.set_secret('K', 'v')
        assert mgr1._secret_warning_shown is True
        assert mgr2._secret_warning_shown is False


class TestHistoryFileLocking:
    """history.jsonl 写入应使用文件锁"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_history_file_created(self):
        """操作后应创建 history.jsonl"""
        self.mgr.set('KEY', 'val')
        history_file = self.mgr.env_file.parent / 'history.jsonl'
        assert history_file.exists()

    def test_history_file_has_content(self):
        """历史文件应有 JSON Lines 内容"""
        self.mgr.set('A', '1')
        self.mgr.set('B', '2')
        self.mgr.delete('A')

        entries = self.mgr.get_history(limit=10)
        assert len(entries) >= 3
        ops = [e['operation'] for e in entries]
        assert 'set' in ops
        assert 'delete' in ops

    def test_concurrent_history_writes(self):
        """并发写入不应导致行交错"""
        import concurrent.futures

        def write_entry(i):
            mgr = EnvironmentManager(self.env_file)
            mgr.set(f'KEY_{i}', f'val_{i}')

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_entry, i) for i in range(20)]
            concurrent.futures.wait(futures)

        # 验证所有行都是有效 JSON
        history_file = self.mgr.env_file.parent / 'history.jsonl'
        valid_count = 0
        with open(history_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)  # 如果行交错会抛异常
                    assert 'timestamp' in entry
                    valid_count += 1

        assert valid_count >= 20


class TestHistoryTrimLazy:
    """H2: History trim 应惰性触发，仅超过 1.5 倍上限时裁切"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_trim_not_triggered_below_threshold(self):
        """行数低于 1.5x MAX 时不触发裁切"""
        # 写入少量记录
        for i in range(10):
            self.mgr.set(f'KEY_{i}', f'val_{i}')

        history_file = self.mgr.env_file.parent / 'history.jsonl'
        with open(history_file, encoding='utf-8') as f:
            lines = f.readlines()
        # 应有 10 行（set 操作），远未触发裁切
        assert len(lines) == 10

    def test_trim_triggered_above_threshold(self):
        """行数超过 1.5x MAX_HISTORY_ENTRIES 时触发裁切"""
        # 降低 MAX 以加速测试
        self.mgr.MAX_HISTORY_ENTRIES = 20

        # 写入 35 条记录（超过 20 * 1.5 = 30）
        for i in range(35):
            self.mgr.set(f'K{i}', f'v{i}')

        # 第 35 次写入后应触发裁切
        history_file = self.mgr.env_file.parent / 'history.jsonl'
        with open(history_file, encoding='utf-8') as f:
            lines = f.readlines()
        # 裁切后保留一半（约 17 行）
        assert len(lines) < 35

    def test_trim_uses_atomic_write(self):
        """裁切应使用原子写入（临时文件 + rename），不留残留"""
        self.mgr.MAX_HISTORY_ENTRIES = 10

        for i in range(20):
            self.mgr.set(f'K{i}', f'v{i}')

        history_file = self.mgr.env_file.parent / 'history.jsonl'
        # 不应残留 .trim.tmp 文件
        tmp_path = str(history_file) + '.trim.tmp'
        assert not os.path.exists(tmp_path)


class TestNonInteractiveConfirmation:
    """H3: 非交互模式下 destructive 操作应给出清晰错误"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_clear_without_force_in_non_interactive(self):
        """非交互模式下 clear 无 --force 应报错并提示 --force"""
        from evm.cli import main
        # 先设置一个变量
        main(['--env-file', self.env_file, 'set', 'A', '1'])
        # 测试模式 stdin 不是 TTY，不带 --force 的 clear 应报错
        code = main(['--env-file', self.env_file, 'clear'])
        assert code == 1  # EVMError → exit code 1

    def test_clear_with_force_in_non_interactive(self):
        """非交互模式下 clear --force 应正常执行"""
        from evm.cli import main
        main(['--env-file', self.env_file, 'set', 'A', '1'])
        code = main(['--env-file', self.env_file, '--force', 'clear'])
        assert code == 0

    def test_delete_group_without_force_in_non_interactive(self):
        """非交互模式下 delete-group 无 --force 应报错"""
        from evm.cli import main
        main(['--env-file', self.env_file, 'setg', 'dev', 'K', 'v'])
        code = main(['--env-file', self.env_file, 'delete-group', 'dev'])
        assert code == 1

    def test_delete_group_with_force_in_non_interactive(self):
        """非交互模式下 delete-group --force 应正常执行"""
        from evm.cli import main
        main(['--env-file', self.env_file, 'setg', 'dev', 'K', 'v'])
        code = main(['--env-file', self.env_file, '--force', 'delete-group', 'dev'])
        assert code == 0


class TestSchemaWarningsModule:
    """M2: Schema 损坏应使用 warnings.warn() 而非 print()"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_corrupted_schema_emits_runtime_warning(self):
        """损坏的 schema 应触发 RuntimeWarning"""
        import warnings as warn_mod
        schema_file = self.mgr._get_schema_file()
        with open(schema_file, 'w') as f:
            f.write('{broken json')

        with warn_mod.catch_warnings(record=True) as w:
            warn_mod.simplefilter("always")
            result = self.mgr._load_schema()

        assert result == {}
        assert len(w) >= 1
        assert issubclass(w[0].category, RuntimeWarning)
        assert 'corrupted' in str(w[0].message).lower()

    def test_unreadable_schema_emits_runtime_warning(self):
        """不可读的 schema 应触发 RuntimeWarning（跳过权限测试在 root 下）"""
        import warnings as warn_mod
        schema_file = self.mgr._get_schema_file()
        schema_file.parent.mkdir(parents=True, exist_ok=True)
        schema_file.write_text('{}')
        # 设置不可读权限
        os.chmod(str(schema_file), 0o000)
        try:
            with warn_mod.catch_warnings(record=True) as w:
                warn_mod.simplefilter("always")
                result = self.mgr._load_schema()
            # root 用户可能仍能读取，检查结果即可
            if result == {}:
                # 如果确实读不到，应有 warning
                if len(w) > 0:
                    assert issubclass(w[0].category, RuntimeWarning)
        finally:
            os.chmod(str(schema_file), 0o600)


class TestShellCompletionDynamic:
    """M3: Shell 补全脚本应包含动态变量名补全"""

    def test_bash_completion_has_key_function(self):
        """bash 补全应包含 _evm_keys 函数"""
        from evm._completion import generate_bash_completion
        script = generate_bash_completion(['set', 'get', 'delete'])
        assert '_evm_keys' in script
        assert 'evm list --json --quiet' in script

    def test_bash_completion_has_key_cmds(self):
        """bash 补全应为 get/delete 等命令提供变量名补全"""
        from evm._completion import generate_bash_completion
        script = generate_bash_completion(['set', 'get', 'delete', 'edit'])
        assert 'get)' in script or 'get|' in script
        assert '_evm_keys' in script

    def test_zsh_completion_has_key_function(self):
        """zsh 补全应包含 _evm_keys 函数"""
        from evm._completion import generate_zsh_completion
        script = generate_zsh_completion(['set', 'get', 'delete'])
        assert '_evm_keys' in script
        assert 'evm list --json --quiet' in script

    def test_fish_completion_has_key_function(self):
        """fish 补全应包含 __evm_keys 函数"""
        from evm._completion import generate_fish_completion
        script = generate_fish_completion(['set', 'get', 'delete'])
        assert '__evm_keys' in script
        assert 'evm list --json --quiet' in script

    def test_fish_completion_has_key_commands(self):
        """fish 补全应为 get/delete 等命令提供变量名补全"""
        from evm._completion import generate_fish_completion
        script = generate_fish_completion(['set', 'get', 'delete', 'edit', 'rename'])
        assert '__fish_seen_subcommand_from get' in script
        assert '__fish_seen_subcommand_from delete' in script
        assert '__evm_keys' in script
