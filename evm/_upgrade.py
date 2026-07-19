#!/usr/bin/env python3
"""
EVM 自升级模块

通过 PyPI JSON API 检查最新版本，必要时调用 pip 升级。
纯标准库实现（urllib + subprocess），无第三方依赖。
"""

import json
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Optional

from . import __version__

# pyproject.toml 中定义的 PyPI 包名
PACKAGE_NAME = 'evm-cli'
PYPI_JSON_URL = f'https://pypi.org/pypi/{PACKAGE_NAME}/json'
# pip 升级命令：始终使用当前解释器的 pip 模块，避免找不到 pip
PIP_UPGRADE_CMD = [
    sys.executable, '-m', 'pip', 'install', '--upgrade', PACKAGE_NAME
]

_DEFAULT_TIMEOUT = 10.0
_DEFAULT_PIP_TIMEOUT = 120.0


def get_current_version() -> str:
    """返回当前运行的 evm 版本"""
    return __version__


def fetch_latest_version(timeout: float = _DEFAULT_TIMEOUT) -> Optional[str]:
    """向 PyPI 查询最新发布版本。

    失败（网络异常 / 解析异常）时返回 None。
    """
    try:
        req = urllib.request.Request(
            PYPI_JSON_URL,
            headers={'User-Agent': f'evm/{__version__}'},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return str(data['info']['version'])
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return None


def _parse_version(version: str) -> tuple[int, ...]:
    """把 '2.5.0' 解析成 (2, 5, 0)。非数字段视为 0。"""
    parts: list[int] = []
    for seg in version.split('.'):
        try:
            parts.append(int(seg))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def is_newer(remote: str, local: str) -> bool:
    """remote 是否比 local 更新（按数字段逐段比较）"""
    rem = _parse_version(remote)
    loc = _parse_version(local)
    max_len = max(len(rem), len(loc))
    rem = rem + (0,) * (max_len - len(rem))
    loc = loc + (0,) * (max_len - len(loc))
    return rem > loc


def check_for_update(
    timeout: float = _DEFAULT_TIMEOUT,
) -> tuple[Optional[str], Optional[bool]]:
    """检查是否有新版本。

    Returns:
        (latest, update_available)
        - latest: 最新版本号字符串；无法获取时为 None
        - update_available: True=有更新, False=已最新, None=无法判定
    """
    latest = fetch_latest_version(timeout=timeout)
    if latest is None:
        return None, None
    return latest, is_newer(latest, get_current_version())


def perform_upgrade(
    force: bool = False,
    dry_run: bool = False,
    timeout: float = _DEFAULT_PIP_TIMEOUT,
) -> tuple[str, str, str]:
    """执行升级。

    Args:
        force: 跳过预检查，直接运行 pip（即使可能已是最新）
        dry_run: 仅打印将要执行的命令，不实际升级
        timeout: pip 子进程超时秒数

    Returns:
        (action, message, new_version)
        - action ∈ {'upgraded', 'already_latest', 'dry_run',
                    'failed', 'network_error'}
        - new_version 为升级后版本号；未知/未升级时为空串
    """
    current = get_current_version()

    if not force:
        latest, available = check_for_update()
        if available is None:
            return (
                'network_error',
                'Unable to check latest version (network unreachable or PyPI error).',
                '',
            )
        if not available:
            return 'already_latest', f'Already up to date ({current}).', current

    if dry_run:
        return (
            'dry_run',
            f'[DRY-RUN] Would run: {" ".join(PIP_UPGRADE_CMD)}',
            '',
        )

    try:
        result = subprocess.run(
            PIP_UPGRADE_CMD,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        return 'failed', f'Upgrade failed: {e}', ''

    if result.returncode != 0:
        lines = (result.stderr or result.stdout or '').strip().splitlines()
        tail = lines[-1] if lines else ''
        detail = f' — {tail}' if tail else ''
        return (
            'failed',
            f'pip upgrade failed (exit {result.returncode}){detail}',
            '',
        )

    # pip 成功后重新查询 PyPI，取得升级后的版本号
    latest = fetch_latest_version()
    new_ver = latest if latest else ''
    if new_ver and is_newer(new_ver, current):
        return 'upgraded', f'Upgraded from {current} to {new_ver}.', new_ver
    return 'upgraded', f'Upgrade complete (now {new_ver or current}).', new_ver


__all__ = [
    'PACKAGE_NAME',
    'PYPI_JSON_URL',
    'PIP_UPGRADE_CMD',
    'get_current_version',
    'fetch_latest_version',
    'is_newer',
    'check_for_update',
    'perform_upgrade',
]
