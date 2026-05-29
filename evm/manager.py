#!/usr/bin/env python3
"""
EVM 核心业务逻辑

EnvironmentManager 类通过 mixin 组合提供所有环境变量管理功能。
所有方法返回数据或抛出异常，不做任何 print() 或 sys.exit()。

模块拆分：
- _io.py      → IOMixin（导入导出/备份恢复/diff）
- _groups.py  → GroupMixin（分组管理）
- _history.py → HistoryMixin（操作日志）
- _schema.py  → SchemaMixin（变量 schema）
"""

import base64
import fcntl
import hashlib
import hmac
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ._groups import GroupMixin
from ._history import HistoryMixin
from ._io import IOMixin
from ._schema import SchemaMixin
from .exceptions import (
    CommandNotFoundError,
    CorruptedStorageError,
    DecryptionError,
    EditorError,
    EVMError,
    KeyAlreadyExistsError,
    KeyNotFoundError,
    LockTimeoutError,
    StorageError,
)


class EnvironmentManager(IOMixin, GroupMixin, HistoryMixin, SchemaMixin):
    """环境变量管理器核心类

    通过 mixin 组合获得分组、IO、历史、schema 功能。
    """

    # 加密前缀标识
    SECRET_PREFIX = "ENC:"
    SECRET_V2_PREFIX = "ENCv2:"
    # 模板引用模式 {{VAR_NAME}}
    TEMPLATE_PATTERN = re.compile(r'\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}')
    # 文件锁默认超时（秒）
    LOCK_TIMEOUT = 5.0

    def __init__(
        self,
        env_file: Optional[str] = None,
        lock_timeout: float = LOCK_TIMEOUT,
    ):
        """初始化环境管理器

        Args:
            env_file: 存储文件路径，默认 ~/.evm/env.json
            lock_timeout: 文件锁超时秒数
        """
        if env_file is None:
            self.env_file = Path.home() / '.evm' / 'env.json'
        else:
            self.env_file = Path(env_file)

        self.lock_timeout = lock_timeout
        self.env_file.parent.mkdir(parents=True, exist_ok=True)
        self._env_vars = self._load_env_vars()

    # ── 内部存储 ──────────────────────────────────────────

    def _load_env_vars(self) -> Dict[str, str]:
        """从存储文件加载环境变量

        Raises:
            CorruptedStorageError: JSON 文件损坏
            StorageError: IO 或权限错误
        """
        if not self.env_file.exists():
            return {}
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise CorruptedStorageError(
                f"Storage file is corrupted: {e}. File: {self.env_file}"
            )
        except PermissionError:
            raise StorageError(
                f"Permission denied reading storage file: {self.env_file}"
            )
        except IOError as e:
            raise StorageError(f"IO error reading storage file: {e}")

    def _save_env_vars(self, dry_run: bool = False) -> None:
        """保存环境变量到存储文件（原子写入 + 文件锁超时 + chmod 600）

        P1: 使用 LOCK_NB + 超时重试，替代原来的阻塞式 LOCK_EX。
        """
        if dry_run:
            return

        try:
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=str(self.env_file.parent),
                suffix='.tmp',
                prefix='.env_',
            )
            try:
                with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
                    # P1: 非阻塞锁 + 超时重试
                    self._acquire_lock(f.fileno())
                    try:
                        json.dump(
                            self._env_vars, f, indent=2, ensure_ascii=False
                        )
                        f.flush()
                        os.fsync(f.fileno())
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except LockTimeoutError:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise

            shutil.move(tmp_path, str(self.env_file))
            os.chmod(str(self.env_file), 0o600)

        except LockTimeoutError:
            raise
        except PermissionError:
            raise StorageError(
                f"Permission denied writing to: {self.env_file}"
            )
        except IOError as e:
            raise StorageError(f"IO error writing storage file: {e}")

    def _acquire_lock(self, fd: int) -> None:
        """获取排他文件锁，带超时重试

        Raises:
            LockTimeoutError: 超时未获取锁
        """
        deadline = time.monotonic() + self.lock_timeout
        while time.monotonic() < deadline:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except (IOError, OSError):
                time.sleep(0.05)
        raise LockTimeoutError(str(self.env_file), self.lock_timeout)

    # ── 基本 CRUD ────────────────────────────────────────

    def set(self, key: str, value: str, dry_run: bool = False) -> str:
        """设置环境变量"""
        if dry_run:
            return f"[DRY-RUN] Would set: {key}={value}"
        self._env_vars[key] = value
        self._save_env_vars()
        self.log_operation('set', key, f'value={value}')
        return f"Set: {key}={value}"

    def get(self, key: str) -> str:
        """获取环境变量值

        Raises:
            KeyNotFoundError: 变量不存在
        """
        value = self._env_vars.get(key)
        if value is None:
            raise KeyNotFoundError(key)
        return value

    def delete(self, key: str, dry_run: bool = False) -> str:
        """删除环境变量

        Raises:
            KeyNotFoundError: 变量不存在
        """
        if key not in self._env_vars:
            raise KeyNotFoundError(key)
        if dry_run:
            return f"[DRY-RUN] Would delete: {key} (value={self._env_vars[key]})"
        del self._env_vars[key]
        self._save_env_vars()
        self.log_operation('delete', key)
        return f"Deleted: {key}"

    def exists(self, key: str) -> bool:
        """检查环境变量是否存在"""
        return key in self._env_vars

    def list_vars(
        self,
        pattern: Optional[str] = None,
        group: Optional[str] = None,
        show_groups: bool = False,
        no_prefix: bool = False,
    ) -> Dict[str, str]:
        """列出环境变量

        Raises:
            GroupNotFoundError: 指定的分组不存在
        """
        from .exceptions import GroupNotFoundError

        if group:
            prefix = f"{group}:"
            filtered = {
                k: v for k, v in self._env_vars.items()
                if k.startswith(prefix)
            }
            if not filtered:
                raise GroupNotFoundError(group)
            if no_prefix:
                result = {}
                for key, value in filtered.items():
                    new_key = key[len(prefix):] if key.startswith(prefix) else key
                    result[new_key] = value
                return result
            return filtered
        elif pattern:
            return {
                k: v for k, v in self._env_vars.items()
                if pattern.lower() in k.lower()
            }
        else:
            return dict(self._env_vars)

    def clear(self, dry_run: bool = False, force: bool = False) -> str:
        """清空所有环境变量

        Args:
            force: 跳过确认（CLI 层处理确认逻辑）
        """
        if not self._env_vars:
            return "No environment variables to clear"
        count = len(self._env_vars)
        if dry_run:
            return f"[DRY-RUN] Would clear {count} variables"
        self._env_vars.clear()
        self._save_env_vars()
        self.log_operation('clear', details=f'{count} variables')
        return f"All environment variables cleared ({count} variables)"

    # ── 搜索 ─────────────────────────────────────────────

    def search(self, pattern: str, search_value: bool = False) -> Dict[str, str]:
        """搜索环境变量"""
        results = {}
        for key, value in self._env_vars.items():
            if pattern.lower() in key.lower():
                results[key] = value
            elif search_value and pattern.lower() in str(value).lower():
                results[key] = value
        return results

    # ── 重命名/复制 ──────────────────────────────────────

    def rename(
        self, old_key: str, new_key: str, dry_run: bool = False
    ) -> str:
        """重命名环境变量"""
        if old_key not in self._env_vars:
            raise KeyNotFoundError(old_key)
        if new_key in self._env_vars:
            raise KeyAlreadyExistsError(new_key)
        if dry_run:
            return f"[DRY-RUN] Would rename: {old_key} -> {new_key}"
        value = self._env_vars.pop(old_key)
        self._env_vars[new_key] = value
        self._save_env_vars()
        self.log_operation('rename', old_key, f'-> {new_key}')
        return f"Renamed: {old_key} -> {new_key}"

    def copy(self, src_key: str, dst_key: str, dry_run: bool = False) -> str:
        """复制环境变量"""
        if src_key not in self._env_vars:
            raise KeyNotFoundError(src_key)
        if dry_run:
            return f"[DRY-RUN] Would copy: {src_key} -> {dst_key}"
        self._env_vars[dst_key] = self._env_vars[src_key]
        self._save_env_vars()
        self.log_operation('copy', src_key, f'-> {dst_key}')
        return f"Copied: {src_key} -> {dst_key}"

    # ── 内存加载 ──────────────────────────────────────────

    def load_to_memory(
        self,
        filter_prefix: Optional[str] = None,
        add_evm_prefix: bool = True,
    ) -> Tuple[int, bool, Optional[str]]:
        """加载环境变量到 os.environ"""
        loaded_count = 0
        for key, value in self._env_vars.items():
            if filter_prefix and not key.startswith(filter_prefix):
                continue
            final_key = f"EVM:{key}" if add_evm_prefix else key
            os.environ[final_key] = str(value)
            loaded_count += 1
        return loaded_count, add_evm_prefix, filter_prefix

    # ── 执行命令 ──────────────────────────────────────────

    def execute(self, command: List[str]) -> None:
        """使用环境变量执行命令"""
        if not command:
            raise EVMError("No command specified")

        env_copy = os.environ.copy()
        for key, value in self._env_vars.items():
            env_copy[key] = str(value)

        try:
            os.execvpe(command[0], command, env_copy)
        except FileNotFoundError:
            raise CommandNotFoundError(command[0])
        except Exception as e:
            raise EVMError(f"Error executing command: {e}")

    # ── 编辑器编辑 ────────────────────────────────────────

    def edit(self, key: str) -> str:
        """使用 $EDITOR 编辑变量值"""
        if key not in self._env_vars:
            raise KeyNotFoundError(key)

        editor = os.environ.get('EDITOR', os.environ.get('VISUAL', 'vi'))
        current_value = self._env_vars[key]

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', prefix='evm_edit_', delete=False
        ) as tmp:
            tmp.write(current_value)
            tmp_path = tmp.name

        try:
            result = subprocess.run([editor, tmp_path])
            if result.returncode != 0:
                raise EditorError(
                    f"Editor exited with code {result.returncode}"
                )

            with open(tmp_path, 'r', encoding='utf-8') as f:
                new_value = f.read().rstrip('\n')

            if new_value == current_value:
                return f"No changes made to '{key}'"

            self._env_vars[key] = new_value
            self._save_env_vars()
            self.log_operation('edit', key)
            return f"Updated: {key}"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # ── 工具信息 ──────────────────────────────────────────

    def info(self) -> Dict[str, object]:
        """返回工具元信息"""
        groups = self.list_groups()
        total_vars = len(self._env_vars)
        secret_count = sum(
            1 for v in self._env_vars.values()
            if isinstance(v, str) and (
                v.startswith(self.SECRET_PREFIX)
                or v.startswith(self.SECRET_V2_PREFIX)
            )
        )

        return {
            'version': '1.8.0',
            'author': 'EVM Tool',
            'license': 'MIT',
            'python': sys.version.split()[0],
            'platform': platform.system(),
            'storage_path': str(self.env_file),
            'storage_exists': self.env_file.exists(),
            'total_variables': total_vars,
            'total_groups': len(groups),
            'secret_variables': secret_count,
            'groups': groups,
            'repository': 'https://github.com/zxygithub/evm',
        }

    # ── 模板展开 ──────────────────────────────────────────

    def expand(self, key: str, depth: int = 0, max_depth: int = 10) -> str:
        """展开变量值中的模板引用 {{OTHER_VAR}}"""
        if key not in self._env_vars:
            raise KeyNotFoundError(key)
        if depth > max_depth:
            raise EVMError(
                f"Template expansion exceeded max depth ({max_depth}). "
                f"Possible circular reference."
            )

        value = self._env_vars[key]

        def replace_match(match):
            ref_key = match.group(1)
            if ref_key in self._env_vars:
                ref_val = self._env_vars[ref_key]
                if self.TEMPLATE_PATTERN.search(ref_val):
                    return self._expand_value(
                        ref_val, depth + 1, max_depth
                    )
                return ref_val
            return match.group(0)

        return self.TEMPLATE_PATTERN.sub(replace_match, value)

    def _expand_value(
        self, value: str, depth: int, max_depth: int
    ) -> str:
        """内部：展开字符串中的模板引用"""
        if depth > max_depth:
            return value

        def replace_match(match):
            ref_key = match.group(1)
            if ref_key in self._env_vars:
                return self._expand_value(
                    self._env_vars[ref_key], depth + 1, max_depth
                )
            return match.group(0)

        return self.TEMPLATE_PATTERN.sub(replace_match, value)

    # ── 加密变量（增强版）─────────────────────────────────

    def _get_machine_salt(self) -> bytes:
        """获取机器相关的盐值"""
        machine_id = (
            platform.node()
            + str(os.getuid() if hasattr(os, 'getuid') else '')
            + platform.machine()
        )
        return machine_id.encode('utf-8')

    def _derive_key_v2(self, salt: bytes) -> bytes:
        """P1: 使用 PBKDF2-HMAC-SHA256 派生加密密钥"""
        return hashlib.pbkdf2_hmac(
            'sha256', self._get_machine_salt(), salt, 100000, dklen=32
        )

    def _encrypt_v2(self, plaintext: str) -> str:
        """P1: 加密 — PBKDF2 密钥 + XOR 密码 + HMAC 完整性校验

        格式: ENCV2:<salt_b64>:<hmac_b64>:<ciphertext_b64>
        """
        salt = os.urandom(16)
        key = self._derive_key_v2(salt)
        data_bytes = plaintext.encode('utf-8')

        # XOR 加密
        ciphertext = bytes(
            d ^ key[i % len(key)] for i, d in enumerate(data_bytes)
        )

        # HMAC-SHA256 完整性校验（覆盖 salt + ciphertext）
        mac = hmac.new(key, salt + ciphertext, hashlib.sha256).digest()

        salt_b64 = base64.b64encode(salt).decode('ascii')
        mac_b64 = base64.b64encode(mac).decode('ascii')
        ct_b64 = base64.b64encode(ciphertext).decode('ascii')

        return f"{self.SECRET_V2_PREFIX}{salt_b64}:{mac_b64}:{ct_b64}"

    def _decrypt_v2(self, encoded: str) -> str:
        """P1: 解密 v2 格式，带完整性校验"""
        parts = encoded.split(':')
        if len(parts) != 3:
            raise DecryptionError("Invalid encrypted data format")

        try:
            salt = base64.b64decode(parts[0])
            stored_mac = base64.b64decode(parts[1])
            ciphertext = base64.b64decode(parts[2])
        except Exception as e:
            raise DecryptionError(f"Failed to decode encrypted data: {e}")

        key = self._derive_key_v2(salt)

        # 验证 HMAC 完整性
        computed_mac = hmac.new(
            key, salt + ciphertext, hashlib.sha256
        ).digest()
        if not hmac.compare_digest(stored_mac, computed_mac):
            raise DecryptionError(
                "Data integrity check failed — data may be corrupted or tampered"
            )

        # XOR 解密
        plaintext = bytes(
            d ^ key[i % len(key)] for i, d in enumerate(ciphertext)
        )

        try:
            return plaintext.decode('utf-8')
        except UnicodeDecodeError as e:
            raise DecryptionError(f"Decrypted data is not valid UTF-8: {e}")

    def _decrypt_v1(self, encoded: str) -> str:
        """兼容：解密旧版 v1 格式（简单 XOR + base64）"""
        machine_id = (
            platform.node()
            + str(os.getuid() if hasattr(os, 'getuid') else '')
            + platform.machine()
        )
        key = hashlib.sha256(machine_id.encode()).digest()
        try:
            encrypted = base64.b64decode(encoded.encode('ascii'))
            decrypted = bytes(
                d ^ key[i % len(key)] for i, d in enumerate(encrypted)
            )
            return decrypted.decode('utf-8')
        except Exception as e:
            raise DecryptionError(f"Failed to decrypt (v1): {e}")

    def set_secret(
        self, key: str, value: str, dry_run: bool = False
    ) -> str:
        """加密存储变量（使用 v2 格式）"""
        if dry_run:
            return f"[DRY-RUN] Would set secret: {key}=*** (encrypted)"
        encrypted = self._encrypt_v2(value)
        self._env_vars[key] = encrypted
        self._save_env_vars()
        self.log_operation('set_secret', key)
        return f"Set secret: {key}=*** (encrypted)"

    def get_secret(self, key: str) -> str:
        """获取并解密变量（兼容 v1 和 v2 格式）"""
        value = self._env_vars.get(key)
        if value is None:
            raise KeyNotFoundError(key)

        if isinstance(value, str) and value.startswith(self.SECRET_V2_PREFIX):
            return self._decrypt_v2(value[len(self.SECRET_V2_PREFIX):])
        elif isinstance(value, str) and value.startswith(self.SECRET_PREFIX):
            # v1 兼容
            return self._decrypt_v1(value[len(self.SECRET_PREFIX):])
        else:
            raise DecryptionError(f"'{key}' is not an encrypted variable")


__all__ = ['EnvironmentManager']
