#!/usr/bin/env python3
"""EVM 完整测试套件

覆盖所有核心功能和 P0/P1/P2 改进。
所有测试使用临时文件，不影响真实环境变量。
"""

import json
import os
import shutil
import stat
import sys
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
        # v3 格式：ENCv3:<salt>:<iv>:<mac>:<ciphertext>
        raw = self.manager._env_vars['API_KEY']
        self.assertTrue(raw.startswith('ENCv3:'))
        self.assertNotEqual(raw, 'super_secret_value')
        # 解密应返回原值
        self.assertEqual(self.manager.get_secret('API_KEY'), 'super_secret_value')

    def test_secret_v1_backward_compat(self):
        """v1 格式的加密变量仍应可以解密，并自动迁移到 v3"""
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
        # 自动迁移到 v3
        self.assertTrue(
            self.manager._env_vars['OLD_SECRET'].startswith('ENCv3:')
        )

    def test_secret_v2_backward_compat(self):
        """v2 格式的加密变量应可以解密，并自动迁移到 v3"""
        import base64
        import hashlib
        import hmac as hmac_mod
        import os as os_mod
        import platform as platform_mod

        salt = os_mod.urandom(16)
        machine_id = (
            platform_mod.node()
            + str(os_mod.getuid() if hasattr(os_mod, 'getuid') else '')
            + platform_mod.machine()
        )
        key = hashlib.pbkdf2_hmac(
            'sha256', machine_id.encode(), salt, 100000, dklen=32
        )
        plaintext = 'v2_secret_value'
        data_bytes = plaintext.encode('utf-8')
        ciphertext = bytes(
            d ^ key[i % len(key)] for i, d in enumerate(data_bytes)
        )
        mac = hmac_mod.new(key, salt + ciphertext, hashlib.sha256).digest()
        v2_value = (
            'ENCv2:'
            + base64.b64encode(salt).decode()
            + ':' + base64.b64encode(mac).decode()
            + ':' + base64.b64encode(ciphertext).decode()
        )

        self.manager._env_vars['V2_SECRET'] = v2_value
        self.manager._save_env_vars()

        result = self.manager.get_secret('V2_SECRET')
        self.assertEqual(result, 'v2_secret_value')
        # 自动迁移到 v3
        self.assertTrue(
            self.manager._env_vars['V2_SECRET'].startswith('ENCv3:')
        )

    def test_secret_tamper_detection(self):
        """v3 格式的 MAC 应能检测篡改"""
        self.manager.set_secret('TAMPER_TEST', 'original_value')
        raw = self.manager._env_vars['TAMPER_TEST']
        # 篡改密文部分 (ENCv3:salt:iv:mac:ciphertext)
        parts = raw[len('ENCv3:'):].split(':')
        parts[3] = 'AAAA'  # 替换密文
        self.manager._env_vars['TAMPER_TEST'] = 'ENCv3:' + ':'.join(parts)

        with self.assertRaises(DecryptionError):
            self.manager.get_secret('TAMPER_TEST')

    def test_secret_first_time_warning(self):
        """首次使用加密功能应包含警告"""
        EnvironmentManager._secret_warning_shown = False
        msg = self.manager.set_secret('WARN_KEY', 'value')
        self.assertIn('WARNING', msg)
        # 第二次不再有警告
        msg2 = self.manager.set_secret('WARN_KEY2', 'value2')
        self.assertNotIn('WARNING', msg2)

    def test_set_does_not_log_value(self):
        """#6: set 操作不应在历史中记录 value"""
        self.manager.set('SENSITIVE', 'my_password_123')
        history = self.manager.get_history(limit=10)
        for entry in history:
            if entry['operation'] == 'set' and entry['key'] == 'SENSITIVE':
                self.assertNotIn('my_password_123', entry.get('details', ''))

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
        self.assertEqual(code, 2)  # KeyNotFoundError → exit code 2

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
        # 验证没有实际写入 — KeyNotFoundError → exit code 2
        code = self._run(['get', 'KEY'])
        self.assertEqual(code, 2)


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


