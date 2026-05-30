#!/usr/bin/env python3
"""
EVM 分组操作 Mixin

从 manager.py 中提取的分组管理功能。
"""


from ._typing import EnvironmentManagerProtocol
from .exceptions import (
    GroupNotFoundError,
    GroupOperationError,
    KeyAlreadyExistsError,
    KeyNotFoundError,
)


class GroupMixin(EnvironmentManagerProtocol):
    """分组操作 mixin — 提供 setg/getg/deleteg/groups 等功能"""

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

    def list_groups(self) -> dict[str, int]:
        """列出所有分组

        Returns:
            {group_name: variable_count} 字典
        """
        groups: dict[str, int] = {}
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
            KeyAlreadyExistsError: 目标分组中已有同名 key
        """
        if key not in self._env_vars:
            raise KeyNotFoundError(key)

        new_key = f"{new_group}:{key}"
        if new_key in self._env_vars and new_key != key:
            raise KeyAlreadyExistsError(new_key)

        if dry_run:
            return f"[DRY-RUN] Would move: {key} -> {new_key}"

        value = self._env_vars.pop(key)
        self._env_vars[new_key] = value
        self._save_env_vars()
        return f"Moved: {key} -> {new_key}"
