# EVM Exit Codes Reference

## Exit Code Table

| Code | Name | Exception Type | Description |
|------|------|---------------|-------------|
| 0 | SUCCESS | — | Command completed successfully |
| 1 | GENERAL_ERROR | `OperationCancelledError` | General error or operation cancelled by user |
| 2 | KEY_NOT_FOUND | `KeyNotFoundError`, `KeyAlreadyExistsError` | Variable not found or target key already exists |
| 3 | STORAGE_ERROR | `StorageError`, `CorruptedStorageError`, `LockTimeoutError` | Storage file I/O error, corruption, or lock timeout |
| 4 | IMPORT_ERROR | `ImportFailedError`, `ExportError` | File import/export failure |
| 5 | DECRYPTION_ERROR | `DecryptionError` | Failed to decrypt encrypted variable |
| 6 | VALIDATION_ERROR | `ValidationError`, `SchemaError` | Value validation or schema definition error |
| 7 | GROUP_ERROR | `GroupNotFoundError`, `GroupOperationError` | Group not found or invalid group operation |
| 8 | BACKUP_ERROR | `BackupError` | Backup file not found or corrupt |
| 9 | EDITOR_ERROR | `EditorError` | External editor failed |
| 10 | COMMAND_NOT_FOUND | `CommandNotFoundError` | `exec` target command not found |

## Usage Patterns

### Shell: Branch on exit code

```bash
evm get API_KEY --json 2>/dev/null
case $? in
    0) echo "Found" ;;
    2) echo "Not found — setting default" ;;
    3) echo "Storage error — check file permissions" ;;
    *) echo "Unexpected error" ;;
esac
```

### Shell: Retry on storage error

```bash
for i in 1 2 3; do
    evm set KEY value
    rc=$?
    if [ $rc -eq 0 ]; then break; fi
    if [ $rc -eq 3 ]; then
        echo "Lock timeout, retrying..."
        sleep 1
    else
        echo "Non-retryable error: $rc"
        exit $rc
    fi
done
```

### Python: Catch specific exceptions

```python
from evm.manager import EnvironmentManager
from evm.exceptions import (
    KeyNotFoundError,      # exit 2
    StorageError,          # exit 3
    ImportFailedError,     # exit 4
    DecryptionError,       # exit 5
    SchemaError,           # exit 6
    GroupNotFoundError,    # exit 7
    BackupError,           # exit 8
    CommandNotFoundError,  # exit 10
)

mgr = EnvironmentManager()

try:
    value = mgr.get("KEY")
except KeyNotFoundError:
    mgr.set("KEY", "default_value")
except StorageError:
    print("Storage file is corrupt, reinitializing...")
    mgr._env_vars = {}
    mgr._save_env_vars()
```

## JSON Error Format

When `--json` is active, errors are written to stderr in this format:

```json
{
    "status": "error",
    "error": "Environment variable 'MISSING' not found",
    "error_code": 2
}
```

### Parsing JSON errors in shell

```bash
# Capture both stdout and stderr
output=$(evm get MISSING --json 2>&1)
rc=$?

if [ $rc -ne 0 ]; then
    error_msg=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error',''))" 2>/dev/null)
    echo "EVM error ($rc): $error_msg"
fi
```
