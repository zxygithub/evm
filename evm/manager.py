#!/usr/bin/env python3
"""
EVM 核心业务逻辑

EnvironmentManager 类提供所有环境变量管理功能。
所有方法返回数据或抛出异常，不做任何 print() 或 sys.exit()。
"""

import base64
import fcntl
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .exceptions import (
    BackupError,
    CommandNotFoundError,
    CorruptedStorageError,
    DecryptionError,
    EditorError,
    EVMError,
    ExportError,
    GroupNotFoundError,
    GroupOperationError,
    ImportError_,
    KeyAlreadyExistsError,
    KeyNotFoundError,
    StorageError,
)


class EnvironmentManager:
    """环境变量管理器核心类"""

    # 加密前缀标识
    SECRET_PREFIX = "ENC:"
    # 模板引用模式 {{VAR_NAME}}
    TEMPLATE_PATTERN = re.compile(r'\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}')

    def __init__(self, env_file: Optional[str] = None):
        """初始化环境管理器

        Args:
            env_file: 存储文件路径，默认 ~/.evm/env.json
        """
        if env_file is None:
            self.env_file = Path.home() / '.evm' / 'env.json'
        else:
            self.env_file = Path(env_file)

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
        except PermissionError as e:
            raise StorageError(
                f"Permission denied reading storage file: {self.env_file}"
            )
        except IOError as e:
            raise StorageError(f"IO error reading storage file: {e}")

    def _save_env_vars(self, dry_run: bool = False) -> None:
        """保存环境变量到存储文件（原子写入 + 文件锁 + chmod 600）

        Args:
            dry_run: 若为 True 则不实际写入

        Raises:
            StorageError: 写入失败
        """
        if dry_run:
            return

        try:
            # 原子写入：先写临时文件再 rename
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=str(self.env_file.parent),
                suffix='.tmp',
                prefix='.env_',
            )
            try:
                with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
                    # 获取排他锁
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    json.dump(self._env_vars, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except Exception:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise

            # 原子替换
            shutil.move(tmp_path, str(self.env_file))
            # 设置文件权限为仅属主可读写
            os.chmod(str(self.env_file), 0o600)

        except PermissionError:
            raise StorageError(
                f"Permission denied writing to: {self.env_file}"
            )
        except IOError as e:
            raise StorageError(f"IO error writing storage file: {e}")

    # ── 基本 CRUD ────────────────────────────────────────

    def set(self, key: str, value: str, dry_run: bool = False) -> str:
        """设置环境变量

        Returns:
            确认消息
        """
        if dry_run:
            return f"[DRY-RUN] Would set: {key}={value}"
        self._env_vars[key] = value
        self._save_env_vars()
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

        Returns:
            过滤后的变量字典

        Raises:
            GroupNotFoundError: 指定的分组不存在
        """
        if group:
            prefix = f"{group}:"
            filtered = {k: v for k, v in self._env_vars.items() if k.startswith(prefix)}
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

    def clear(self, dry_run: bool = False) -> str:
        """清空所有环境变量

        Returns:
            确认消息
        """
        if not self._env_vars:
            return "No environment variables to clear"
        count = len(self._env_vars)
        if dry_run:
            return f"[DRY-RUN] Would clear {count} variables"
        self._env_vars.clear()
        self._save_env_vars()
        return f"All environment variables cleared ({count} variables)"

    # ── 导入导出 ──────────────────────────────────────────

    def export(
        self,
        format_type: str = 'json',
        output_file: Optional[str] = None,
        group: Optional[str] = None,
        dry_run: bool = False,
    ) -> str:
        """导出环境变量

        Returns:
            确认消息
        """
        if group:
            export_vars = {
                k: v for k, v in self._env_vars.items()
                if k.startswith(f"{group}:")
            }
            if not export_vars:
                raise GroupNotFoundError(group)
        else:
            export_vars = dict(self._env_vars)

        if not export_vars:
            return "No environment variables to export"

        if output_file:
            output_path = Path(output_file)
        else:
            output_path = Path.cwd() / f"env.{format_type}"

        if dry_run:
            return (
                f"[DRY-RUN] Would export {len(export_vars)} variables "
                f"to {output_path} (format={format_type})"
            )

        try:
            if format_type == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_vars, f, indent=2, ensure_ascii=False)
            elif format_type == 'env':
                with open(output_path, 'w', encoding='utf-8') as f:
                    for key, value in sorted(export_vars.items()):
                        f.write(f'{key}={value}\n')
            elif format_type == 'sh':
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write('#!/bin/bash\n\n')
                    for key, value in sorted(export_vars.items()):
                        # P0: 使用 shlex.quote 防止 shell 注入
                        f.write(f'export {key}={shlex.quote(value)}\n')
            else:
                raise ExportError(f"Unsupported format: {format_type}")
            return f"Environment variables exported to: {output_path}"
        except IOError as e:
            raise ExportError(f"Error exporting: {e}")

    def load(
        self,
        input_file: str,
        format_type: Optional[str] = None,
        replace: bool = False,
        group: Optional[str] = None,
        nest: bool = False,
        dry_run: bool = False,
    ) -> str:
        """从文件导入环境变量

        Returns:
            确认消息
        """
        input_path = Path(input_file)
        if not input_path.exists():
            raise ImportError_(f"File not found: {input_file}", input_file)

        try:
            # 判断格式
            if format_type:
                fmt = format_type.lower()
            elif input_path.suffix in ['.json', '.backup']:
                fmt = 'json'
            elif input_path.suffix == '.env':
                fmt = 'env'
            else:
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        content = f.read(100)
                        fmt = 'json' if content.strip().startswith('{') else 'env'
                except Exception:
                    fmt = 'json'

            # 加载数据
            loaded_vars = {}
            backup_timestamp = None
            groups_detected = 0

            if fmt in ['json', 'backup']:
                with open(input_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if nest and isinstance(data, dict):
                    for group_name, group_data in data.items():
                        if isinstance(group_data, dict):
                            groups_detected += 1
                            for key, value in group_data.items():
                                loaded_vars[f"{group_name}:{key}"] = value
                        else:
                            loaded_vars[group_name] = str(group_data)
                elif isinstance(data, dict) and 'variables' in data:
                    loaded_vars = data['variables']
                    backup_timestamp = data.get('timestamp', 'unknown')
                elif isinstance(data, dict):
                    loaded_vars = data
                else:
                    raise ImportError_(
                        "Invalid JSON format: expected a dictionary",
                        input_file,
                    )
            elif fmt == 'env':
                with open(input_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip("'").strip('"')
                                loaded_vars[key] = value
            else:
                raise ImportError_(f"Unsupported format: {fmt}", input_file)

            # 添加分组前缀
            if group and not nest:
                grouped_vars = {}
                for key, value in loaded_vars.items():
                    if not key.startswith(f"{group}:"):
                        grouped_vars[f"{group}:{key}"] = value
                    else:
                        grouped_vars[key] = value
                loaded_vars = grouped_vars

            # 构建消息
            parts = []
            if backup_timestamp:
                parts.append(f"Detected backup file (timestamp: {backup_timestamp})")
            if nest and groups_detected > 0:
                parts.append(
                    f"Detected and imported {groups_detected} groups "
                    f"from nested structure"
                )

            if dry_run:
                parts.append(
                    f"[DRY-RUN] Would {'replace' if replace else 'merge'} "
                    f"{len(loaded_vars)} variables from {input_file}"
                )
                return '\n'.join(parts) if parts else (
                    f"[DRY-RUN] Would load {len(loaded_vars)} variables"
                )

            # 应用到环境变量
            if replace:
                self._env_vars = loaded_vars
                parts.append(
                    f"Replaced environment variables ({len(loaded_vars)} total)"
                )
            else:
                self._env_vars.update(loaded_vars)
                parts.append(
                    f"Loaded {len(loaded_vars)} environment variables from {input_file}"
                )

            self._save_env_vars()

            if group:
                parts.append(f"Variables added to group '{group}'")

            return '\n'.join(parts) if parts else f"Loaded {len(loaded_vars)} variables"

        except (json.JSONDecodeError, ValueError) as e:
            raise ImportError_(f"Error loading: {e}", input_file)
        except IOError as e:
            raise ImportError_(f"IO error loading: {e}", input_file)

    # ── 搜索 ─────────────────────────────────────────────

    def search(self, pattern: str, search_value: bool = False) -> Dict[str, str]:
        """搜索环境变量

        Returns:
            匹配的变量字典
        """
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
        """重命名环境变量

        Raises:
            KeyNotFoundError: 原变量不存在
            KeyAlreadyExistsError: 目标变量名已存在
        """
        if old_key not in self._env_vars:
            raise KeyNotFoundError(old_key)
        if new_key in self._env_vars:
            raise KeyAlreadyExistsError(new_key)
        if dry_run:
            return f"[DRY-RUN] Would rename: {old_key} -> {new_key}"
        value = self._env_vars.pop(old_key)
        self._env_vars[new_key] = value
        self._save_env_vars()
        return f"Renamed: {old_key} -> {new_key}"

    def copy(self, src_key: str, dst_key: str, dry_run: bool = False) -> str:
        """复制环境变量

        Raises:
            KeyNotFoundError: 源变量不存在
        """
        if src_key not in self._env_vars:
            raise KeyNotFoundError(src_key)
        if dry_run:
            return f"[DRY-RUN] Would copy: {src_key} -> {dst_key}"
        self._env_vars[dst_key] = self._env_vars[src_key]
        self._save_env_vars()
        return f"Copied: {src_key} -> {dst_key}"

    # ── 备份恢复 ──────────────────────────────────────────

    def backup(self, backup_file: Optional[str] = None) -> str:
        """创建备份

        Returns:
            确认消息
        """
        if backup_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = Path.home() / '.evm' / f"backup_{timestamp}.json"
        else:
            backup_file = Path(backup_file)

        backup_file.parent.mkdir(parents=True, exist_ok=True)
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'variables': self._env_vars,
        }

        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            os.chmod(str(backup_file), 0o600)
            return f"Backup created: {backup_file}"
        except IOError as e:
            raise BackupError(f"Error creating backup: {e}")

    def restore(self, backup_file: str, merge: bool = False) -> str:
        """从备份恢复

        Returns:
            确认消息
        """
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise BackupError(f"Backup file not found: {backup_file}")

        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            if 'variables' not in backup_data:
                raise BackupError("Invalid backup file format")

            restored_vars = backup_data['variables']
            if merge:
                self._env_vars.update(restored_vars)
                msg = f"Merged {len(restored_vars)} variables from backup"
            else:
                self._env_vars = restored_vars
                msg = f"Restored {len(restored_vars)} variables from backup"

            self._save_env_vars()

            timestamp = backup_data.get('timestamp', '')
            if timestamp:
                msg += f"\nBackup timestamp: {timestamp}"
            return msg
        except (json.JSONDecodeError, IOError) as e:
            raise BackupError(f"Error restoring from backup: {e}")

    # ── 分组管理 ──────────────────────────────────────────

    def set_grouped(
        self, group: str, key: str, value: str, dry_run: bool = False
    ) -> str:
        """设置分组变量"""
        full_key = f"{group}:{key}" if group else key
        if dry_run:
            return f"[DRY-RUN] Would set: [{group}]{key} = {value}"
        self._env_vars[full_key] = value
        self._save_env_vars()
        return f"Set: [{group}]{key} = {value}"

    def get_grouped(self, group: str, key: str) -> str:
        """获取分组变量

        Raises:
            KeyNotFoundError: 变量不存在
        """
        full_key = f"{group}:{key}" if group else key
        value = self._env_vars.get(full_key)
        if value is None and group:
            value = self._env_vars.get(key)
        if value is None:
            raise KeyNotFoundError(full_key)
        return value

    def delete_grouped(
        self, group: str, key: str, dry_run: bool = False
    ) -> str:
        """删除分组变量

        Raises:
            KeyNotFoundError: 变量不存在
        """
        full_key = f"{group}:{key}" if group else key
        if full_key not in self._env_vars:
            raise KeyNotFoundError(full_key)
        if dry_run:
            return f"[DRY-RUN] Would delete: [{group}]{key}"
        del self._env_vars[full_key]
        self._save_env_vars()
        return f"Deleted: [{group}]{key}"

    def list_groups(self) -> Dict[str, int]:
        """列出所有分组

        Returns:
            {group_name: variable_count} 字典
        """
        groups: Dict[str, int] = {}
        for key in self._env_vars:
            if ':' in key:
                group = key.split(':', 1)[0]
                groups[group] = groups.get(group, 0) + 1
        return groups

    def delete_group(self, group: str, dry_run: bool = False) -> str:
        """删除整个分组

        Raises:
            GroupOperationError: 尝试删除 default 组
            GroupNotFoundError: 分组不存在
        """
        if group == 'default':
            raise GroupOperationError(
                "Cannot delete default namespace. Use 'clear' to remove all variables."
            )

        prefix = f"{group}:"
        to_delete = [k for k in self._env_vars if k.startswith(prefix)]

        if not to_delete:
            raise GroupNotFoundError(group)

        if dry_run:
            return (
                f"[DRY-RUN] Would delete group '{group}' "
                f"and {len(to_delete)} variables"
            )

        for key in to_delete:
            del self._env_vars[key]
        self._save_env_vars()
        return f"Deleted group '{group}' and all its variables ({len(to_delete)} total)"

    def move_to_group(
        self, key: str, new_group: str, dry_run: bool = False
    ) -> str:
        """移动变量到另一个分组

        Raises:
            KeyNotFoundError: 变量不存在
        """
        if key not in self._env_vars:
            raise KeyNotFoundError(key)

        new_key = f"{new_group}:{key}"
        if dry_run:
            return f"[DRY-RUN] Would move: {key} -> {new_key}"

        value = self._env_vars.pop(key)
        self._env_vars[new_key] = value
        self._save_env_vars()
        return f"Moved: {key} -> {new_key}"

    # ── 内存加载 ──────────────────────────────────────────

    def load_to_memory(
        self,
        filter_prefix: Optional[str] = None,
        add_evm_prefix: bool = True,
    ) -> Tuple[int, bool, Optional[str]]:
        """加载环境变量到 os.environ

        Returns:
            (loaded_count, add_evm_prefix, filter_prefix)
        """
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
        """使用环境变量执行命令

        Raises:
            CommandNotFoundError: 命令不存在
            EVMError: 执行失败
        """
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

    # ── P2: 编辑器编辑 ────────────────────────────────────

    def edit(self, key: str) -> str:
        """使用 $EDITOR 编辑变量值

        Raises:
            KeyNotFoundError: 变量不存在
            EditorError: 编辑器错误或用户取消
        """
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
                raise EditorError(f"Editor exited with code {result.returncode}")

            with open(tmp_path, 'r', encoding='utf-8') as f:
                new_value = f.read().rstrip('\n')

            if new_value == current_value:
                return f"No changes made to '{key}'"

            self._env_vars[key] = new_value
            self._save_env_vars()
            return f"Updated: {key}"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # ── P2: 工具信息 ──────────────────────────────────────

    def info(self) -> Dict[str, object]:
        """返回工具元信息"""
        groups = self.list_groups()
        total_vars = len(self._env_vars)
        secret_count = sum(
            1 for v in self._env_vars.values()
            if isinstance(v, str) and v.startswith(self.SECRET_PREFIX)
        )

        return {
            'version': '1.7.0',
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

    # ── P2: 模板展开 ──────────────────────────────────────

    def expand(self, key: str, depth: int = 0, max_depth: int = 10) -> str:
        """展开变量值中的模板引用

        {{OTHER_VAR}} 会被替换为 OTHER_VAR 的值。

        Raises:
            KeyNotFoundError: 变量不存在
            EVMError: 递归深度超限
        """
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
                # 递归展开引用的值
                ref_val = self._env_vars[ref_key]
                if self.TEMPLATE_PATTERN.search(ref_val):
                    # 临时存入 env_vars 以递归展开
                    return self._expand_value(ref_val, depth + 1, max_depth)
                return ref_val
            return match.group(0)  # 未找到则保持原样

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

    # ── P2: 加密变量 ──────────────────────────────────────

    def _get_encryption_key(self) -> bytes:
        """获取机器相关的加密密钥"""
        machine_id = (
            platform.node()
            + str(os.getuid() if hasattr(os, 'getuid') else '')
            + platform.machine()
        )
        return hashlib.sha256(machine_id.encode()).digest()

    def _xor_encrypt(self, data: str, key: bytes) -> str:
        """XOR 加密 + base64 编码"""
        data_bytes = data.encode('utf-8')
        encrypted = bytes(
            d ^ key[i % len(key)] for i, d in enumerate(data_bytes)
        )
        return base64.b64encode(encrypted).decode('ascii')

    def _xor_decrypt(self, encoded: str, key: bytes) -> str:
        """base64 解码 + XOR 解密"""
        encrypted = base64.b64decode(encoded.encode('ascii'))
        decrypted = bytes(
            d ^ key[i % len(key)] for i, d in enumerate(encrypted)
        )
        return decrypted.decode('utf-8')

    def set_secret(
        self, key: str, value: str, dry_run: bool = False
    ) -> str:
        """加密存储变量

        Raises:
            StorageError: 加密失败
        """
        encrypted = self._xor_encrypt(value, self._get_encryption_key())
        secret_value = f"{self.SECRET_PREFIX}{encrypted}"
        if dry_run:
            return f"[DRY-RUN] Would set secret: {key}=*** (encrypted)"
        self._env_vars[key] = secret_value
        self._save_env_vars()
        return f"Set secret: {key}=*** (encrypted)"

    def get_secret(self, key: str) -> str:
        """获取并解密变量

        Raises:
            KeyNotFoundError: 变量不存在
            DecryptionError: 解密失败或不是加密变量
        """
        value = self._env_vars.get(key)
        if value is None:
            raise KeyNotFoundError(key)

        if not isinstance(value, str) or not value.startswith(self.SECRET_PREFIX):
            raise DecryptionError(f"'{key}' is not an encrypted variable")

        try:
            encoded = value[len(self.SECRET_PREFIX):]
            return self._xor_decrypt(encoded, self._get_encryption_key())
        except Exception as e:
            raise DecryptionError(f"Failed to decrypt '{key}': {e}")

    # ── P2: Diff 比较 ─────────────────────────────────────

    def diff(self, backup_file: str) -> Dict[str, Dict]:
        """比较当前状态与备份文件的差异

        Returns:
            {'added': {}, 'removed': {}, 'changed': {}}
        """
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise BackupError(f"File not found: {backup_file}")

        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            if 'variables' in backup_data:
                backup_vars = backup_data['variables']
            elif isinstance(backup_data, dict):
                backup_vars = backup_data
            else:
                raise BackupError("Invalid file format for diff")
        except (json.JSONDecodeError, IOError) as e:
            raise BackupError(f"Error reading file: {e}")

        current = self._env_vars
        added = {k: v for k, v in current.items() if k not in backup_vars}
        removed = {k: v for k, v in backup_vars.items() if k not in current}
        changed = {
            k: {'current': current[k], 'backup': backup_vars[k]}
            for k in current
            if k in backup_vars and current[k] != backup_vars[k]
        }

        return {
            'added': added,
            'removed': removed,
            'changed': changed,
            'backup_timestamp': backup_data.get('timestamp', ''),
        }


__all__ = ['EnvironmentManager']