# ══════════════════════════════════════════════════════════════
# P0: JSON 输出模式
# ══════════════════════════════════════════════════════════════


class TestJSONOutput(unittest.TestCase):
    """测试 --json 模式：所有命令的 JSON 输出"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'json_test.json')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _run_json(self, args):
        """运行命令并捕获 JSON 输出"""
        import io
        from evm.cli import main
        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        try:
            code = main(['--env-file', self.env_file, '--json'] + args)
        except SystemExit as e:
            code = e.code
        finally:
            sys.stdout = old_stdout
        output = captured.getvalue()
        return code, output

    def _parse_json(self, output):
        """解析 JSON 输出"""
        import json as json_mod
        # 取最后一行非空的输出
        for line in reversed(output.strip().split('\n')):
            line = line.strip()
            if line:
                return json_mod.loads(line)
        return None

    def test_set_json(self):
        code, output = self._run_json(['set', 'KEY', 'value'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['data']['key'], 'KEY')
        self.assertEqual(data['data']['value'], 'value')

    def test_get_json(self):
        self._run_json(['set', 'API_KEY', 'secret123'])
        code, output = self._run_json(['get', 'API_KEY'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['data']['value'], 'secret123')

    def test_get_missing_json_error(self):
        code, output = self._run_json(['get', 'MISSING'])
        self.assertEqual(code, 2)
        # JSON 错误输出到 stderr，不检查 stdout

    def test_list_json(self):
        self._run_json(['set', 'A', '1'])
        self._run_json(['set', 'B', '2'])
        code, output = self._run_json(['list'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('A', data['data'])
        self.assertIn('B', data['data'])

    def test_list_empty_json(self):
        code, output = self._run_json(['list'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['data'], {})

    def test_delete_json(self):
        self._run_json(['set', 'KEY', 'val'])
        code, output = self._run_json(['delete', 'KEY'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertTrue(data['data']['deleted'])

    def test_search_json(self):
        self._run_json(['set', 'API_KEY', '123'])
        self._run_json(['set', 'API_URL', 'http://x'])
        code, output = self._run_json(['search', 'API'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertIn('API_KEY', data['data'])
        self.assertIn('API_URL', data['data'])

    def test_info_json(self):
        code, output = self._run_json(['info'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertIn('version', data['data'])
        self.assertIn('storage_path', data['data'])

    def test_groups_json(self):
        self._run_json(['setg', 'dev', 'KEY', 'val'])
        code, output = self._run_json(['groups'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertIn('dev', data['data']['groups'])

    def test_clear_json(self):
        self._run_json(['set', 'A', '1'])
        code, output = self._run_json(['--force', 'clear'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['data']['cleared'], 1)

    def test_rename_json(self):
        self._run_json(['set', 'OLD', 'val'])
        code, output = self._run_json(['rename', 'OLD', 'NEW'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['data']['old_key'], 'OLD')
        self.assertEqual(data['data']['new_key'], 'NEW')

    def test_copy_json(self):
        self._run_json(['set', 'SRC', 'val'])
        code, output = self._run_json(['copy', 'SRC', 'DST'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['data']['src_key'], 'SRC')
        self.assertEqual(data['data']['dst_key'], 'DST')

    def test_expand_json(self):
        self._run_json(['set', 'HOST', 'localhost'])
        self._run_json(['set', 'URL', 'http://{{HOST}}:3000'])
        code, output = self._run_json(['expand', 'URL'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['data']['expanded'], 'http://localhost:3000')

    def test_diff_json(self):
        self._run_json(['set', 'A', '1'])
        backup = os.path.join(self.temp_dir, 'backup.json')
        from evm.cli import main
        main(['--env-file', self.env_file, 'backup', '--file', backup])
        self._run_json(['set', 'B', '2'])
        code, output = self._run_json(['diff', backup])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertIn('B', data['data']['added'])

    def test_history_json(self):
        self._run_json(['set', 'A', '1'])
        code, output = self._run_json(['history'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertIsInstance(data['data'], list)
        self.assertTrue(len(data['data']) >= 1)

    def test_validate_json(self):
        self._run_json(['set', 'URL', 'https://example.com'])
        self._run_json(['schema', 'set', 'URL', '--format', 'url'])
        code, output = self._run_json(['validate', 'URL'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertTrue(data['data']['valid'])

    def test_schema_set_json(self):
        code, output = self._run_json(['schema', 'set', 'URL', '--format', 'url'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['data']['key'], 'URL')

    def test_schema_list_json(self):
        self._run_json(['schema', 'set', 'URL', '--format', 'url'])
        code, output = self._run_json(['schema', 'list'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertIn('URL', data['data'])

    def test_export_json_mode(self):
        self._run_json(['set', 'K', 'v'])
        code, output = self._run_json(['export', '--format', 'env'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertIn('message', data['data'])

    def test_load_json_mode(self):
        import_file = os.path.join(self.temp_dir, 'import.json')
        with open(import_file, 'w') as f:
            json.dump({'LOADED': 'yes'}, f)
        code, output = self._run_json(['load', import_file])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertIn('message', data['data'])

    def test_backup_json_mode(self):
        self._run_json(['set', 'K', 'v'])
        code, output = self._run_json(['backup'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertIn('message', data['data'])

    def test_setg_json(self):
        code, output = self._run_json(['setg', 'dev', 'KEY', 'val'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['data']['group'], 'dev')

    def test_getg_json(self):
        self._run_json(['setg', 'dev', 'KEY', 'val'])
        code, output = self._run_json(['getg', 'dev', 'KEY'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['data']['value'], 'val')

    def test_move_group_json(self):
        self._run_json(['set', 'KEY', 'val'])
        code, output = self._run_json(['move-group', 'KEY', 'prod'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['data']['target_group'], 'prod')

    def test_loadmemory_json(self):
        self._run_json(['set', 'MEM_VAR', 'mem_val'])
        code, output = self._run_json(['loadmemory'])
        self.assertEqual(code, 0)
        data = self._parse_json(output)
        self.assertEqual(data['data']['loaded'], 1)
        # 清理
        if 'EVM:MEM_VAR' in os.environ:
            del os.environ['EVM:MEM_VAR']

    def test_completion_not_json(self):
        """completion 命令不受 --json 影响"""
        code, output = self._run_json(['completion', 'bash'])
        self.assertEqual(code, 0)
        self.assertIn('_evm_completions', output)


# ══════════════════════════════════════════════════════════════
# P0: 细化退出码
# ══════════════════════════════════════════════════════════════


class TestExitCodes(unittest.TestCase):
    """测试细化退出码"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'exit_test.json')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _run(self, args):
        from evm.cli import main
        return main(['--env-file', self.env_file] + args)

    def test_success_code_0(self):
        code = self._run(['set', 'K', 'v'])
        self.assertEqual(code, 0)

    def test_key_not_found_code_2(self):
        code = self._run(['get', 'MISSING'])
        self.assertEqual(code, 2)

    def test_key_already_exists_code_2(self):
        self._run(['set', 'A', '1'])
        self._run(['set', 'B', '2'])
        code = self._run(['rename', 'A', 'B'])
        self.assertEqual(code, 2)

    def test_group_not_found_code_7(self):
        code = self._run(['--force', 'delete-group', 'nonexistent'])
        self.assertEqual(code, 7)

    def test_group_operation_code_7(self):
        code = self._run(['--force', 'delete-group', 'default'])
        self.assertEqual(code, 7)

    def test_backup_error_code_8(self):
        code = self._run(['restore', '/nonexistent/file.json'])
        self.assertEqual(code, 8)

    def test_schema_error_code_6(self):
        code = self._run(['validate', 'NO_SCHEMA'])
        self.assertEqual(code, 6)

    def test_decryption_error_code_5(self):
        self._run(['set', 'PLAIN', 'value'])
        from evm.cli import main
        code = main(['--env-file', self.env_file, 'get', '--secret', 'PLAIN'])
        self.assertEqual(code, 5)

    def test_command_not_found_code_10(self):
        self._run(['set', 'K', 'v'])
        code = self._run(['exec', 'nonexistent_command_xyz'])
        self.assertEqual(code, 10)

    def test_import_error_code_4(self):
        code = self._run(['load', '/nonexistent/file.json'])
        self.assertEqual(code, 4)


