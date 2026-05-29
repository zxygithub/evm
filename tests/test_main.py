#!/usr/bin/env python3
"""EVM 完整测试套件

覆盖所有核心功能和 P0/P1/P2 改进。
所有测试使用临时文件，不影响真实环境变量。
"""

import json
import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path

from evm.exceptions import (
    BackupError,
    CorruptedStorageError,
    DecryptionError,
    EVMError,
    ExportError,
    GroupNotFoundError,
    GroupOperationError,
    ImportError_,
    KeyAlreadyExistsError,
    KeyNotFoundError,
    LockTimeoutError,
    OperationCancelledError,
    SchemaError,
    StorageError,
    ValidationError,
)
from evm.manager import EnvironmentManager


class TestEnvironmentManagerBase(unittest.TestCase):
    """测试基类：自动创建临时环境"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'test_env.json')
        self.manager = EnvironmentManager(self.env_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)


# ══════════════════════════════════════════════════════════════
# 基本 CRUD
# ══════════════════════════════════════════════════════════════


class TestBasicCRUD(TestEnvironmentManagerBase):

    def test_init_creates_directory(self):
        self.assertTrue(os.path.exists(os.path.dirname(self.env_file)))

    def test_set_and_get(self):
        self.manager.set('KEY', 'value')
        self.assertEqual(self.manager.get('KEY'), 'value')

    def test_set_overwrites(self):
        self.manager.set('KEY', 'v1')
        self.manager.set('KEY', 'v2')
        self.assertEqual(self.manager.get('KEY'), 'v2')

    def test_get_nonexistent_raises(self):
        with self.assertRaises(KeyNotFoundError):
            self.manager.get('MISSING')

    def test_delete(self):
        self.manager.set('KEY', 'value')
        self.manager.delete('KEY')
        self.assertFalse(self.manager.exists('KEY'))

    def test_delete_nonexistent_raises(self):
        with self.assertRaises(KeyNotFoundError):
            self.manager.delete('MISSING')

    def test_exists(self):
        self.assertFalse(self.manager.exists('KEY'))
        self.manager.set('KEY', 'value')
        self.assertTrue(self.manager.exists('KEY'))

    def test_list_vars_empty(self):
        self.assertEqual(self.manager.list_vars(), {})

    def test_list_vars_all(self):
        self.manager.set('A', '1')
        self.manager.set('B', '2')
        result = self.manager.list_vars()
        self.assertEqual(result, {'A': '1', 'B': '2'})

    def test_list_vars_pattern(self):
        self.manager.set('API_KEY', '123')
        self.manager.set('API_URL', 'http://x')
        self.manager.set('DB_HOST', 'localhost')
        result = self.manager.list_vars(pattern='API')
        self.assertEqual(len(result), 2)
        self.assertIn('API_KEY', result)
        self.assertIn('API_URL', result)

    def test_clear(self):
        self.manager.set('A', '1')
        self.manager.set('B', '2')
        self.manager.clear()
        self.assertEqual(self.manager.list_vars(), {})

    def test_clear_empty(self):
        msg = self.manager.clear()
        self.assertIn('No environment variables', msg)


# ══════════════════════════════════════════════════════════════
# P0: 安全修复
# ══════════════════════════════════════════════════════════════


class TestSecurity(TestEnvironmentManagerBase):

    def test_storage_file_permissions(self):
        """P0: 存储文件应为 600 权限"""
        self.manager.set('KEY', 'value')
        file_stat = os.stat(self.env_file)
        mode = stat.S_IMODE(file_stat.st_mode)
        self.assertEqual(mode, 0o600)

    def test_shell_export_escaping(self):
        """P0: shell 导出应使用 shlex.quote 转义"""
        self.manager.set('DANGEROUS', '$(rm -rf /)')
        export_file = os.path.join(self.temp_dir, 'export.sh')
        self.manager.export('sh', export_file)

        with open(export_file, 'r') as f:
            content = f.read()
        # 值应被正确引用，不会直接暴露 $(...)
        self.assertIn("'$(rm -rf /)'", content)
        self.assertNotIn('$(rm -rf /)\n', content)

    def test_shell_export_backticks(self):
        """P0: 反引号应被单引号包裹，防止执行"""
        self.manager.set('CMD', '`whoami`')
        export_file = os.path.join(self.temp_dir, 'export.sh')
        self.manager.export('sh', export_file)

        with open(export_file, 'r') as f:
            content = f.read()
        # shlex.quote 会将值用单引号包裹，使反引号成为字面量
        self.assertIn("'`whoami`'", content)

    def test_corrupted_storage_raises(self):
        """P0: 损坏的 JSON 文件应抛出 CorruptedStorageError"""
        with open(self.env_file, 'w') as f:
            f.write('{invalid json content')

        with self.assertRaises(CorruptedStorageError):
            EnvironmentManager(self.env_file)


# ══════════════════════════════════════════════════════════════
# 导入导出
# ══════════════════════════════════════════════════════════════


class TestExportImport(TestEnvironmentManagerBase):

    def test_export_json(self):
        self.manager.set('K1', 'v1')
        self.manager.set('K2', 'v2')
        export_file = os.path.join(self.temp_dir, 'export.json')
        self.manager.export('json', export_file)

        with open(export_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(data['K1'], 'v1')
        self.assertEqual(data['K2'], 'v2')

    def test_export_env(self):
        self.manager.set('K1', 'v1')
        export_file = os.path.join(self.temp_dir, 'export.env')
        self.manager.export('env', export_file)

        with open(export_file, 'r') as f:
            content = f.read()
        self.assertIn('K1=v1', content)

    def test_export_sh(self):
        self.manager.set('K1', 'v1')
        export_file = os.path.join(self.temp_dir, 'export.sh')
        self.manager.export('sh', export_file)

        with open(export_file, 'r') as f:
            content = f.read()
        self.assertIn('#!/bin/bash', content)
        self.assertIn('export K1=', content)

    def test_export_empty(self):
        msg = self.manager.export('json')
        self.assertIn('No environment variables', msg)

    def test_export_group(self):
        self.manager.set_grouped('dev', 'A', '1')
        self.manager.set('B', '2')
        export_file = os.path.join(self.temp_dir, 'export.json')
        self.manager.export('json', export_file, group='dev')

        with open(export_file, 'r') as f:
            data = json.load(f)
        self.assertIn('dev:A', data)
        self.assertNotIn('B', data)

    def test_export_group_not_found(self):
        with self.assertRaises(GroupNotFoundError):
            self.manager.export('json', group='nonexistent')

    def test_load_json(self):
        import_file = os.path.join(self.temp_dir, 'import.json')
        with open(import_file, 'w') as f:
            json.dump({'KEY1': 'val1', 'KEY2': 'val2'}, f)

        self.manager.load(import_file)
        self.assertEqual(self.manager.get('KEY1'), 'val1')
        self.assertEqual(self.manager.get('KEY2'), 'val2')

    def test_load_env(self):
        import_file = os.path.join(self.temp_dir, 'import.env')
        with open(import_file, 'w') as f:
            f.write('KEY1="val1"\n')
            f.write('# comment\n')
            f.write('KEY2=val2\n')

        self.manager.load(import_file)
        self.assertEqual(self.manager.get('KEY1'), 'val1')
        self.assertEqual(self.manager.get('KEY2'), 'val2')

    def test_load_replace(self):
        self.manager.set('OLD', 'old')
        import_file = os.path.join(self.temp_dir, 'import.json')
        with open(import_file, 'w') as f:
            json.dump({'NEW': 'new'}, f)

        self.manager.load(import_file, replace=True)
        self.assertFalse(self.manager.exists('OLD'))
        self.assertTrue(self.manager.exists('NEW'))

    def test_load_merge(self):
        self.manager.set('OLD', 'old')
        import_file = os.path.join(self.temp_dir, 'import.json')
        with open(import_file, 'w') as f:
            json.dump({'NEW': 'new'}, f)

        self.manager.load(import_file, replace=False)
        self.assertTrue(self.manager.exists('OLD'))
        self.assertTrue(self.manager.exists('NEW'))

    def test_load_with_group(self):
        import_file = os.path.join(self.temp_dir, 'import.json')
        with open(import_file, 'w') as f:
            json.dump({'KEY1': 'v1'}, f)

        self.manager.load(import_file, group='dev')
        self.assertTrue(self.manager.exists('dev:KEY1'))

    def test_load_nest(self):
        import_file = os.path.join(self.temp_dir, 'nested.json')
        with open(import_file, 'w') as f:
            json.dump({
                'dev': {'DB': 'localhost'},
                'prod': {'DB': 'prod.example.com'},
            }, f)

        self.manager.load(import_file, nest=True)
        self.assertEqual(self.manager.get('dev:DB'), 'localhost')
        self.assertEqual(self.manager.get('prod:DB'), 'prod.example.com')

    def test_load_backup_file(self):
        import_file = os.path.join(self.temp_dir, 'backup.json')
        with open(import_file, 'w') as f:
            json.dump({
                'timestamp': '2024-01-01T00:00:00',
                'variables': {'K1': 'v1'},
            }, f)

        self.manager.load(import_file, format_type='backup')
        self.assertEqual(self.manager.get('K1'), 'v1')

    def test_load_auto_detect_json(self):
        import_file = os.path.join(self.temp_dir, 'config')
        with open(import_file, 'w') as f:
            json.dump({'K1': 'v1'}, f)

        self.manager.load(import_file)
        self.assertEqual(self.manager.get('K1'), 'v1')

    def test_load_auto_detect_env(self):
        import_file = os.path.join(self.temp_dir, 'config')
        with open(import_file, 'w') as f:
            f.write('K1="v1"\n')

        self.manager.load(import_file)
        self.assertEqual(self.manager.get('K1'), 'v1')

    def test_load_file_not_found(self):
        with self.assertRaises(ImportError_):
            self.manager.load('/nonexistent/file.json')


# ══════════════════════════════════════════════════════════════
# 重命名 / 复制 / 搜索
# ══════════════════════════════════════════════════════════════


class TestRenameCopySearch(TestEnvironmentManagerBase):

    def test_rename(self):
        self.manager.set('OLD', 'value')
        self.manager.rename('OLD', 'NEW')
        self.assertFalse(self.manager.exists('OLD'))
        self.assertEqual(self.manager.get('NEW'), 'value')

    def test_rename_nonexistent_raises(self):
        with self.assertRaises(KeyNotFoundError):
            self.manager.rename('MISSING', 'NEW')

    def test_rename_conflict_raises(self):
        self.manager.set('A', '1')
        self.manager.set('B', '2')
        with self.assertRaises(KeyAlreadyExistsError):
            self.manager.rename('A', 'B')

    def test_copy(self):
        self.manager.set('SRC', 'value')
        self.manager.copy('SRC', 'DST')
        self.assertEqual(self.manager.get('DST'), 'value')
        self.assertTrue(self.manager.exists('SRC'))

    def test_copy_nonexistent_raises(self):
        with self.assertRaises(KeyNotFoundError):
            self.manager.copy('MISSING', 'DST')

    def test_search_by_key(self):
        self.manager.set('API_KEY', '123')
        self.manager.set('API_URL', 'http://x')
        self.manager.set('DB_HOST', 'localhost')
        results = self.manager.search('api')
        self.assertEqual(len(results), 2)

    def test_search_by_value(self):
        self.manager.set('A', 'hello_world')
        self.manager.set('B', 'goodbye')
        results = self.manager.search('hello', search_value=True)
        self.assertEqual(len(results), 1)
        self.assertIn('A', results)

    def test_search_no_results(self):
        self.manager.set('A', '1')
        results = self.manager.search('zzz')
        self.assertEqual(len(results), 0)


# ══════════════════════════════════════════════════════════════
# 备份恢复
# ══════════════════════════════════════════════════════════════


class TestBackupRestore(TestEnvironmentManagerBase):

    def test_backup(self):
        self.manager.set('K1', 'v1')
        backup_file = os.path.join(self.temp_dir, 'backup.json')
        self.manager.backup(backup_file)

        self.assertTrue(os.path.exists(backup_file))
        with open(backup_file, 'r') as f:
            data = json.load(f)
        self.assertIn('variables', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['variables']['K1'], 'v1')

    def test_restore_replace(self):
        self.manager.set('K1', 'v1')
        backup_file = os.path.join(self.temp_dir, 'backup.json')
        self.manager.backup(backup_file)

        self.manager.set('K2', 'v2')
        self.manager.restore(backup_file, merge=False)

        self.assertTrue(self.manager.exists('K1'))
        self.assertFalse(self.manager.exists('K2'))

    def test_restore_merge(self):
        self.manager.set('K1', 'v1')
        backup_file = os.path.join(self.temp_dir, 'backup.json')
        self.manager.backup(backup_file)

        self.manager.set('K2', 'v2')
        self.manager.restore(backup_file, merge=True)

        self.assertTrue(self.manager.exists('K1'))
        self.assertTrue(self.manager.exists('K2'))

    def test_restore_file_not_found(self):
        with self.assertRaises(BackupError):
            self.manager.restore('/nonexistent/backup.json')


# ══════════════════════════════════════════════════════════════
# 分组管理
# ══════════════════════════════════════════════════════════════


class TestGroups(TestEnvironmentManagerBase):

    def test_set_grouped(self):
        self.manager.set_grouped('dev', 'KEY', 'value')
        self.assertEqual(self.manager.get('dev:KEY'), 'value')

    def test_get_grouped(self):
        self.manager.set_grouped('dev', 'KEY', 'value')
        self.assertEqual(self.manager.get_grouped('dev', 'KEY'), 'value')

    def test_get_grouped_fallback(self):
        """get_grouped 应回退到无前缀 key"""
        self.manager.set('KEY', 'value')
        self.assertEqual(self.manager.get_grouped('dev', 'KEY'), 'value')

    def test_get_grouped_not_found(self):
        with self.assertRaises(KeyNotFoundError):
            self.manager.get_grouped('dev', 'MISSING')

    def test_delete_grouped(self):
        self.manager.set_grouped('dev', 'KEY', 'value')
        self.manager.delete_grouped('dev', 'KEY')
        self.assertFalse(self.manager.exists('dev:KEY'))

    def test_delete_grouped_not_found(self):
        with self.assertRaises(KeyNotFoundError):
            self.manager.delete_grouped('dev', 'MISSING')

    def test_list_groups(self):
        self.manager.set_grouped('dev', 'A', '1')
        self.manager.set_grouped('dev', 'B', '2')
        self.manager.set_grouped('prod', 'C', '3')
        groups = self.manager.list_groups()
        self.assertEqual(groups['dev'], 2)
        self.assertEqual(groups['prod'], 1)

    def test_list_groups_empty(self):
        self.assertEqual(self.manager.list_groups(), {})

    def test_list_vars_by_group(self):
        self.manager.set_grouped('dev', 'A', '1')
        self.manager.set_grouped('dev', 'B', '2')
        result = self.manager.list_vars(group='dev')
        self.assertEqual(len(result), 2)

    def test_list_vars_by_group_no_prefix(self):
        self.manager.set_grouped('dev', 'A', '1')
        result = self.manager.list_vars(group='dev', no_prefix=True)
        self.assertIn('A', result)
        self.assertNotIn('dev:A', result)

    def test_list_vars_group_not_found(self):
        with self.assertRaises(GroupNotFoundError):
            self.manager.list_vars(group='nonexistent')

    def test_delete_group(self):
        self.manager.set_grouped('dev', 'A', '1')
        self.manager.set_grouped('dev', 'B', '2')
        self.manager.set_grouped('prod', 'C', '3')
        self.manager.delete_group('dev')
        self.assertFalse(self.manager.exists('dev:A'))
        self.assertFalse(self.manager.exists('dev:B'))
        self.assertTrue(self.manager.exists('prod:C'))

    def test_delete_group_default_raises(self):
        with self.assertRaises(GroupOperationError):
            self.manager.delete_group('default')

    def test_delete_group_not_found(self):
        with self.assertRaises(GroupNotFoundError):
            self.manager.delete_group('nonexistent')

    def test_move_to_group(self):
        self.manager.set('KEY', 'value')
        self.manager.move_to_group('KEY', 'dev')
        self.assertFalse(self.manager.exists('KEY'))
        self.assertEqual(self.manager.get('dev:KEY'), 'value')

    def test_move_to_group_not_found(self):
        with self.assertRaises(KeyNotFoundError):
            self.manager.move_to_group('MISSING', 'dev')

    def test_mixed_variables(self):
        self.manager.set('GLOBAL', 'g')
        self.manager.set_grouped('dev', 'KEY', 'd')
        self.manager.set_grouped('prod', 'KEY', 'p')
        self.assertEqual(len(self.manager.list_vars()), 3)


# ══════════════════════════════════════════════════════════════
# 内存加载
# ══════════════════════════════════════════════════════════════


class TestLoadMemory(TestEnvironmentManagerBase):

    def test_load_to_memory_with_prefix(self):
        self.manager.set('TEST_VAR', 'test_value')
        count, prefix, filt = self.manager.load_to_memory()
        self.assertEqual(count, 1)
        self.assertTrue(prefix)
        self.assertEqual(os.environ.get('EVM:TEST_VAR'), 'test_value')
        # 清理
        del os.environ['EVM:TEST_VAR']

    def test_load_to_memory_no_prefix(self):
        self.manager.set('EVM_TEST_NOPREFIX', 'val')
        count, prefix, filt = self.manager.load_to_memory(add_evm_prefix=False)
        self.assertEqual(count, 1)
        self.assertFalse(prefix)
        self.assertEqual(os.environ.get('EVM_TEST_NOPREFIX'), 'val')
        del os.environ['EVM_TEST_NOPREFIX']

    def test_load_to_memory_with_filter(self):
        self.manager.set('FILTER_A', '1')
        self.manager.set('FILTER_B', '2')
        self.manager.set('OTHER', '3')
        count, _, filt = self.manager.load_to_memory(filter_prefix='FILTER_')
        self.assertEqual(count, 2)
        self.assertEqual(os.environ.get('EVM:FILTER_A'), '1')
        self.assertEqual(os.environ.get('EVM:FILTER_B'), '2')
        self.assertIsNone(os.environ.get('EVM:OTHER'))
        # 清理
        del os.environ['EVM:FILTER_A']
        del os.environ['EVM:FILTER_B']

    def test_load_to_memory_empty(self):
        count, _, _ = self.manager.load_to_memory()
        self.assertEqual(count, 0)


# ══════════════════════════════════════════════════════════════
# P2: 新功能
# ══════════════════════════════════════════════════════════════


class TestSecrets(TestEnvironmentManagerBase):

    def test_set_and_get_secret(self):
        self.manager.set_secret('API_KEY', 'super_secret_value')
        # v2 格式：ENCv2:<salt>:<hmac>:<ciphertext>
        raw = self.manager._env_vars['API_KEY']
        self.assertTrue(raw.startswith('ENCv2:'))
        self.assertNotEqual(raw, 'super_secret_value')
        # 解密应返回原值
        self.assertEqual(self.manager.get_secret('API_KEY'), 'super_secret_value')

    def test_secret_v1_backward_compat(self):
        """v1 格式的加密变量仍应可以解密"""
        import base64
        import hashlib
        import platform
        # 模拟旧版 v1 加密
        machine_id = (
            platform.node()
            + str(os.getuid() if hasattr(os, 'getuid') else '')
            + platform.machine()
        )
        key = hashlib.sha256(machine_id.encode()).digest()
        plaintext = 'old_secret_value'
        data_bytes = plaintext.encode('utf-8')
        encrypted = bytes(d ^ key[i % len(key)] for i, d in enumerate(data_bytes))
        v1_value = 'ENC:' + base64.b64encode(encrypted).decode('ascii')

        self.manager._env_vars['OLD_SECRET'] = v1_value
        self.manager._save_env_vars()

        # 应该可以解密 v1 格式
        result = self.manager.get_secret('OLD_SECRET')
        self.assertEqual(result, 'old_secret_value')

    def test_secret_tamper_detection(self):
        """v2 格式的 HMAC 应能检测篡改"""
        self.manager.set_secret('TAMPER_TEST', 'original_value')
        raw = self.manager._env_vars['TAMPER_TEST']
        # 篡改密文部分
        parts = raw[len('ENCv2:'):].split(':')
        parts[2] = 'AAAA'  # 替换密文
        self.manager._env_vars['TAMPER_TEST'] = 'ENCv2:' + ':'.join(parts)

        with self.assertRaises(DecryptionError):
            self.manager.get_secret('TAMPER_TEST')

    def test_get_secret_non_secret_raises(self):
        self.manager.set('PLAIN', 'value')
        with self.assertRaises(DecryptionError):
            self.manager.get_secret('PLAIN')

    def test_get_secret_not_found(self):
        with self.assertRaises(KeyNotFoundError):
            self.manager.get_secret('MISSING')


class TestTemplates(TestEnvironmentManagerBase):

    def test_expand_simple(self):
        self.manager.set('HOST', 'localhost')
        self.manager.set('URL', 'http://{{HOST}}:3000')
        self.assertEqual(self.manager.expand('URL'), 'http://localhost:3000')

    def test_expand_multiple(self):
        self.manager.set('HOST', 'localhost')
        self.manager.set('PORT', '8080')
        self.manager.set('URL', 'http://{{HOST}}:{{PORT}}')
        self.assertEqual(self.manager.expand('URL'), 'http://localhost:8080')

    def test_expand_no_template(self):
        self.manager.set('PLAIN', 'no templates here')
        self.assertEqual(self.manager.expand('PLAIN'), 'no templates here')

    def test_expand_missing_ref(self):
        self.manager.set('URL', 'http://{{MISSING}}:3000')
        self.assertEqual(self.manager.expand('URL'), 'http://{{MISSING}}:3000')

    def test_expand_not_found(self):
        with self.assertRaises(KeyNotFoundError):
            self.manager.expand('MISSING')


class TestInfo(TestEnvironmentManagerBase):

    def test_info_basic(self):
        info = self.manager.info()
        self.assertIn('version', info)
        self.assertIn('storage_path', info)
        self.assertEqual(info['total_variables'], 0)

    def test_info_with_data(self):
        self.manager.set('A', '1')
        self.manager.set_grouped('dev', 'B', '2')
        info = self.manager.info()
        self.assertEqual(info['total_variables'], 2)
        self.assertEqual(info['total_groups'], 1)
        self.assertIn('dev', info['groups'])

    def test_info_with_secrets(self):
        self.manager.set_secret('SECRET', 'val')
        info = self.manager.info()
        self.assertEqual(info['secret_variables'], 1)


class TestDiff(TestEnvironmentManagerBase):

    def test_diff_no_changes(self):
        self.manager.set('A', '1')
        backup_file = os.path.join(self.temp_dir, 'backup.json')
        self.manager.backup(backup_file)

        result = self.manager.diff(backup_file)
        self.assertEqual(len(result['added']), 0)
        self.assertEqual(len(result['removed']), 0)
        self.assertEqual(len(result['changed']), 0)

    def test_diff_added(self):
        backup_file = os.path.join(self.temp_dir, 'backup.json')
        self.manager.backup(backup_file)

        self.manager.set('NEW', 'value')
        result = self.manager.diff(backup_file)
        self.assertIn('NEW', result['added'])

    def test_diff_removed(self):
        self.manager.set('OLD', 'value')
        backup_file = os.path.join(self.temp_dir, 'backup.json')
        self.manager.backup(backup_file)

        self.manager.delete('OLD')
        result = self.manager.diff(backup_file)
        self.assertIn('OLD', result['removed'])

    def test_diff_changed(self):
        self.manager.set('KEY', 'old_value')
        backup_file = os.path.join(self.temp_dir, 'backup.json')
        self.manager.backup(backup_file)

        self.manager.set('KEY', 'new_value')
        result = self.manager.diff(backup_file)
        self.assertIn('KEY', result['changed'])
        self.assertEqual(result['changed']['KEY']['current'], 'new_value')
        self.assertEqual(result['changed']['KEY']['backup'], 'old_value')

    def test_diff_file_not_found(self):
        with self.assertRaises(BackupError):
            self.manager.diff('/nonexistent/backup.json')


class TestDryRun(TestEnvironmentManagerBase):

    def test_dry_run_set(self):
        msg = self.manager.set('KEY', 'value', dry_run=True)
        self.assertIn('DRY-RUN', msg)
        self.assertFalse(self.manager.exists('KEY'))

    def test_dry_run_delete(self):
        self.manager.set('KEY', 'value')
        msg = self.manager.delete('KEY', dry_run=True)
        self.assertIn('DRY-RUN', msg)
        self.assertTrue(self.manager.exists('KEY'))

    def test_dry_run_clear(self):
        self.manager.set('A', '1')
        msg = self.manager.clear(dry_run=True)
        self.assertIn('DRY-RUN', msg)
        self.assertTrue(self.manager.exists('A'))

    def test_dry_run_rename(self):
        self.manager.set('OLD', 'value')
        msg = self.manager.rename('OLD', 'NEW', dry_run=True)
        self.assertIn('DRY-RUN', msg)
        self.assertTrue(self.manager.exists('OLD'))
        self.assertFalse(self.manager.exists('NEW'))

    def test_dry_run_copy(self):
        self.manager.set('SRC', 'value')
        msg = self.manager.copy('SRC', 'DST', dry_run=True)
        self.assertIn('DRY-RUN', msg)
        self.assertFalse(self.manager.exists('DST'))

    def test_dry_run_export(self):
        self.manager.set('K', 'v')
        msg = self.manager.export('json', dry_run=True)
        self.assertIn('DRY-RUN', msg)

    def test_dry_run_load(self):
        import_file = os.path.join(self.temp_dir, 'import.json')
        with open(import_file, 'w') as f:
            json.dump({'K': 'v'}, f)

        msg = self.manager.load(import_file, dry_run=True)
        self.assertIn('DRY-RUN', msg)
        self.assertFalse(self.manager.exists('K'))

    def test_dry_run_set_grouped(self):
        msg = self.manager.set_grouped('dev', 'K', 'v', dry_run=True)
        self.assertIn('DRY-RUN', msg)
        self.assertFalse(self.manager.exists('dev:K'))

    def test_dry_run_delete_group(self):
        self.manager.set_grouped('dev', 'K', 'v')
        msg = self.manager.delete_group('dev', dry_run=True)
        self.assertIn('DRY-RUN', msg)
        self.assertTrue(self.manager.exists('dev:K'))

    def test_dry_run_set_secret(self):
        msg = self.manager.set_secret('KEY', 'val', dry_run=True)
        self.assertIn('DRY-RUN', msg)
        self.assertFalse(self.manager.exists('KEY'))


class TestFileLocking(TestEnvironmentManagerBase):

    def test_atomic_write(self):
        """写入应为原子操作（不留下临时文件）"""
        self.manager.set('KEY', 'value')
        # 临时文件不应残留
        tmp_files = [
            f for f in os.listdir(os.path.dirname(self.env_file))
            if f.startswith('.env_') and f.endswith('.tmp')
        ]
        self.assertEqual(len(tmp_files), 0)

    def test_data_persistence(self):
        """写入后重新加载应得到相同数据"""
        self.manager.set('PERSIST', 'value')
        new_mgr = EnvironmentManager(self.env_file)
        self.assertEqual(new_mgr.get('PERSIST'), 'value')


# ══════════════════════════════════════════════════════════════
# CLI 入口测试
# ══════════════════════════════════════════════════════════════


class TestCLI(unittest.TestCase):
    """测试 CLI 入口（使用 --env-file 隔离）"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'cli_test.json')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _run(self, args):
        from evm.cli import main
        return main(['--env-file', self.env_file] + args)

    def test_no_command_shows_help(self):
        """无命令时应显示帮助（返回 0）"""
        code = self._run([])
        self.assertEqual(code, 0)

    def test_set_and_get(self):
        code = self._run(['set', 'CLI_KEY', 'cli_value'])
        self.assertEqual(code, 0)

        code = self._run(['get', 'CLI_KEY'])
        self.assertEqual(code, 0)

    def test_get_missing_returns_error(self):
        code = self._run(['get', 'MISSING'])
        self.assertEqual(code, 1)

    def test_list(self):
        self._run(['set', 'A', '1'])
        code = self._run(['list'])
        self.assertEqual(code, 0)

    def test_info(self):
        code = self._run(['info'])
        self.assertEqual(code, 0)

    def test_verbose(self):
        code = self._run(['-v'])
        self.assertEqual(code, 0)

    def test_version(self):
        from evm.cli import main
        with self.assertRaises(SystemExit) as ctx:
            main(['--env-file', self.env_file, '--version'])
        self.assertEqual(ctx.exception.code, 0)

    def test_dry_run_set(self):
        code = self._run(['--dry-run', 'set', 'KEY', 'val'])
        self.assertEqual(code, 0)
        # 验证没有实际写入
        code = self._run(['get', 'KEY'])
        self.assertEqual(code, 1)


