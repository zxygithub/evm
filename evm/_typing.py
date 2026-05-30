#!/usr/bin/env python3
"""
EVM 类型定义

定义 Mixin 类期望的接口协议。
"""

from pathlib import Path
from typing import Protocol


class EnvironmentManagerProtocol(Protocol):
    """EnvironmentManager 的协议定义，供 Mixin 类使用"""

    env_file: Path
    _env_vars: dict[str, str]

    def _save_env_vars(self, dry_run: bool = False) -> None:
        """保存环境变量到存储文件"""
        ...


__all__ = ['EnvironmentManagerProtocol']