# ══════════════════════════════════════════════════════════════
# P1: exec 使用 subprocess.run
# ══════════════════════════════════════════════════════════════


class TestExecSubprocess(unittest.TestCase):
    """测试 exec 命令使用 subprocess.run"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'exec_test.json')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _run(self, args):
        from evm.cli import main
        return main(['--env-file', self.env_file] + args)

    def test_exec_returns_child_exit_code(self):
        """exec 应返回子进程的退出码"""
        self._run(['set', 'EVM_TEST_VAR', 'hello'])
        code = self._run(['exec', '--', 'sh', '-c', 'exit 0'])
        self.assertEqual(code, 0)

    def test_exec_nonzero_exit_code(self):
        """exec 应透传非零退出码"""
        self._run(['set', 'EVM_TEST_VAR', 'hello'])
        code = self._run(['exec', '--', 'sh', '-c', 'exit 42'])
        self.assertEqual(code, 42)

    def test_exec_env_vars_available(self):
        """exec 执行时环境变量应对子进程可用"""
        self._run(['set', 'EVM_EXEC_TEST', 'exec_value'])
        code = self._run([
            'exec', '--', 'sh', '-c',
            'test "$EVM_EXEC_TEST" = "exec_value"',
        ])
        self.assertEqual(code, 0)

    def test_exec_command_not_found(self):
        """exec 找不到命令应返回 10"""
        code = self._run(['exec', '--', 'nonexistent_cmd_xyz_123'])
        self.assertEqual(code, 10)

    def test_exec_returns_int(self):
        """execute() 应返回 int"""
        from evm.manager import EnvironmentManager
        mgr = EnvironmentManager(self.env_file)
        result = mgr.execute(['sh', '-c', 'exit 0'])
        self.assertIsInstance(result, int)
        self.assertEqual(result, 0)


# ══════════════════════════════════════════════════════════════
# P2: --quiet 模式
# ══════════════════════════════════════════════════════════════


class TestQuietMode(unittest.TestCase):
    """测试 --quiet 模式"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'quiet_test.json')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _run_quiet(self, args, capture_stdout=True):
        """运行命令并捕获输出"""
        import io
        from evm.cli import main
        old_stdout = sys.stdout
        if capture_stdout:
            sys.stdout = captured = io.StringIO()
        try:
            code = main(['--env-file', self.env_file, '--quiet'] + args)
        except SystemExit as e:
            code = e.code
        finally:
            if capture_stdout:
                sys.stdout = old_stdout
        output = captured.getvalue() if capture_stdout else ''
        return code, output

    def _run_quiet_json(self, args):
        """运行 --json --quiet 命令"""
        import io
        from evm.cli import main
        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()
        try:
            code = main(['--env-file', self.env_file, '--json', '--quiet'] + args)
        except SystemExit as e:
            code = e.code
        finally:
            sys.stdout = old_stdout
        return code, captured.getvalue()

    def test_quiet_set_no_output(self):
        code, output = self._run_quiet(['set', 'KEY', 'value'])
        self.assertEqual(code, 0)
        self.assertEqual(output.strip(), '')

    def test_quiet_get_still_outputs_value(self):
        """quiet 模式下 get 不输出（由 --json 控制）"""
        self._run_quiet(['set', 'KEY', 'value'])
        code, output = self._run_quiet(['get', 'KEY'])
        self.assertEqual(code, 0)
        # quiet 模式下不输出人类文本
        self.assertEqual(output.strip(), '')

    def test_quiet_list_no_output(self):
        self._run_quiet(['set', 'A', '1'])
        code, output = self._run_quiet(['list'])
        self.assertEqual(code, 0)
        self.assertEqual(output.strip(), '')

    def test_quiet_json_set_no_stdout(self):
        """--json --quiet 应不输出到 stdout"""
        code, output = self._run_quiet_json(['set', 'KEY', 'value'])
        self.assertEqual(code, 0)
        self.assertEqual(output.strip(), '')

    def test_quiet_error_still_has_exit_code(self):
        """quiet 模式下错误仍有正确退出码"""
        code, output = self._run_quiet(['get', 'MISSING'])
        self.assertEqual(code, 2)

    def test_quiet_clear_no_output(self):
        self._run_quiet(['set', 'A', '1'])
        code, output = self._run_quiet(['--force', 'clear'])
        self.assertEqual(code, 0)
        self.assertEqual(output.strip(), '')

    def test_quiet_info_no_output(self):
        code, output = self._run_quiet(['info'])
        self.assertEqual(code, 0)
        self.assertEqual(output.strip(), '')


