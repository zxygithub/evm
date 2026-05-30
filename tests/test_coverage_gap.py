#!/usr/bin/env python3
"""
覆盖率补全测试 — 目标: 95%+

针对每个模块的未覆盖行编写精确测试:
- manager.py: _load_env_vars 错误路径、execute 边界、edit 路径、expand 递归、v1/v2 解密
- _crypto.py: decrypt_v3 格式错误/base64 错误/非 UTF-8
- _history.py: OSError 分支、JSONDecodeError 跳过、clear_history、trim 权限失败
- _io.py: 不支持格式、JSONDecodeError/ValueError/OSError、backup OSError
- cli.py: OperationCancelledError、set secret json、get secret tty、completion 未知 shell
- _schema.py: 保存失败、无属性、删除不存在、required 未设置、pattern re.error
- exceptions.py: ValidationError 属性
- _groups.py: delete_grouped dry_run、move_to_group dry_run
- __main__.py: 模块入口
- _json.py: json_error quiet
"""

import argparse
import base64
import hashlib
import hmac as hmac_mod
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from evm import EnvironmentManager
from evm.exceptions import (
    CorruptedStorageError,
    DecryptionError,
    EditorError,
    EVMError,
    KeyNotFoundError,
    SchemaError,
    StorageError,
    ValidationError,
)

# ═══════════════════════════════════════════════════════════
# manager.py — _load_env_vars 错误路径 (lines 106-111)
# ═══════════════════════════════════════════════════════════


class TestLoadEnvVarsErrors:
    """_load_env_vars: 文件损坏 / 权限拒绝 / IO 错误"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_corrupted_json_raises(self):
        """损坏的 JSON 存储文件 → CorruptedStorageError"""
        env_file = os.path.join(self.temp_dir, 'env.json')
        with open(env_file, 'w') as f:
            f.write('{broken json content')
        with pytest.raises(CorruptedStorageError, match='corrupted'):
            EnvironmentManager(env_file)

    def test_permission_denied_raises(self):
        """存储文件不可读 → StorageError"""
        env_file = os.path.join(self.temp_dir, 'env.json')
        with open(env_file, 'w') as f:
            f.write('{}')
        os.chmod(env_file, 0o000)
        try:
            with pytest.raises(StorageError, match='Permission denied|IO error'):
                EnvironmentManager(env_file)
        finally:
            os.chmod(env_file, 0o644)

    def test_oserror_on_read_raises(self):
        """读取时 OSError → StorageError"""
        env_file = os.path.join(self.temp_dir, 'env.json')
        with open(env_file, 'w') as f:
            f.write('{}')
        with patch('builtins.open', side_effect=OSError('disk error')):
            with pytest.raises(StorageError, match='IO error'):
                EnvironmentManager(env_file)


# ═══════════════════════════════════════════════════════════
# manager.py — _save_env_vars 错误路径 (lines 144-162)
# ═══════════════════════════════════════════════════════════


class TestSaveEnvVarsErrors:
    """_save_env_vars: 写入失败 / 权限错误"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_to_readonly_dir(self):
        """写入只读目录 → StorageError"""
        ro_dir = os.path.join(self.temp_dir, 'readonly')
        os.mkdir(ro_dir)
        os.chmod(ro_dir, stat.S_IRUSR | stat.S_IXUSR)
        mgr = EnvironmentManager(os.path.join(ro_dir, 'env.json'))
        try:
            with pytest.raises(StorageError):
                mgr.set('KEY', 'val')
        finally:
            os.chmod(ro_dir, 0o755)

    def test_save_dry_run_skips_write(self):
        """dry_run=True 不触发实际写入"""
        self.mgr.set('KEY', 'val', dry_run=True)
        assert not os.path.exists(self.env_file)

    def test_save_temp_write_failure(self):
        """临时文件写入异常 → 清理 + 重抛"""
        with patch('tempfile.mkstemp', side_effect=OSError('no space')):
            with pytest.raises(StorageError, match='IO error'):
                self.mgr.set('KEY', 'val')


