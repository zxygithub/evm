#!/usr/bin/env python3
"""
EVM 操作历史 Mixin

记录操作日志到 history.jsonl（JSON Lines 格式），与 env.json 同目录。
"""

import fcntl
import json
import os
from datetime import datetime
from pathlib import Path

from ._typing import EnvironmentManagerProtocol


class HistoryMixin(EnvironmentManagerProtocol):
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

        仅捕获 OSError，避免吞没编程错误。
        创建文件时设置 chmod 600。
        使用文件锁防止并发追加时行交错。
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

            fd = os.open(str(history_file), os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
                try:
                    line = json.dumps(entry, ensure_ascii=False) + '\n'
                    os.write(fd, line.encode('utf-8'))
                finally:
                    fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

            # 新建文件时设置权限
            if is_new:
                os.chmod(str(history_file), 0o600)

            # 惰性裁切：仅在超过 1.5 倍上限时触发，避免每次 O(N) 扫描
            self._trim_history_if_needed()
        except OSError:
            pass

    def get_history(
        self, limit: int = 20, offset: int = 0
    ) -> list[dict]:
        """获取操作历史（最新在前）"""
        history_file = self._get_history_file()
        if not history_file.exists():
            return []

        entries = []
        try:
            with open(history_file, encoding='utf-8') as f:
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

    def _trim_history_if_needed(self) -> None:
        """惰性裁切：仅在行数超过 1.5 倍上限时触发。

        使用原子写入（先写临时文件，再 rename）防止崩溃导致历史丢失。
        """
        history_file = self._get_history_file()
        if not history_file.exists():
            return

        threshold = int(self.MAX_HISTORY_ENTRIES * 1.5)
        try:
            with open(history_file, encoding='utf-8') as f:
                lines = f.readlines()

            if len(lines) <= threshold:
                return

            # 保留最新的一半
            keep = lines[len(lines) // 2:]

            # 原子写入：先写临时文件，再 rename
            tmp_path = str(history_file) + '.trim.tmp'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                f.writelines(keep)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, str(history_file))
            os.chmod(str(history_file), 0o600)
        except OSError:
            # 清理临时文件
            tmp_path = str(history_file) + '.trim.tmp'
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