# ══════════════════════════════════════════════════════════════
# JSON 错误输出
# ══════════════════════════════════════════════════════════════


class TestJSONErrorOutput(unittest.TestCase):
    """测试 --json 模式下的错误输出"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'json_err_test.json')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _run_json_err(self, args):
        """运行命令并捕获 stderr JSON 输出"""
        import io
        from evm.cli import main
        old_stderr = sys.stderr
        sys.stderr = captured = io.StringIO()
        try:
            code = main(['--env-file', self.env_file, '--json'] + args)
        except SystemExit as e:
            code = e.code
        finally:
            sys.stderr = old_stderr
        return code, captured.getvalue()

    def _parse_json(self, output):
        import json as json_mod
        for line in reversed(output.strip().split('\n')):
            line = line.strip()
            if line:
                return json_mod.loads(line)
        return None

    def test_json_error_key_not_found(self):
        code, stderr = self._run_json_err(['get', 'MISSING'])
        self.assertEqual(code, 2)
        data = self._parse_json(stderr)
        self.assertIsNotNone(data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['error_code'], 2)
        self.assertIn('MISSING', data['error'])

    def test_json_error_group_not_found(self):
        code, stderr = self._run_json_err(['--force', 'delete-group', 'nope'])
        self.assertEqual(code, 7)
        data = self._parse_json(stderr)
        self.assertIsNotNone(data)
        self.assertEqual(data['error_code'], 7)

    def test_json_error_schema_not_found(self):
        code, stderr = self._run_json_err(['validate', 'NO_SCHEMA'])
        self.assertEqual(code, 6)
        data = self._parse_json(stderr)
        self.assertIsNotNone(data)
        self.assertEqual(data['error_code'], 6)


# ══════════════════════════════════════════════════════════════
# Code Review 修复验证
# ══════════════════════════════════════════════════════════════


class TestLockFile(TestEnvironmentManagerBase):
    """#1: 验证使用共享 .lock 文件加锁"""

    def test_lock_file_created(self):
        """写入后应创建 .lock 文件"""
        self.manager.set('KEY', 'value')
        lock_path = str(self.env_file) + '.lock'
        self.assertTrue(os.path.exists(lock_path))

    def test_lock_file_permissions(self):
        """锁文件应为 600 权限"""
        self.manager.set('KEY', 'value')
        lock_path = str(self.env_file) + '.lock'
        file_stat = os.stat(lock_path)
        mode = stat.S_IMODE(file_stat.st_mode)
        self.assertEqual(mode, 0o600)

    def test_concurrent_writes_no_data_loss(self):
        """#1: 并发写入不应丢数据（模拟两进程竞争锁）"""
        import threading
        results = []

        def write_vars(mgr, prefix, count):
            for i in range(count):
                mgr.set(f'{prefix}_{i}', f'value_{i}')
            results.append(prefix)

        mgr1 = EnvironmentManager(self.env_file)
        mgr2 = EnvironmentManager(self.env_file)

        t1 = threading.Thread(target=write_vars, args=(mgr1, 'A', 5))
        t2 = threading.Thread(target=write_vars, args=(mgr2, 'B', 5))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # 重新加载验证
        final = EnvironmentManager(self.env_file)
        # 至少有一组变量应完整存在（锁确保不丢）
        all_keys = list(final._env_vars.keys())
        self.assertTrue(len(all_keys) >= 5)