# ══════════════════════════════════════════════════════════════
# P1: 文件锁超时
# ══════════════════════════════════════════════════════════════


class TestLockTimeout(TestEnvironmentManagerBase):

    def test_lock_timeout_custom(self):
        """自定义超时值"""
        mgr = EnvironmentManager(self.env_file, lock_timeout=0.1)
        self.assertEqual(mgr.lock_timeout, 0.1)

    def test_concurrent_write_no_conflict(self):
        """顺序写入不应冲突"""
        self.manager.set('A', '1')
        self.manager.set('B', '2')
        self.assertEqual(self.manager.get('A'), '1')
        self.assertEqual(self.manager.get('B'), '2')


# ══════════════════════════════════════════════════════════════
# P1: load() 重构
# ══════════════════════════════════════════════════════════════


class TestLoadRefactored(TestEnvironmentManagerBase):

    def test_detect_format_explicit(self):
        path = Path(self.temp_dir) / 'test.dat'
        path.touch()
        fmt = self.manager._detect_format(path, 'json')
        self.assertEqual(fmt, 'json')

    def test_detect_format_by_extension(self):
        json_path = Path(self.temp_dir) / 'test.json'
        json_path.touch()
        env_path = Path(self.temp_dir) / 'test.env'
        env_path.touch()

        self.assertEqual(self.manager._detect_format(json_path, None), 'json')
        self.assertEqual(self.manager._detect_format(env_path, None), 'env')

    def test_detect_format_by_content(self):
        json_path = Path(self.temp_dir) / 'config'
        with open(json_path, 'w') as f:
            f.write('{"key": "value"}')
        self.assertEqual(self.manager._detect_format(json_path, None), 'json')

        env_path = Path(self.temp_dir) / 'config2'
        with open(env_path, 'w') as f:
            f.write('KEY=value\n')
        self.assertEqual(self.manager._detect_format(env_path, None), 'env')

    def test_load_nested_returns_groups(self):
        data = {
            'dev': {'A': '1', 'B': '2'},
            'prod': {'A': '3'},
        }
        loaded, groups = self.manager._load_nested(data)
        self.assertEqual(groups, 2)
        self.assertEqual(loaded['dev:A'], '1')
        self.assertEqual(loaded['prod:A'], '3')

    def test_apply_group_prefix(self):
        vars_dict = {'KEY1': 'v1', 'KEY2': 'v2'}
        result = self.manager._apply_group_prefix(vars_dict, 'staging')
        self.assertIn('staging:KEY1', result)
        self.assertIn('staging:KEY2', result)

    def test_apply_group_prefix_none(self):
        vars_dict = {'KEY1': 'v1'}
        result = self.manager._apply_group_prefix(vars_dict, None)
        self.assertEqual(result, vars_dict)