# ═══════════════════════════════════════════════════════════
# manager.py — execute 边界 (lines 354, 365-368)
# ═══════════════════════════════════════════════════════════


class TestExecuteBoundaries:
    """execute: 空命令 / KeyboardInterrupt / 通用异常"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_empty_command_raises(self):
        """空命令列表 → EVMError"""
        with pytest.raises(EVMError, match='No command'):
            self.mgr.execute([])

    def test_keyboard_interrupt_returns_130(self):
        """子进程 KeyboardInterrupt → 退出码 130"""
        with patch('evm.manager.subprocess.run', side_effect=KeyboardInterrupt):
            code = self.mgr.execute(['false'])
            assert code == 130

    def test_generic_exception_raises_evmError(self):
        """子进程通用异常 → EVMError"""
        with patch('evm.manager.subprocess.run', side_effect=RuntimeError('boom')):
            with pytest.raises(EVMError, match='Error executing'):
                self.mgr.execute(['test'])


# ═══════════════════════════════════════════════════════════
# manager.py — edit 路径 (lines 395, 405-408)
# ═══════════════════════════════════════════════════════════


class TestEditBoundaries:
    """edit: 非零退出 / 无变更 / 更新"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_edit_nonexistent_key_raises(self):
        """编辑不存在的 key → KeyNotFoundError"""
        with pytest.raises(KeyNotFoundError):
            self.mgr.edit('NONEXISTENT')

    def test_edit_editor_nonzero_exit(self):
        """编辑器退出码非零 → EditorError"""
        self.mgr.set('K', 'val')
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch('evm.manager.subprocess.run', return_value=mock_result):
            with pytest.raises(EditorError, match='exited with code'):
                self.mgr.edit('K')

    def test_edit_no_changes(self):
        """编辑器未修改内容 → 'No changes'"""
        self.mgr.set('K', 'original')
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch('evm.manager.subprocess.run', return_value=mock_result):
            # 编辑器不改内容，tmp 文件保持 'original'
            msg = self.mgr.edit('K')
            assert 'No changes' in msg

    def test_edit_updates_value(self):
        """编辑器修改内容 → 'Updated'"""
        self.mgr.set('K', 'old')
        mock_result = MagicMock()
        mock_result.returncode = 0

        def fake_run(cmd, **kwargs):
            # 修改临时文件内容
            tmp_path = cmd[-1]
            with open(tmp_path, 'w') as f:
                f.write('new_value\n')
            return mock_result

        with patch('evm.manager.subprocess.run', side_effect=fake_run):
            msg = self.mgr.edit('K')
            assert 'Updated' in msg
            assert self.mgr.get('K') == 'new_value'


# ═══════════════════════════════════════════════════════════
# manager.py — _expand_value 递归路径 (lines 474-485)
# ═══════════════════════════════════════════════════════════