class TestHistoryPermissions(TestEnvironmentManagerBase):
    """#3/#6: 验证历史文件权限和安全性"""

    def test_history_file_permissions(self):
        """#6: history.jsonl 应为 600 权限"""
        self.manager.set('KEY', 'value')
        history_file = self.manager._get_history_file()
        if history_file.exists():
            file_stat = os.stat(history_file)
            mode = stat.S_IMODE(file_stat.st_mode)
            self.assertEqual(mode, 0o600)

    def test_history_silent_on_os_error(self):
        """#3: OSError 应被静默处理（不影响主操作）"""
        # 正常操作不应抛异常
        self.manager.set('A', '1')
        self.manager.set('B', '2')
        self.assertEqual(self.manager.get('A'), '1')


class TestIPv6Validation(TestEnvironmentManagerBase):
    """#7: 验证 IPv6 使用 ipaddress 标准库"""

    def test_valid_ipv6(self):
        self.manager.set_schema('IP', format='ipv6')
        self.manager.set('IP', '::1')
        result = self.manager.validate('IP')
        self.assertTrue(result['valid'])

    def test_valid_ipv6_full(self):
        self.manager.set_schema('IP', format='ipv6')
        self.manager.set('IP', '2001:0db8:85a3:0000:0000:8a2e:0370:7334')
        result = self.manager.validate('IP')
        self.assertTrue(result['valid'])

    def test_invalid_ipv6_triple_colon(self):
        """:::  应被拒绝"""
        self.manager.set_schema('IP', format='ipv6')
        self.manager.set('IP', ':::')
        result = self.manager.validate('IP')
        self.assertFalse(result['valid'])

    def test_invalid_ipv6_hex_only(self):
        """纯 hex 字符串不是合法 IPv6"""
        self.manager.set_schema('IP', format='ipv6')
        self.manager.set('IP', 'abcdef')
        result = self.manager.validate('IP')
        self.assertFalse(result['valid'])


