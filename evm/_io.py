#!/usr/bin/env python3
"""
EVM 导入导出 Mixin

从 manager.py 中提取的 IO 功能，load() 已重构为多个独立方法。
"""

import json
import shlex
from pathlib import Path
from typing import Dict, Optional

from ._schema import VALID_KEY_PATTERN
from .exceptions import (
    BackupError,
    ExportError,
    GroupNotFoundError,
    ImportFailedError,
)


def _parse_env_value(raw: str) -> str:
    """#8: 解析 .env 值，正确处理平衡引号

    支持: "double quoted", 'single quoted', unquoted
    不平衡引号（如 "value'）按字面量处理。
    """
    stripped = raw.strip()
    if len(stripped) >= 2:
        if stripped[0] == '"' and stripped[-1] == '"':
            # 平衡双引号：去掉引号，处理转义
            inner = stripped[1:-1]
            return inner.replace('\\"', '"').replace('\\\\', '\\')
        if stripped[0] == "'" and stripped[-1] == "'":
            # 平衡单引号：去掉引号，不处理转义
            return stripped[1:-1]
    # 无引号或不平衡：原样返回（仅去除首尾空白）
    return stripped


def _validate_key_name(key: str) -> bool:
    """#9: 校验环境变量 key 名是否安全"""
    return bool(VALID_KEY_PATTERN.match(key))