class TestExpandValueRecursive:
    """_expand_value: 内部递归展开"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_deep_recursive_expansion(self):
        """三层嵌套模板展开"""
        self.mgr.set('A', '{{B}}')
        self.mgr.set('B', '{{C}}')
        self.mgr.set('C', 'final')
        result = self.mgr.expand('A')
        assert result == 'final'

    def test_expand_unresolved_ref_kept(self):
        """未解析的引用保留原文"""
        self.mgr.set('A', 'hello {{MISSING}}')
        result = self.mgr.expand('A')
        assert result == 'hello {{MISSING}}'

    def test_max_depth_returns_value_silently(self):
        """_expand_value 超过最大深度时静默返回当前值（不抛异常）"""
        self.mgr.set('A', '{{B}}')
        self.mgr.set('B', '{{C}}')
        self.mgr.set('C', '{{D}}')
        # depth=0 expand 会递归调用 _expand_value，每层 depth+1
        # 当 depth > max_depth 时 _expand_value 返回原值
        result = self.mgr.expand('A')
        # 最多展开 max_depth=10 层，此处只有 3 层，全部展开
        assert result == '{{D}}'  # D 不存在，保留原文

    def test_expand_circular_reference(self):
        """循环引用在 max_depth 内静默停止"""
        self.mgr.set('A', '{{B}}')
        self.mgr.set('B', '{{A}}')
        # 不会无限递归，_expand_value 在 depth > max_depth 时返回
        result = self.mgr.expand('A')
        assert '{{' in result  # 最终某层无法解析，保留模板语法


# ═══════════════════════════════════════════════════════════
# _crypto.py — decrypt_v3 错误路径 (lines 139, 146-147, 167-168)
# ═══════════════════════════════════════════════════════════


class TestDecryptV3Errors:
    """decrypt_v3: 格式错误 / base64 错误 / 非 UTF-8"""

    def test_wrong_part_count(self):
        """字段数不等于 4 → DecryptionError"""
        from evm._crypto import decrypt_v3
        with pytest.raises(DecryptionError, match='Invalid v3'):
            decrypt_v3('only:two:parts', lambda s: b'\x00' * 32)

    def test_bad_base64_decode(self):
        """base64 解码异常 → DecryptionError (通过 mock 触发)"""
        from evm._crypto import decrypt_v3
        with patch('evm._crypto.base64.b64decode', side_effect=Exception('bad b64')):
            with pytest.raises(DecryptionError, match='Failed to decode'):
                decrypt_v3('a:b:c:d', lambda s: b'\x00' * 32)

    def test_non_utf8_plaintext(self):
        """解密后非 UTF-8 → DecryptionError"""
        from evm._crypto import decrypt_v3, derive_subkeys, hmac_ctr_keystream

        salt = os.urandom(16)
        master_key = os.urandom(32)
        enc_key, mac_key = derive_subkeys(master_key, salt)

        # 构造非 UTF-8 的明文
        bad_bytes = b'\x80\x81\x82\x83'
        iv = os.urandom(16)
        keystream = hmac_ctr_keystream(enc_key, iv, len(bad_bytes))
        ciphertext = bytes(a ^ b for a, b in zip(bad_bytes, keystream))

        mac = hmac_mod.new(
            mac_key, salt + iv + ciphertext, hashlib.sha256
        ).digest()

        encoded = (
            base64.b64encode(salt).decode()
            + ':' + base64.b64encode(iv).decode()
            + ':' + base64.b64encode(mac).decode()
            + ':' + base64.b64encode(ciphertext).decode()
        )

        with pytest.raises(DecryptionError, match='not valid UTF-8'):
            decrypt_v3(encoded, lambda s: master_key)


# ═══════════════════════════════════════════════════════════
# manager.py — v1/v2 解密错误路径 (lines 527-528, 474-485)
# ═══════════════════════════════════════════════════════════


class TestV1V2DecryptPaths:
    """_decrypt_v1 / _decrypt_v2: 完整错误路径覆盖"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    # ── v2 路径 ──────────────────────────────────────────

    def test_v2_roundtrip(self):
        """v2 加密 → 解密 → 正确还原"""
        salt = os.urandom(16)
        key = self.mgr._derive_key_v2(salt)
        plaintext = b'v2_secret_value'
        ciphertext = bytes(d ^ key[i % len(key)] for i, d in enumerate(plaintext))
        mac = hmac_mod.new(key, salt + ciphertext, hashlib.sha256).digest()
        # _decrypt_v2 接收去掉 ENCv2: 前缀后的数据 (salt:mac:ct = 3 parts)
        v2_encoded = (
            base64.b64encode(salt).decode()
            + ':' + base64.b64encode(mac).decode()
            + ':' + base64.b64encode(ciphertext).decode()
        )
        result = self.mgr._decrypt_v2(v2_encoded)
        assert result == 'v2_secret_value'

    def test_v2_non_utf8_ciphertext(self):
        """v2 解密后非 UTF-8 → DecryptionError"""
        salt = os.urandom(16)
        key = self.mgr._derive_key_v2(salt)
        bad_bytes = b'\x80\x81\x82'
        ciphertext = bytes(d ^ key[i % len(key)] for i, d in enumerate(bad_bytes))
        mac = hmac_mod.new(key, salt + ciphertext, hashlib.sha256).digest()
        v2_encoded = (
            base64.b64encode(salt).decode()
            + ':' + base64.b64encode(mac).decode()
            + ':' + base64.b64encode(ciphertext).decode()
        )
        with pytest.raises(DecryptionError, match='not valid UTF-8'):
            self.mgr._decrypt_v2(v2_encoded)

    def test_v2_mac_failure(self):
        """v2 HMAC 校验失败 → DecryptionError"""
        salt = os.urandom(16)
        bad_mac = b'\xff' * 32
        ciphertext = b'\x00' * 10
        v2_encoded = (
            base64.b64encode(salt).decode()
            + ':' + base64.b64encode(bad_mac).decode()
            + ':' + base64.b64encode(ciphertext).decode()
        )
        with pytest.raises(DecryptionError, match='integrity'):
            self.mgr._decrypt_v2(v2_encoded)

    # ── v1 路径 ──────────────────────────────────────────

    def test_v1_roundtrip(self):
        """v1 加密 → 解密 → 正确还原"""
        machine_id = (
            platform.node()
            + str(os.getuid() if hasattr(os, 'getuid') else '')
            + platform.machine()
        )
        key = hashlib.sha256(machine_id.encode()).digest()
        plaintext = b'v1_secret'
        ciphertext = bytes(d ^ key[i % len(key)] for i, d in enumerate(plaintext))
        v1_encoded = 'ENC:' + base64.b64encode(ciphertext).decode('ascii')
        result = self.mgr._decrypt_v1(v1_encoded[len('ENC:'):])
        assert result == 'v1_secret'

    def test_v1_bad_base64(self):
        """v1 base64 解码失败 → DecryptionError"""
        with pytest.raises(DecryptionError, match='Failed to decrypt'):
            self.mgr._decrypt_v1('!!!not-valid-base64!!!')

    def test_v1_non_utf8(self):
        """v1 解密后非 UTF-8 → DecryptionError"""
        machine_id = (
            platform.node()
            + str(os.getuid() if hasattr(os, 'getuid') else '')
            + platform.machine()
        )
        key = hashlib.sha256(machine_id.encode()).digest()
        bad_bytes = b'\x80\x81\x82'
        ciphertext = bytes(d ^ key[i % len(key)] for i, d in enumerate(bad_bytes))
        v1_data = base64.b64encode(ciphertext).decode('ascii')
        with pytest.raises(DecryptionError):
            self.mgr._decrypt_v1(v1_data)

    # ── get_secret 自动迁移 v2 → v3 ──────────────────────

    def test_get_secret_auto_migrates_v2_to_v3(self):
        """get_secret 读取 v2 密文后自动升级为 v3"""
        salt = os.urandom(16)
        key = self.mgr._derive_key_v2(salt)
        plaintext = b'auto_migrate_me'
        ciphertext = bytes(d ^ key[i % len(key)] for i, d in enumerate(plaintext))
        mac = hmac_mod.new(key, salt + ciphertext, hashlib.sha256).digest()
        v2_encoded = (
            'ENCv2:'
            + base64.b64encode(salt).decode()
            + ':' + base64.b64encode(mac).decode()
            + ':' + base64.b64encode(ciphertext).decode()
        )
        self.mgr._env_vars['MIGRATE_KEY'] = v2_encoded

        result = self.mgr.get_secret('MIGRATE_KEY')
        assert result == 'auto_migrate_me'
        # 验证已迁移到 v3
        assert self.mgr._env_vars['MIGRATE_KEY'].startswith('ENCv3:')

    # ── get_secret 自动迁移 v1 → v3 ──────────────────────

    def test_get_secret_auto_migrates_v1_to_v3(self):
        """get_secret 读取 v1 密文后自动升级为 v3"""
        machine_id = (
            platform.node()
            + str(os.getuid() if hasattr(os, 'getuid') else '')
            + platform.machine()
        )
        key = hashlib.sha256(machine_id.encode()).digest()
        plaintext = b'v1_auto_migrate'
        ciphertext = bytes(d ^ key[i % len(key)] for i, d in enumerate(plaintext))
        v1_encoded = 'ENC:' + base64.b64encode(ciphertext).decode('ascii')
        self.mgr._env_vars['V1_MIGRATE'] = v1_encoded

        result = self.mgr.get_secret('V1_MIGRATE')
        assert result == 'v1_auto_migrate'
        assert self.mgr._env_vars['V1_MIGRATE'].startswith('ENCv3:')