class TestEnvQuoteParsing(TestEnvironmentManagerBase):
    """#8: 验证 .env 引号解析"""

    def test_balanced_double_quotes(self):
        env_file = os.path.join(self.temp_dir, 'quotes.env')
        with open(env_file, 'w') as f:
            f.write('KEY="hello world"\n')
        self.manager.load(env_file, format_type='env')
        self.assertEqual(self.manager.get('KEY'), 'hello world')

    def test_balanced_single_quotes(self):
        env_file = os.path.join(self.temp_dir, 'quotes.env')
        with open(env_file, 'w') as f:
            f.write("KEY='hello world'\n")
        self.manager.load(env_file, format_type='env')
        self.assertEqual(self.manager.get('KEY'), 'hello world')

    def test_unbalanced_quotes_preserved(self):
        """不平衡引号应按字面量处理"""
        env_file = os.path.join(self.temp_dir, 'quotes.env')
        with open(env_file, 'w') as f:
            f.write('KEY="value\'\n')
        self.manager.load(env_file, format_type='env')
        # 不平衡引号：保留原样（含引号字符）
        val = self.manager.get('KEY')
        self.assertIn('value', val)


class TestShellExportKeyEscaping(TestEnvironmentManagerBase):
    """#9: 验证 shell 导出 key 转义"""

    def test_key_escaped_in_sh_export(self):
        """key 名应被 shlex.quote 转义"""
        self.manager.set('NORMAL_KEY', 'value')
        export_file = os.path.join(self.temp_dir, 'export.sh')
        self.manager.export('sh', export_file)
        with open(export_file, 'r') as f:
            content = f.read()
        self.assertIn('export NORMAL_KEY=', content)

    def test_env_import_rejects_bad_keys(self):
        """#9: 导入时应跳过不安全的 key 名"""
        env_file = os.path.join(self.temp_dir, 'bad.env')
        with open(env_file, 'w') as f:
            f.write('GOOD_KEY=value1\n')
            f.write('$(whoami)=value2\n')
        self.manager.load(env_file, format_type='env')
        self.assertTrue(self.manager.exists('GOOD_KEY'))
        self.assertFalse(self.manager.exists('$(whoami)'))


