#!/usr/bin/env python3
"""
EVM 自定义异常体系

所有 EVM 错误都继承自 EVMError，便于调用者统一捕获。
"""


class EVMError(Exception):
    """EVM 所有错误的基类"""
    pass


class KeyNotFoundError(EVMError):
    """请求的环境变量不存在"""
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Environment variable '{key}' not found")


class KeyAlreadyExistsError(EVMError):
    """目标变量名已存在（rename/copy 冲突）"""
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Environment variable '{key}' already exists")


class StorageError(EVMError):
    """存储文件读写失败"""
    pass


class CorruptedStorageError(StorageError):
    """存储文件损坏（JSON 解析失败）"""
    pass


class PermissionError_(StorageError):
    """存储文件权限不足"""
    pass


class ExportError(EVMError):
    """导出失败"""
    pass


class ImportError_(EVMError):
    """导入失败"""
    def __init__(self, message: str, file_path: str = None):
        self.file_path = file_path
        super().__init__(message)


class CommandNotFoundError(EVMError):
    """exec 命令找不到可执行文件"""
    def __init__(self, command: str):
        self.command = command
        super().__init__(f"Command not found: {command}")


class GroupNotFoundError(EVMError):
    """请求的分组不存在"""
    def __init__(self, group: str):
        self.group = group
        super().__init__(f"Group '{group}' not found or has no variables")


class GroupOperationError(EVMError):
    """分组操作错误（如删除 default 组）"""
    pass


class BackupError(EVMError):
    """备份/恢复失败"""
    pass


class EditorError(EVMError):
    """编辑器相关错误"""
    pass


class DecryptionError(EVMError):
    """解密失败"""
    pass


__all__ = [
    'EVMError',
    'KeyNotFoundError',
    'KeyAlreadyExistsError',
    'StorageError',
    'CorruptedStorageError',
    'PermissionError_',
    'ExportError',
    'ImportError_',
    'CommandNotFoundError',
    'GroupNotFoundError',
    'GroupOperationError',
    'BackupError',
    'EditorError',
    'DecryptionError',
]