# ══════════════════════════════════════════════════════════════
# P2: 操作历史
# ══════════════════════════════════════════════════════════════


class TestHistory(TestEnvironmentManagerBase):

    def test_log_and_get_history(self):
        self.manager.set('HIST_KEY', 'value')
        history = self.manager.get_history(limit=10)
        self.assertTrue(len(history) >= 1)
        self.assertEqual(history[0]['operation'], 'set')
        self.assertEqual(history[0]['key'], 'HIST_KEY')

    def test_history_empty(self):
        history = self.manager.get_history()
        self.assertEqual(history, [])

    def test_clear_history(self):
        self.manager.set('A', '1')
        self.manager.set('B', '2')
        msg = self.manager.clear_history()
        self.assertIn('cleared', msg.lower())
        history = self.manager.get_history()
        self.assertEqual(history, [])

    def test_history_latest_first(self):
        self.manager.set('FIRST', '1')
        self.manager.set('SECOND', '2')
        history = self.manager.get_history(limit=10)
        # 最新在前
        self.assertEqual(history[0]['key'], 'SECOND')
        self.assertEqual(history[1]['key'], 'FIRST')

    def test_history_operations_logged(self):
        """多种操作都应记录日志"""
        self.manager.set('A', '1')
        self.manager.delete('A')
        self.manager.set('B', '2')
        self.manager.rename('B', 'C')

        history = self.manager.get_history(limit=10)
        ops = [h['operation'] for h in history]
        self.assertIn('set', ops)
        self.assertIn('delete', ops)
        self.assertIn('rename', ops)


