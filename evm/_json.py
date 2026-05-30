#!/usr/bin/env python3
"""
EVM JSON 输出模块

为 Agent/程序化调用提供结构化 JSON 输出。
设计原则: stdout 是数据 (JSON)，stderr 是日志/人类可读信息。

JSON 信封格式:
  成功: {"status": "ok", "data": {...}}
  错误: {"status": "error", "error": "...", "error_code": N}
"""

import json
import sys
from typing import Any


def json_output(data: Any, quiet: bool = False) -> None:
    """输出成功 JSON 到 stdout

    Args:
        data: 要输出的数据（dict/list/str 等 JSON 可序列化对象）
        quiet: 若为 True 则不输出（静默模式）
    """
    if quiet:
        return
    envelope = {"status": "ok", "data": data}
    print(json.dumps(envelope, ensure_ascii=False, indent=None, default=str))


def json_error(message: str, error_code: int = 1, quiet: bool = False) -> None:
    """输出错误 JSON 到 stderr

    Args:
        message: 错误信息
        error_code: 退出码
        quiet: 若为 True 则不输出
    """
    if quiet:
        return
    envelope = {
        "status": "error",
        "error": message,
        "error_code": error_code,
    }
    print(
        json.dumps(envelope, ensure_ascii=False, indent=None),
        file=sys.stderr,
    )


__all__ = ['json_output', 'json_error']