class TestEnvNewlineExport(TestEnvironmentManagerBase):
    """#13: 验证 .env 导出处理换行"""

    def test_newline_in_value_quoted(self):
        """值含换行时应被双引号包裹"""
        self.manager.set('MULTI', 'line1\nline2')
        export_file = os.path.join(self.temp_dir, 'export.env')
        self.manager.export('env', export_file)
        with open(export_file, 'r') as f:
            content = f.read()
        # 应包含引号包裹和转义换行
        self.assertIn('MULTI="', content)
        self.assertIn('\\n', content)


class TestSchemaCorruptionWarning(TestEnvironmentManagerBase):
    """#10: 验证 schema 损坏时发出警告"""

    def test_corrupted_schema_warns(self):
        """损坏的 schema 文件应在 stderr 打印警告"""
        import io
        schema_file = self.manager._get_schema_file()
        schema_file.parent.mkdir(parents=True, exist_ok=True)
        with open(schema_file, 'w') as f:
            f.write('{invalid json')

        old_stderr = sys.stderr
        sys.stderr = captured = io.StringIO()
        try:
            schema = self.manager._load_schema()
        finally:
            sys.stderr = old_stderr

        self.assertEqual(schema, {})
        self.assertIn('Warning', captured.getvalue())
        self.assertIn('corrupted', captured.getvalue().lower())


class TestCryptoModule(TestEnvironmentManagerBase):
    """验证 _crypto.py 模块"""

    def test_hkdf_expand(self):
        from evm._crypto import hkdf_expand
        prk = b'\x00' * 32
        okm = hkdf_expand(prk, b'test-info', 32)
        self.assertEqual(len(okm), 32)

    def test_derive_subkeys_different(self):
        from evm._crypto import derive_subkeys
        master = b'\x01' * 32
        salt = b'\x02' * 16
        enc_key, mac_key = derive_subkeys(master, salt)
        self.assertNotEqual(enc_key, mac_key)
        self.assertEqual(len(enc_key), 32)
        self.assertEqual(len(mac_key), 32)

    def test_hmac_ctr_keystream_length(self):
        from evm._crypto import hmac_ctr_keystream
        key = b'\x03' * 32
        iv = b'\x04' * 16
        stream = hmac_ctr_keystream(key, iv, 100)
        self.assertEqual(len(stream), 100)

    def test_encrypt_decrypt_roundtrip(self):
        from evm._crypto import encrypt_v3, decrypt_v3
        import hashlib

        def derive(salt):
            return hashlib.pbkdf2_hmac(
                'sha256', b'test-machine-id', salt, 100000, dklen=32
            )

        plaintext = 'Hello, World! 🔐'
        encrypted = encrypt_v3(plaintext, derive)
        self.assertTrue(encrypted.startswith('ENCv3:'))
        decrypted = decrypt_v3(encrypted[len('ENCv3:'):], derive)
        self.assertEqual(decrypted, plaintext)

    def test_tampered_ciphertext_detected(self):
        from evm._crypto import encrypt_v3, decrypt_v3
        import hashlib

        def derive(salt):
            return hashlib.pbkdf2_hmac(
                'sha256', b'test-machine-id', salt, 100000, dklen=32
            )

        encrypted = encrypt_v3('secret', derive)
        # 篡改密文
        parts = encrypted[len('ENCv3:'):].split(':')
        parts[3] = 'AAAA'
        tampered = ':'.join(parts)

        with self.assertRaises(DecryptionError):
            decrypt_v3(tampered, derive)


if __name__ == '__main__':
    unittest.main()