# ══════════════════════════════════════════════════════════════
# P2: Schema 定义和校验
# ══════════════════════════════════════════════════════════════


class TestSchema(TestEnvironmentManagerBase):

    def test_set_schema(self):
        msg = self.manager.set_schema('API_URL', format='url', required=True)
        self.assertIn('API_URL', msg)

    def test_set_schema_invalid_format(self):
        with self.assertRaises(SchemaError):
            self.manager.set_schema('KEY', format='nonexistent_format')

    def test_set_schema_invalid_regex(self):
        with self.assertRaises(SchemaError):
            self.manager.set_schema('KEY', pattern='[invalid')

    def test_get_schema(self):
        self.manager.set_schema('URL', format='url')
        schema = self.manager.get_schema('URL')
        self.assertIn('URL', schema)
        self.assertEqual(schema['URL']['format'], 'url')

    def test_get_schema_not_found(self):
        with self.assertRaises(SchemaError):
            self.manager.get_schema('MISSING')

    def test_get_all_schema(self):
        self.manager.set_schema('A', format='url')
        self.manager.set_schema('B', format='email')
        schema = self.manager.get_schema()
        self.assertEqual(len(schema), 2)

    def test_delete_schema(self):
        self.manager.set_schema('KEY', format='url')
        msg = self.manager.delete_schema('KEY')
        self.assertIn('KEY', msg)
        with self.assertRaises(SchemaError):
            self.manager.get_schema('KEY')

    def test_validate_url_valid(self):
        self.manager.set('API_URL', 'https://api.example.com/v1')
        self.manager.set_schema('API_URL', format='url')
        result = self.manager.validate('API_URL')
        self.assertTrue(result['valid'])

    def test_validate_url_invalid(self):
        self.manager.set('API_URL', 'not-a-url')
        self.manager.set_schema('API_URL', format='url')
        result = self.manager.validate('API_URL')
        self.assertFalse(result['valid'])

    def test_validate_email(self):
        self.manager.set_schema('EMAIL', format='email')
        self.manager.set('EMAIL', 'user@example.com')
        self.assertTrue(self.manager.validate('EMAIL')['valid'])

        self.manager.set('EMAIL', 'invalid-email')
        self.assertFalse(self.manager.validate('EMAIL')['valid'])

    def test_validate_port(self):
        self.manager.set_schema('PORT', format='port')
        self.manager.set('PORT', '8080')
        self.assertTrue(self.manager.validate('PORT')['valid'])

        self.manager.set('PORT', 'not-a-port')
        self.assertFalse(self.manager.validate('PORT')['valid'])

    def test_validate_integer(self):
        self.manager.set_schema('COUNT', format='integer')
        self.manager.set('COUNT', '-42')
        self.assertTrue(self.manager.validate('COUNT')['valid'])

        self.manager.set('COUNT', 'not-a-number')
        self.assertFalse(self.manager.validate('COUNT')['valid'])

    def test_validate_boolean(self):
        self.manager.set_schema('FLAG', format='boolean')
        self.manager.set('FLAG', 'true')
        self.assertTrue(self.manager.validate('FLAG')['valid'])

        self.manager.set('FLAG', 'maybe')
        self.assertFalse(self.manager.validate('FLAG')['valid'])

    def test_validate_ipv4(self):
        self.manager.set_schema('IP', format='ipv4')
        self.manager.set('IP', '192.168.1.1')
        self.assertTrue(self.manager.validate('IP')['valid'])

        self.manager.set('IP', '999.999.999.999')
        self.assertFalse(self.manager.validate('IP')['valid'])

    def test_validate_custom_pattern(self):
        self.manager.set_schema('CODE', pattern=r'^[A-Z]{3}-\d{4}$')
        self.manager.set('CODE', 'ABC-1234')
        self.assertTrue(self.manager.validate('CODE')['valid'])

        self.manager.set('CODE', 'abc')
        self.assertFalse(self.manager.validate('CODE')['valid'])

    def test_validate_required_missing(self):
        self.manager.set_schema('REQUIRED_VAR', format='url', required=True)
        result = self.manager.validate('REQUIRED_VAR')
        self.assertFalse(result['valid'])
        self.assertTrue(any('Required' in e for e in result['errors']))

    def test_validate_all(self):
        self.manager.set('URL', 'https://example.com')
        self.manager.set('PORT', '8080')
        self.manager.set_schema('URL', format='url')
        self.manager.set_schema('PORT', format='port')
        results = self.manager.validate_all()
        self.assertTrue(all(r['valid'] for r in results.values()))

    def test_validate_no_schema(self):
        with self.assertRaises(SchemaError):
            self.manager.validate('NO_SCHEMA_KEY')


