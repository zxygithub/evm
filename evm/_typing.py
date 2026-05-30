#!/usr/bin/env python3
"""
EVM 类型定义

定义 Mixin 类期望的接口协议。
Mixin 继承此协议后可消除 type: ignore[attr-defined] 注释，
并让 mypy 正确校验跨 mixin 的属性访问。
"""

from pathlib import Path
from typing import Protocol


class EnvironmentManagerProtocol(Protocol):
    """EnvironmentManager 的协议定义，供 Mixin 类使用。

    所有 mixin（IOMixin、GroupMixin、HistoryMixin、SchemaMixin）
    在运行时期望宿主类提供以下属性和方法。
    """

    env_file: Path
    _env_vars: dict[str, str]
    lock_timeout: float

    def _save_env_vars(self, dry_run: bool = False) -> None:
        """保存环境变量到存储文件"""
        ...

    def log_operation(
        self,
        operation: str,
        key: str = '',
        details: str = '',
        status: str = 'success',
    ) -> None:
        """记录操作日志"""
        ...


__all__ = ['EnvironmentManagerProtocol']