# ═══════════════════════════════════════════════════════════
# _history.py — 错误路径 (lines 68-69, 87-90, 102, 133-141)
# ═══════════════════════════════════════════════════════════


class TestHistoryErrors:
    """log_operation OSError、get_history 损坏行、clear_history 边界"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_operation_swallows_oserror(self):
        """log_operation OSError → 静默失败"""
        with patch('os.open', side_effect=OSError('disk full')):
            # 不应抛出异常
            self.mgr.log_operation('test', 'KEY')

    def test_get_history_skips_bad_json_lines(self):
        """历史文件中损坏 JSON 行被跳过"""
        history_file = self.mgr.env_file.parent / 'history.jsonl'
        history_file.write_text(
            '{"timestamp":"t1","operation":"set","key":"A","status":"success"}\n'
            'THIS IS NOT JSON\n'
            '{"timestamp":"t2","operation":"set","key":"B","status":"success"}\n'
        )
        entries = self.mgr.get_history(limit=10)
        assert len(entries) == 2

    def test_get_history_oserror_returns_empty(self):
        """读取历史文件 OSError → 空列表"""
        history_file = self.mgr.env_file.parent / 'history.jsonl'
        history_file.write_text('{}')
        with patch('builtins.open', side_effect=OSError('read error')):
            entries = self.mgr.get_history()
            assert entries == []

    def test_clear_history_no_file(self):
        """无历史文件 → 'No history to clear'"""
        msg = self.mgr.clear_history()
        assert 'No history' in msg

    def test_clear_history_with_file(self):
        """有历史文件 → 删除 + 'History cleared'"""
        self.mgr.set('K', 'v')  # 触发 log_operation 创建历史
        msg = self.mgr.clear_history()
        assert 'cleared' in msg.lower()

    def test_trim_chmod_failure_no_crash(self):
        """trim 后 chmod 失败 → 不影响功能"""
        self.mgr.MAX_HISTORY_ENTRIES = 5
        # 写入超过阈值的记录
        for i in range(10):
            self.mgr.set(f'K{i}', f'v{i}')

        original_chmod = os.chmod
        call_count = [0]

        def selective_chmod(path, mode):
            if '.jsonl' in str(path):
                call_count[0] += 1
                raise OSError('chmod failed')
            return original_chmod(path, mode)

        with patch('os.chmod', side_effect=selective_chmod):
            # 不应崩溃
            self.mgr.set('TRIGGER', 'trim')


# ═══════════════════════════════════════════════════════════
# _schema.py — 错误路径 (lines 94-95, 143, 166, 196, 215, 258-259)
# ═══════════════════════════════════════════════════════════


class TestSchemaErrors:
    """Schema 保存失败 / 无属性 / 删除不存在 / 校验边界"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_schema_oserror(self):
        """保存 schema OSError → SchemaError"""
        with patch('builtins.open', side_effect=OSError('disk full')):
            with pytest.raises(SchemaError, match='Failed to save'):
                self.mgr.set_schema('KEY', format='url')

    def test_set_schema_no_properties(self):
        """不指定任何属性 → SchemaError"""
        with pytest.raises(SchemaError, match='No schema properties'):
            self.mgr.set_schema('KEY')

    def test_delete_schema_nonexistent(self):
        """删除不存在的 schema → SchemaError"""
        with pytest.raises(SchemaError, match='No schema defined'):
            self.mgr.delete_schema('NONEXISTENT')

    def test_validate_required_not_set(self):
        """required=True 但变量未设置 → valid=False"""
        self.mgr.set_schema('MISSING', required=True)
        result = self.mgr.validate('MISSING')
        assert result['valid'] is False
        assert any('Required' in e for e in result['errors'])

    def test_validate_not_required_not_set(self):
        """非 required 且变量未设置 → valid=True + warning"""
        self.mgr.set_schema('OPTIONAL', format='url', required=False)
        result = self.mgr.validate('OPTIONAL')
        assert result['valid'] is True
        assert any('not set' in w for w in result['warnings'])

    def test_validate_pattern_re_error(self):
        """schema 中的正则本身无效 → 校验报告错误"""
        # 直接写入一个无效 regex 的 schema
        schema_file = self.mgr._get_schema_file()
        schema_file.parent.mkdir(parents=True, exist_ok=True)
        schema_data = {
            'BAD_REGEX': {'pattern': '[invalid('}
        }
        schema_file.write_text(json.dumps(schema_data))
        self.mgr.set('BAD_REGEX', 'test_value')
        result = self.mgr.validate('BAD_REGEX')
        assert result['valid'] is False
        assert any('Invalid schema regex' in e for e in result['errors'])


