#!/usr/bin/env python3
"""
EVM 操作历史 Mixin

记录操作日志到 ~/.evm/history.jsonl（JSON Lines 格式）。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class HistoryMixin:
    """操作历史 mixin — 记录和查看操作日志"""

    MAX_HISTORY_ENTRIES = 1000

    def _get_history_file(self) -> Path:
        """获取历史文件路径（与 env.json 同目录）"""
        return self.env_file.parent / 'history.jsonl'

    def log_operation(
        self,
        operation: str,
        key: str = '',
        details: str = '',
        status: str = 'success',
    ) -> None:
        """记录操作日志（静默失败，不影响主流程）

        #3 fix: 仅捕获 OSError 而非裸 Exception，
        避免吞没编程错误（AttributeError, TypeError 等）。

        #6 fix: 创建文件时设置 chmod 600。
        """
        try:
            history_file = self._get_history_file()
            is_new = not history_file.exists()

            entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'key': key,
                'details': details,
                'status': status,
            }
            with open(history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

            # 新建文件时设置权限
            if is_new:
                os.chmod(str(history_file), 0o600)

            # 定期清理：超过上限时只保留最新一半
            self._trim_history()
        except OSError:
            pass  # 仅捕获 IO 相关错误，不影响主操作

    def get_history(
        self, limit: int = 20, offset: int = 0
    ) -> List[dict]:
        """获取操作历史（最新在前）"""
        history_file = self._get_history_file()
        if not history_file.exists():
            return []

        entries = []
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except OSError:
            return []

        # 最新在前
        entries.reverse()
        return entries[offset:offset + limit]

    def clear_history(self) -> str:
        """清空操作历史"""
        history_file = self._get_history_file()
        if history_file.exists():
            os.unlink(history_file)
            return "History cleared"
        return "No history to clear"

    def _trim_history(self) -> None:
        """当日志超过上限时裁剪"""
        history_file = self._get_history_file()
        if not history_file.exists():
            return

        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if len(lines) <= self.MAX_HISTORY_ENTRIES:
                return

            # 保留最新的一半
            keep = lines[len(lines) // 2:]
            with open(history_file, 'w', encoding='utf-8') as f:
                f.writelines(keep)
        except OSError:
            pass