# ══════════════════════════════════════════════════════════════
# P2: Shell 补全
# ══════════════════════════════════════════════════════════════


class TestCompletion(TestEnvironmentManagerBase):

    def test_bash_completion(self):
        from evm._completion import generate_bash_completion
        from evm.cli import ALL_COMMANDS
        script = generate_bash_completion(ALL_COMMANDS)
        self.assertIn('_evm_completions', script)
        self.assertIn('complete -F', script)
        self.assertIn('set', script)

    def test_zsh_completion(self):
        from evm._completion import generate_zsh_completion
        from evm.cli import ALL_COMMANDS
        script = generate_zsh_completion(ALL_COMMANDS)
        self.assertIn('#compdef evm', script)

    def test_fish_completion(self):
        from evm._completion import generate_fish_completion
        from evm.cli import ALL_COMMANDS
        script = generate_fish_completion(ALL_COMMANDS)
        self.assertIn('complete -c evm', script)


# ══════════════════════════════════════════════════════════════
# P2: CLI 新命令
# ══════════════════════════════════════════════════════════════


class TestCLINewCommands(unittest.TestCase):
    """测试新增 CLI 命令"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'cli_test.json')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _run(self, args):
        from evm.cli import main
        return main(['--env-file', self.env_file] + args)

    def test_completion_bash(self):
        code = self._run(['completion', 'bash'])
        self.assertEqual(code, 0)

    def test_completion_zsh(self):
        code = self._run(['completion', 'zsh'])
        self.assertEqual(code, 0)

    def test_completion_fish(self):
        code = self._run(['completion', 'fish'])
        self.assertEqual(code, 0)

    def test_history_empty(self):
        code = self._run(['history'])
        self.assertEqual(code, 0)

    def test_history_with_data(self):
        self._run(['set', 'A', '1'])
        code = self._run(['history'])
        self.assertEqual(code, 0)

    def test_history_clear(self):
        self._run(['set', 'A', '1'])
        code = self._run(['history', '--clear'])
        self.assertEqual(code, 0)

    def test_schema_set(self):
        code = self._run(['schema', 'set', 'URL', '--format', 'url'])
        self.assertEqual(code, 0)

    def test_schema_list(self):
        self._run(['schema', 'set', 'URL', '--format', 'url'])
        code = self._run(['schema', 'list'])
        self.assertEqual(code, 0)

    def test_schema_delete(self):
        self._run(['schema', 'set', 'URL', '--format', 'url'])
        code = self._run(['schema', 'delete', 'URL'])
        self.assertEqual(code, 0)

    def test_validate_with_schema(self):
        self._run(['set', 'URL', 'https://example.com'])
        self._run(['schema', 'set', 'URL', '--format', 'url'])
        code = self._run(['validate', 'URL'])
        self.assertEqual(code, 0)

    def test_validate_all(self):
        self._run(['set', 'URL', 'https://example.com'])
        self._run(['schema', 'set', 'URL', '--format', 'url'])
        code = self._run(['validate'])
        self.assertEqual(code, 0)

    def test_clear_with_force(self):
        self._run(['set', 'A', '1'])
        code = self._run(['--force', 'clear'])
        self.assertEqual(code, 0)

    def test_delete_group_with_force(self):
        self._run(['setg', 'test_grp', 'K', 'v'])
        code = self._run(['--force', 'delete-group', 'test_grp'])
        self.assertEqual(code, 0)


if __name__ == '__main__':
    unittest.main()
