"""
EVM - Environment Variable Manager
A command-line tool for managing environment variables.
"""

__version__ = "2.6.0"
__author__ = "EVM Tool"

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
    ImportFailedError,
    KeyAlreadyExistsError,
    KeyNotFoundError,
    LockTimeoutError,
    OperationCancelledError,
    SchemaError,
    StorageError,
    StoragePermissionError,
    ValidationError,
)
from .manager import EnvironmentManager

__all__ = [
    '__version__',
    '__author__',
    # Core API
    'EnvironmentManager',
    # Exceptions
    'EVMError',
    'KeyNotFoundError',
    'KeyAlreadyExistsError',
    'StorageError',
    'CorruptedStorageError',
    'StoragePermissionError',
    'LockTimeoutError',
    'ExportError',
    'ImportFailedError',
    'CommandNotFoundError',
    'GroupNotFoundError',
    'GroupOperationError',
    'BackupError',
    'EditorError',
    'DecryptionError',
    'ValidationError',
    'SchemaError',
    'OperationCancelledError',
]