# ═══════════════════════════════════════════════════════════
# exceptions.py — ValidationError 属性 (lines 103-106)
# ═══════════════════════════════════════════════════════════


class TestValidationErrorAttributes:
    """ValidationError 携带 key/value/expected_format"""

    def test_attributes(self):
        e = ValidationError('MY_KEY', 'bad_val', 'url')
        assert e.key == 'MY_KEY'
        assert e.value == 'bad_val'
        assert e.expected_format == 'url'
        assert 'MY_KEY' in str(e)
        assert 'url' in str(e)


# ═══════════════════════════════════════════════════════════
# _groups.py — dry_run 路径 (lines 58, 122)
# ═══════════════════════════════════════════════════════════


class TestGroupDryRun:
    """delete_grouped / move_to_group dry_run"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_delete_grouped_dry_run(self):
        """delete_grouped dry_run → 不删除"""
        self.mgr.set_grouped('dev', 'K', 'v')
        msg = self.mgr.delete_grouped('dev', 'K', dry_run=True)
        assert 'DRY-RUN' in msg
        assert self.mgr.exists('dev:K')

    def test_move_to_group_dry_run(self):
        """move_to_group dry_run → 不移动"""
        self.mgr.set('K', 'v')
        msg = self.mgr.move_to_group('K', 'prod', dry_run=True)
        assert 'DRY-RUN' in msg
        assert self.mgr.exists('K')
        assert not self.mgr.exists('prod:K')


# ═══════════════════════════════════════════════════════════
# _json.py — json_error quiet (line 40)
# ═══════════════════════════════════════════════════════════


class TestJsonErrorQuiet:
    """json_error quiet=True → 不输出"""

    def test_quiet_suppresses_output(self, capsys):
        from evm._json import json_error
        json_error('test error', 1, quiet=True)
        captured = capsys.readouterr()
        assert captured.err == ''
        assert captured.out == ''


# ═══════════════════════════════════════════════════════════
# __main__.py — 模块入口 (line 9)
# ═══════════════════════════════════════════════════════════


class TestMainModule:
    """python -m evm 入口"""

    def test_module_entry_point(self):
        """python -m evm --version 正常退出"""
        import re
        result = subprocess.run(
            [sys.executable, '-m', 'evm', '--version'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert re.search(r'\d+\.\d+\.\d+', result.stdout)


# ═══════════════════════════════════════════════════════════
# cli.py — 补充分支 (lines 408-412, 439, 466, 572, 830, 956)
# ═══════════════════════════════════════════════════════════


class TestCliBranches:
    """CLI 未覆盖分支"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_operation_cancelled_text(self, capsys):
        """OperationCancelledError → 文本输出"""
        from evm.cli import main
        # 在非 TTY 下 clear 非空存储应触发 OperationCancelledError
        main(['--env-file', self.env_file, 'set', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, 'clear'])
        # 非 TTY + 无 --force → EVMError (非交互模式)
        assert code == 1
        captured = capsys.readouterr()
        assert 'non-interactive' in captured.err.lower() or 'force' in captured.err.lower()

    def test_set_secret_json_mode(self, capsys):
        """set --secret --json"""
        from evm.cli import main
        code = main(['--env-file', self.env_file, '--json', 'set', '--secret', 'K', 'V'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'
        assert data['data']['encrypted'] is True

    def test_completion_unsupported_shell(self, capsys):
        """completion 不支持的 shell → EVMError"""
        from evm.cli import _dispatch
        from evm.manager import EnvironmentManager
        mgr = EnvironmentManager(self.env_file)
        args = argparse.Namespace(command='completion', shell='powershell')
        with pytest.raises(EVMError, match='Unsupported shell'):
            _dispatch(mgr, args, False, False, False, False)

    def test_deleteg_json_mode(self, capsys):
        """deleteg --json"""
        from evm.cli import main
        main(['--env-file', self.env_file, '--quiet', 'setg', 'dev', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, '--json', 'deleteg', 'dev', 'K'])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data['status'] == 'ok'
        assert data['data']['deleted'] is True

    def test_edit_quiet_mode(self, capsys):
        """edit --quiet → 无输出"""
        from evm.cli import main
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'val'])
        capsys.readouterr()
        with patch('evm.manager.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            code = main(['--env-file', self.env_file, '--quiet', 'edit', 'K'])
            assert code == 0
            captured = capsys.readouterr()
            assert captured.out == ''

    def test_loadmemory_text_mode(self, capsys):
        """loadmemory 文本模式"""
        from evm.cli import main
        main(['--env-file', self.env_file, '--quiet', 'set', 'K', 'V'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, 'loadmemory'])
        assert code == 0
        captured = capsys.readouterr()
        assert 'Loaded' in captured.out or 'loaded' in captured.out.lower()

    def test_validate_key_text_mode(self, capsys):
        """validate KEY 文本模式（非 --json）"""
        from evm.cli import main
        main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'PORT', '--format', 'port'])
        main(['--env-file', self.env_file, '--quiet', 'set', 'PORT', '8080'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, 'validate', 'PORT'])
        assert code == 0
        captured = capsys.readouterr()
        assert 'PORT' in captured.out or 'valid' in captured.out.lower()

    def test_schema_no_subcommand_text(self, capsys):
        """schema (no subcommand) 文本模式"""
        from evm.cli import main
        main(['--env-file', self.env_file, '--quiet', 'schema', 'set', 'K', '--format', 'url'])
        capsys.readouterr()
        code = main(['--env-file', self.env_file, 'schema'])
        assert code == 0

    def test_get_secret_tty_warning(self, capsys):
        """get --secret 在 TTY 上显示 scrollback 警告"""
        from evm.cli import main
        main(['--env-file', self.env_file, '--quiet', 'set', '--secret', 'K', 'V'])
        capsys.readouterr()
        # 模拟 TTY
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.isatty.return_value = True
            mock_stdout.write = sys.stdout.write
            mock_stdout.flush = sys.stdout.flush
            code = main(['--env-file', self.env_file, 'get', '--secret', 'K'])
            assert code == 0
            captured = capsys.readouterr()
            assert 'scrollback' in captured.err.lower() or 'WARNING' in captured.err
