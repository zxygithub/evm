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
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from ._crypto import decrypt_v3, encrypt_v3
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
    SECRET_V3_PREFIX = "ENCv3:"
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
        self._secret_warning_shown = False
        self.env_file.parent.mkdir(parents=True, exist_ok=True)
        self._env_vars = self._load_env_vars()

    # ── 内部存储 ──────────────────────────────────────────

    def _load_env_vars(self) -> dict[str, str]:
        """从存储文件加载环境变量

        Raises:
            CorruptedStorageError: JSON 文件损坏
            StorageError: IO 或权限错误
        """
        if not self.env_file.exists():
            return {}
        try:
            with open(self.env_file, encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            raise CorruptedStorageError(
                f"Storage file is corrupted: {e}. File: {self.env_file}"
            ) from e
        except PermissionError as e:
            raise StorageError(
                f"Permission denied reading storage file: {self.env_file}"
            ) from e
        except OSError as e:
            raise StorageError(
                f"IO error reading storage file: {e}"
            ) from e

    def _save_env_vars(self, dry_run: bool = False) -> None:
        """保存环境变量到存储文件（原子写入 + 共享锁文件 + chmod 600）

        #1 fix: 使用独立的 .lock 文件加锁，而非锁临时文件。
        两个并发进程争夺同一个 .lock 文件的排他锁，
        确保 write + move 操作的原子性。
        """
        if dry_run:
            return

        lock_path = str(self.env_file) + '.lock'
        lock_fd = None
        try:
            # 打开共享锁文件（所有进程竞争同一资源）
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
            self._acquire_lock(lock_fd)
            try:
                tmp_fd, tmp_path = tempfile.mkstemp(
                    dir=str(self.env_file.parent),
                    suffix='.tmp',
                    prefix='.env_',
                )
                try:
                    with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
                        json.dump(
                            self._env_vars, f, indent=2, ensure_ascii=False
                        )
                        f.flush()
                        os.fsync(f.fileno())
                except Exception:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    raise

                # 原子替换（在锁保护下）
                shutil.move(tmp_path, str(self.env_file))
                os.chmod(str(self.env_file), 0o600)
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)

        except LockTimeoutError:
            raise
        except PermissionError as e:
            raise StorageError(
                f"Permission denied writing to: {self.env_file}"
            ) from e
        except OSError as e:
            raise StorageError(
                f"IO error writing storage file: {e}"
            ) from e
        finally:
            if lock_fd is not None:
                try:
                    os.close(lock_fd)
                except OSError:
                    pass

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
            except OSError:
                time.sleep(0.05)
        raise LockTimeoutError(str(self.env_file), self.lock_timeout)

    # ── 基本 CRUD ────────────────────────────────────────

    def set(self, key: str, value: str, dry_run: bool = False) -> str:
        """设置环境变量

        #6 fix: 不记录 value 到操作日志，防止敏感信息泄露。
        """
        if dry_run:
            return f"[DRY-RUN] Would set: {key}={value}"
        self._env_vars[key] = value
        self._save_env_vars()
        self.log_operation('set', key)
        return f"Set: {key}={value}"

    def get(self, key: str) -> str:
        """获取环境变量值

        Raises:
            KeyNotFoundError: 变量不存在
        """
        value = self._env_vars.get(key)
        if value is None:
            raise KeyNotFoundError(key)
        return value  # type: ignore[no-any-return]

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
    ) -> dict[str, str]:
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

    def search(self, pattern: str, search_value: bool = False) -> dict[str, str]:
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
    ) -> tuple[int, bool, Optional[str]]:
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

    def execute(self, command: list[str]) -> int:
        """使用环境变量执行命令

        P1: 改用 subprocess.run 替代 os.execvpe，
        以便 Agent 可以捕获退出码。

        Returns:
            子进程的退出码
        """
        if not command:
            raise EVMError("No command specified")

        env_copy = os.environ.copy()
        for key, value in self._env_vars.items():
            env_copy[key] = str(value)

        try:
            result = subprocess.run(command, env=env_copy)
            return result.returncode
        except FileNotFoundError:
            raise CommandNotFoundError(command[0])
        except KeyboardInterrupt:
            return 130
        except Exception as e:
            raise EVMError(f"Error executing command: {e}")

    # ── 注入 shell ───────────────────────────────────────

    _SHELL_ID_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

    def inject(
        self,
        shell: str = 'sh',
        group: Optional[str] = None,
        include_secrets: bool = False,
        prefix: Optional[str] = None,
    ) -> dict:
        """生成可被 shell eval 的导出语句

        用法: ``eval "$(evm inject)"``

        - 默认只导出非分组变量（含 ``:`` 的 key 不是合法 shell 标识符）。
        - ``--group NAME`` 时导出该分组变量并去除 ``group:`` 前缀。
        - 加密变量默认跳过（避免输出密文）；``include_secrets=True``
          时解密后以明文导出。
        - 非合法 shell 标识符的 key 会被跳过并记入 ``skipped``。

        Args:
            shell: 目标 shell —— bash/zsh/sh 输出 POSIX ``export``；
                fish 输出 ``set -gx``。其余值按 POSIX 处理。
            group: 仅导出指定分组的变量。
            include_secrets: 是否解密并导出加密变量。
            prefix: 给所有导出 key 加前缀（如 ``EVM_``）。

        Returns:
            dict: ``{shell, count, variables, skipped, output}``
        """
        use_fish = shell == 'fish'
        injected: dict[str, str] = {}
        skipped: list[str] = []

        group_prefix = f"{group}:" if group else None

        for key, value in self._env_vars.items():
            # 分组过滤
            if group_prefix:
                if not key.startswith(group_prefix):
                    continue
                final_key = key[len(group_prefix):]
            else:
                # 默认跳过分组变量（含冒号，非合法 shell 标识符）
                if ':' in key:
                    continue
                final_key = key

            # 合法 shell 标识符校验
            if not self._SHELL_ID_PATTERN.match(final_key):
                skipped.append(key)
                continue

            # 加密变量处理（v1 ENC: / v2 ENCv2: / v3 ENCv3:）
            is_secret = isinstance(value, str) and value.startswith(
                (self.SECRET_PREFIX,
                 self.SECRET_V2_PREFIX,
                 self.SECRET_V3_PREFIX)
            )
            if is_secret:
                if not include_secrets:
                    skipped.append(key)
                    continue
                plain = self.get_secret(key)
            else:
                plain = str(value)

            if prefix:
                final_key = f"{prefix}{final_key}"
                if not self._SHELL_ID_PATTERN.match(final_key):
                    skipped.append(key)
                    continue

            injected[final_key] = plain

        lines = []
        for k in sorted(injected):
            v = injected[k]
            if use_fish:
                lines.append(f"set -gx {k} {shlex.quote(v)}")
            else:
                lines.append(f"export {k}={shlex.quote(v)}")

        return {
            'shell': shell,
            'count': len(injected),
            'variables': injected,
            'skipped': skipped,
            'output': '\n'.join(lines) + ('\n' if lines else ''),
        }

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
            try:
                result = subprocess.run([editor, tmp_path])
            except FileNotFoundError:
                raise EditorError(
                    f"Editor not found: '{editor}'. "
                    f"Set $EDITOR or $VISUAL to a valid editor path."
                )
            if result.returncode != 0:
                raise EditorError(
                    f"Editor exited with code {result.returncode}"
                )

            with open(tmp_path, encoding='utf-8') as f:
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

    def info(self) -> dict[str, object]:
        """返回工具元信息"""
        from . import __version__

        groups = self.list_groups()
        total_vars = len(self._env_vars)
        secret_count = sum(
            1 for v in self._env_vars.values()
            if isinstance(v, str) and (
                v.startswith(self.SECRET_PREFIX)
                or v.startswith(self.SECRET_V2_PREFIX)
                or v.startswith(self.SECRET_V3_PREFIX)
            )
        )

        return {
            'version': __version__,
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

    # ── 加密变量（v3: HKDF + HMAC-CTR + Encrypt-then-MAC）──────

    @staticmethod
    def _get_machine_salt() -> bytes:
        """获取机器相关的盐值

        #2: 此盐值与机器绑定。hostname/uid/arch 变化会导致密钥不同。
        用户应知晓此限制。
        """
        machine_id = (
            platform.node()
            + str(os.getuid() if hasattr(os, 'getuid') else '')
            + platform.machine()
        )
        return machine_id.encode('utf-8')

    def _derive_master_key(self, salt: bytes) -> bytes:
        """#4+#15: PBKDF2 派生主密钥，供 _crypto.py 使用"""
        return hashlib.pbkdf2_hmac(
            'sha256', self._get_machine_salt(), salt, 100000, dklen=32
        )

    # ── v2 兼容（保留旧版解密，供自动迁移使用）────────────

    def _derive_key_v2(self, salt: bytes) -> bytes:
        """v2 兼容：PBKDF2 密钥派生（与 v3 共用参数）"""
        return hashlib.pbkdf2_hmac(
            'sha256', self._get_machine_salt(), salt, 100000, dklen=32
        )

    def _decrypt_v2(self, encoded: str) -> str:
        """v2 兼容解密（重复密钥 XOR + HMAC）"""
        parts = encoded.split(':')
        if len(parts) != 3:
            raise DecryptionError("Invalid v2 encrypted data format")

        try:
            salt = base64.b64decode(parts[0])
            stored_mac = base64.b64decode(parts[1])
            ciphertext = base64.b64decode(parts[2])
        except Exception as e:
            raise DecryptionError(
                f"Failed to decode v2 data: {e}"
            ) from e

        key = self._derive_key_v2(salt)

        computed_mac = hmac.new(
            key, salt + ciphertext, hashlib.sha256
        ).digest()
        if not hmac.compare_digest(stored_mac, computed_mac):
            raise DecryptionError(
                "Data integrity check failed (v2)"
            )

        plaintext = bytes(
            d ^ key[i % len(key)] for i, d in enumerate(ciphertext)
        )
        try:
            return plaintext.decode('utf-8')
        except UnicodeDecodeError as e:
            raise DecryptionError(
                f"Decrypted data is not valid UTF-8: {e}"
            ) from e

    def _decrypt_v1(self, encoded: str) -> str:
        """v1 兼容解密（简单 XOR + base64，无盐无 MAC）"""
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
            raise DecryptionError(
                f"Failed to decrypt (v1): {e}"
            ) from e

    def set_secret(
        self, key: str, value: str, dry_run: bool = False
    ) -> str:
        """加密存储变量

        使用 v3 格式: HKDF 密钥分离 + HMAC-CTR + Encrypt-then-MAC。

        #2: 首次使用时打印机器绑定警告。
        """
        if dry_run:
            return f"[DRY-RUN] Would set secret: {key}=*** (encrypted)"

        # #2: 首次使用加密功能时发出警告
        warning = ''
        if not self._secret_warning_shown:
            self._secret_warning_shown = True
            warning = (
                " [WARNING: Encryption key is derived from machine identity "
                "(hostname + uid + arch). Changing hostname or migrating to "
                "another machine will make secrets unrecoverable.]"
            )

        encrypted = encrypt_v3(value, self._derive_master_key)
        self._env_vars[key] = encrypted
        self._save_env_vars()
        self.log_operation('set_secret', key)
        return f"Set secret: {key}=*** (encrypted){warning}"

    def get_secret(self, key: str) -> str:
        """获取并解密变量

        支持 v1/v2/v3 三种格式。
        #16: 读取 v1/v2 格式时自动迁移到 v3。
        """
        value = self._env_vars.get(key)
        if value is None:
            raise KeyNotFoundError(key)

        if isinstance(value, str) and value.startswith(self.SECRET_V3_PREFIX):
            # v3: 直接解密
            return decrypt_v3(
                value[len(self.SECRET_V3_PREFIX):],
                self._derive_master_key,
            )

        elif isinstance(value, str) and value.startswith(self.SECRET_V2_PREFIX):
            # #16: v2 → 解密后自动迁移到 v3
            plaintext = self._decrypt_v2(
                value[len(self.SECRET_V2_PREFIX):]
            )
            self._env_vars[key] = encrypt_v3(
                plaintext, self._derive_master_key
            )
            self._save_env_vars()
            self.log_operation('migrate_secret', key, 'v2 -> v3')
            return plaintext

        elif isinstance(value, str) and value.startswith(self.SECRET_PREFIX):
            # #16: v1 → 解密后自动迁移到 v3
            plaintext = self._decrypt_v1(
                value[len(self.SECRET_PREFIX):]
            )
            self._env_vars[key] = encrypt_v3(
                plaintext, self._derive_master_key
            )
            self._save_env_vars()
            self.log_operation('migrate_secret', key, 'v1 -> v3')
            return plaintext

        else:
            raise DecryptionError(f"'{key}' is not an encrypted variable")


__all__ = ['EnvironmentManager']