class IOMixin:
    """导入导出 mixin — 提供 load/export/backup/restore/diff"""

    # ── 格式检测与加载辅助方法 ────────────────────────────

    def _detect_format(self, path: Path, format_type: Optional[str]) -> str:
        """检测文件格式

        Args:
            path: 文件路径
            format_type: 强制指定的格式

        Returns:
            'json', 'env', 或 'backup'
        """
        if format_type:
            return format_type.lower()
        if path.suffix in ['.json', '.backup']:
            return 'json'
        if path.suffix == '.env':
            return 'env'
        # 内容嗅探
        try:
            with open(path, encoding='utf-8') as f:
                content = f.read(100)
                return 'json' if content.strip().startswith('{') else 'env'
        except OSError:
            return 'json'

    def _load_json_file(self, path: Path) -> dict:
        """加载 JSON 文件

        Raises:
            ImportFailedError: JSON 解析失败
        """
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ImportFailedError(
                    "Invalid JSON format: expected a dictionary",
                    str(path),
                )
            return data
        except json.JSONDecodeError as e:
            raise ImportFailedError(
                f"JSON parse error: {e}", str(path)
            ) from e

    def _load_env_file(self, path: Path) -> Dict[str, str]:
        """加载 .env 文件

        #8: 使用平衡引号解析
        #9: 校验 key 名安全性
        """
        loaded = {}
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, raw_value = line.split('=', 1)
                        key = key.strip()
                        # #9: 校验 key 名
                        if not _validate_key_name(key):
                            continue  # 跳过不安全的 key
                        value = _parse_env_value(raw_value)
                        loaded[key] = value
        return loaded

    def _load_nested(self, data: dict) -> tuple:
        """处理嵌套 JSON（一级 key 作为分组名）

        Returns:
            (loaded_vars, groups_detected)
        """
        loaded_vars = {}
        groups_detected = 0
        for group_name, group_data in data.items():
            if isinstance(group_data, dict):
                groups_detected += 1
                for key, value in group_data.items():
                    loaded_vars[f"{group_name}:{key}"] = value
            else:
                loaded_vars[group_name] = str(group_data)
        return loaded_vars, groups_detected

    def _apply_group_prefix(
        self, vars_dict: Dict[str, str], group: Optional[str]
    ) -> Dict[str, str]:
        """为变量添加分组前缀"""
        if not group:
            return vars_dict
        result = {}
        prefix = f"{group}:"
        for key, value in vars_dict.items():
            if not key.startswith(prefix):
                result[f"{prefix}{key}"] = value
            else:
                result[key] = value
        return result

    # ── 导出 ──────────────────────────────────────────────

    def export(
        self,
        format_type: str = 'json',
        output_file: Optional[str] = None,
        group: Optional[str] = None,
        dry_run: bool = False,
    ) -> str:
        """导出环境变量"""
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
                        # #13: 值含换行时用双引号包裹
                        if '\n' in str(value) or '\r' in str(value):
                            escaped = str(value).replace(
                                '\\', '\\\\'
                            ).replace('"', '\\"').replace('\n', '\\n')
                            f.write(f'{key}="{escaped}"\n')
                        else:
                            f.write(f'{key}={value}\n')
            elif format_type == 'sh':
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write('#!/bin/bash\n\n')
                    for key, value in sorted(export_vars.items()):
                        # #9: key 也用 shlex.quote 转义
                        safe_key = shlex.quote(key)
                        f.write(
                            f'export {safe_key}={shlex.quote(str(value))}\n'
                        )
            else:
                raise ExportError(f"Unsupported format: {format_type}")
            return f"Environment variables exported to: {output_path}"
        except OSError as e:
            raise ExportError(f"Error exporting: {e}") from e

    # ── 导入（重构后）────────────────────────────────────

    def load(
        self,
        input_file: str,
        format_type: Optional[str] = None,
        replace: bool = False,
        group: Optional[str] = None,
        nest: bool = False,
        dry_run: bool = False,
    ) -> str:
        """从文件导入环境变量"""
        input_path = Path(input_file)
        if not input_path.exists():
            raise ImportFailedError(
                f"File not found: {input_file}", input_file
            )

        try:
            fmt = self._detect_format(input_path, format_type)

            # 加载原始数据
            backup_timestamp = None
            groups_detected = 0

            if fmt in ['json', 'backup']:
                data = self._load_json_file(input_path)

                if nest:
                    loaded_vars, groups_detected = self._load_nested(data)
                elif 'variables' in data:
                    # 备份文件格式
                    loaded_vars = data['variables']
                    backup_timestamp = data.get('timestamp', 'unknown')
                else:
                    loaded_vars = data
            elif fmt == 'env':
                loaded_vars = self._load_env_file(input_path)
            else:
                raise ImportFailedError(
                    f"Unsupported format: {fmt}", input_file
                )

            # 添加分组前缀
            if group and not nest:
                loaded_vars = self._apply_group_prefix(loaded_vars, group)

            # 构建消息
            parts = []
            if backup_timestamp:
                parts.append(
                    f"Detected backup file (timestamp: {backup_timestamp})"
                )
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
                    f"Loaded {len(loaded_vars)} environment variables "
                    f"from {input_file}"
                )

            self._save_env_vars()

            if group:
                parts.append(f"Variables added to group '{group}'")

            return '\n'.join(parts) if parts else (
                f"Loaded {len(loaded_vars)} variables"
            )

        except (ImportFailedError, ExportError):
            raise
        except (json.JSONDecodeError, ValueError) as e:
            raise ImportFailedError(
                f"Error loading: {e}", input_file
            ) from e
        except OSError as e:
            raise ImportFailedError(
                f"IO error loading: {e}", input_file
            ) from e

    # ── 备份恢复 ──────────────────────────────────────────

    def backup(self, backup_file: Optional[str] = None) -> str:
        """创建备份"""
        import os
        from datetime import datetime

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
        except OSError as e:
            raise BackupError(f"Error creating backup: {e}") from e

    def restore(self, backup_file: str, merge: bool = False) -> str:
        """从备份恢复"""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise BackupError(f"Backup file not found: {backup_file}")

        try:
            with open(backup_path, encoding='utf-8') as f:
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
        except (json.JSONDecodeError, OSError) as e:
            raise BackupError(
                f"Error restoring from backup: {e}"
            ) from e

    # ── Diff 比较 ─────────────────────────────────────────

    def diff(self, backup_file: str) -> Dict[str, Dict]:
        """比较当前状态与备份文件的差异"""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise BackupError(f"File not found: {backup_file}")

        try:
            with open(backup_path, encoding='utf-8') as f:
                backup_data = json.load(f)

            if 'variables' in backup_data:
                backup_vars = backup_data['variables']
            elif isinstance(backup_data, dict):
                backup_vars = backup_data
            else:
                raise BackupError("Invalid file format for diff")
        except (json.JSONDecodeError, OSError) as e:
            raise BackupError(f"Error reading file: {e}") from e

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
