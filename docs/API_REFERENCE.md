# EVM Python API Reference

**Version**: 2.6.1  
**Requirements**: Python 3.9+, POSIX (macOS / Linux)  
**Dependencies**: None (stdlib only)

---

## Table of Contents

1. [Installation & Import](#installation--import)
2. [EnvironmentManager](#environmentmanager)
   - [Constructor](#constructor)
   - [CRUD Operations](#crud-operations)
   - [Search & Copy](#search--copy)
   - [Group Operations](#group-operations)
   - [Import / Export](#import--export)
   - [Backup / Restore / Diff](#backup--restore--diff)
   - [Encryption](#encryption)
   - [Schema & Validation](#schema--validation)
   - [Template Expansion](#template-expansion)
   - [History](#history)
   - [Execute & Edit](#execute--edit)
   - [Utility Methods](#utility-methods)
3. [Exception Hierarchy](#exception-hierarchy)
4. [Formatters Module](#formatters-module)
5. [Crypto Module](#crypto-module)
6. [CLI Exit Codes](#cli-exit-codes)
7. [Quick-Start Recipes](#quick-start-recipes)

---

## Installation & Import

```bash
pip install -e .        # production
pip install -e ".[dev]" # development (pytest + ruff + mypy)
```

```python
# Recommended: import from the package root
from evm import EnvironmentManager, KeyNotFoundError, EVMError

# Or import from submodules directly
from evm.manager import EnvironmentManager
from evm.exceptions import EVMError, KeyNotFoundError, DecryptionError
from evm.formatters import print_vars_table, print_diff
from evm._crypto import encrypt_v3, decrypt_v3
```

### Package Exports

| Symbol | Source | Description |
|--------|--------|-------------|
| `EnvironmentManager` | `evm.manager` | Core manager class |
| `EVMError` | `evm.exceptions` | Base exception class |
| `KeyNotFoundError` | `evm.exceptions` | Variable not found |
| `KeyAlreadyExistsError` | `evm.exceptions` | Target key already exists |
| `StorageError` | `evm.exceptions` | File I/O failure |
| `CorruptedStorageError` | `evm.exceptions` | JSON corruption |
| `StoragePermissionError` | `evm.exceptions` | Permission denied |
| `LockTimeoutError` | `evm.exceptions` | Lock acquisition timeout |
| `ExportError` | `evm.exceptions` | Export failure |
| `ImportFailedError` | `evm.exceptions` | Import failure |
| `CommandNotFoundError` | `evm.exceptions` | Exec command not found |
| `GroupNotFoundError` | `evm.exceptions` | Group not found |
| `GroupOperationError` | `evm.exceptions` | Invalid group operation |
| `BackupError` | `evm.exceptions` | Backup/restore failure |
| `EditorError` | `evm.exceptions` | $EDITOR not found / failed |
| `DecryptionError` | `evm.exceptions` | Decryption failure |
| `ValidationError` | `evm.exceptions` | Schema validation failure |
| `SchemaError` | `evm.exceptions` | Schema definition error |
| `OperationCancelledError` | `evm.exceptions` | User cancelled operation |

---

## EnvironmentManager

The central class that provides all variable management functionality through mixin composition.

```
EnvironmentManager
├── IOMixin       → load, export, backup, restore, diff
├── GroupMixin    → set_grouped, get_grouped, delete_grouped, list_groups, delete_group, move_to_group
├── HistoryMixin  → log_operation, get_history, clear_history
└── SchemaMixin   → set_schema, get_schema, delete_schema, validate, validate_all
```

### Constructor

```python
EnvironmentManager(
    env_file: str | None = None,
    lock_timeout: float = 5.0,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `env_file` | `str \| None` | `~/.evm/env.json` | Path to the JSON storage file. Parent directory is created automatically. |
| `lock_timeout` | `float` | `5.0` | Seconds to wait for file lock before raising `LockTimeoutError`. |

```python
# Default: uses ~/.evm/env.json
mgr = EnvironmentManager()

# Custom storage path (useful for per-project isolation)
mgr = EnvironmentManager(env_file='/tmp/my_project.json')

# Shorter lock timeout for CI environments
mgr = EnvironmentManager(lock_timeout=2.0)
```

**Attributes** (read-only after construction):

| Attribute | Type | Description |
|-----------|------|-------------|
| `env_file` | `Path` | Resolved storage file path |
| `_env_vars` | `dict[str, str]` | In-memory variable store (internal) |

---

### CRUD Operations

#### `set(key, value, dry_run=False) -> str`

Set an environment variable. Persists immediately.

```python
msg = mgr.set('API_KEY', 'abc123')
# msg: "Set: API_KEY=abc123"

# Preview without writing
msg = mgr.set('KEY', 'val', dry_run=True)
# msg: "[DRY-RUN] Would set: KEY=val"
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `str` | — | Variable name |
| `value` | `str` | — | Variable value |
| `dry_run` | `bool` | `False` | If `True`, preview without writing |

**Returns**: Status message string.

---

#### `get(key) -> str`

Retrieve a variable value.

```python
value = mgr.get('API_KEY')  # "abc123"
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | `str` | Variable name |

**Raises**: `KeyNotFoundError` if the variable does not exist.

---

#### `delete(key, dry_run=False) -> str`

Delete a variable.

```python
msg = mgr.delete('API_KEY')
# msg: "Deleted: API_KEY"
```

**Raises**: `KeyNotFoundError` if the variable does not exist.

---

#### `exists(key) -> bool`

Check if a variable exists (no exceptions).

```python
if mgr.exists('API_KEY'):
    print("Found!")
```

---

#### `list_vars(pattern=None, group=None, show_groups=False, no_prefix=False) -> dict[str, str]`

List variables with optional filtering.

```python
all_vars = mgr.list_vars()
filtered = mgr.list_vars(pattern='API')
dev_vars = mgr.list_vars(group='dev')
dev_stripped = mgr.list_vars(group='dev', no_prefix=True)
# {"DEBUG": "true"} instead of {"dev:DEBUG": "true"}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pattern` | `str \| None` | `None` | Case-insensitive substring match on keys |
| `group` | `str \| None` | `None` | Filter by group prefix |
| `show_groups` | `bool` | `False` | (unused, reserved) |
| `no_prefix` | `bool` | `False` | Strip group prefix from keys |

**Raises**: `GroupNotFoundError` if `group` is specified but contains no variables.

---

#### `clear(dry_run=False, force=False) -> str`

Delete all variables.

```python
msg = mgr.clear()
# msg: "All environment variables cleared (5 variables)"
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dry_run` | `bool` | `False` | Preview without writing |
| `force` | `bool` | `False` | Skip confirmation (CLI layer handles prompts) |

---

### Search & Copy

#### `search(pattern, search_value=False) -> dict[str, str]`

Search variables by key (and optionally value).

```python
results = mgr.search('API')
results = mgr.search('localhost', search_value=True)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pattern` | `str` | — | Case-insensitive search term |
| `search_value` | `bool` | `False` | Also search in values |

**Returns**: `dict[str, str]` of matching key-value pairs.

---

#### `rename(old_key, new_key, dry_run=False) -> str`

Rename a variable.

```python
msg = mgr.rename('OLD_NAME', 'NEW_NAME')
```

**Raises**: `KeyNotFoundError` / `KeyAlreadyExistsError`.

---

#### `copy(src_key, dst_key, dry_run=False) -> str`

Copy a variable's value to a new key.

```python
msg = mgr.copy('API_KEY', 'API_KEY_BACKUP')
```

**Raises**: `KeyNotFoundError` if `src_key` does not exist.

---

### Group Operations

#### `set_grouped(group, key, value, dry_run=False) -> str`

```python
mgr.set_grouped('dev', 'DEBUG', 'true')
# Stores as "dev:DEBUG" = "true"
```

#### `get_grouped(group, key) -> str`

```python
val = mgr.get_grouped('dev', 'DEBUG')
```

**Raises**: `KeyNotFoundError`.

#### `delete_grouped(group, key, dry_run=False) -> str`

```python
mgr.delete_grouped('dev', 'DEBUG')
```

**Raises**: `KeyNotFoundError`.

#### `list_groups() -> dict[str, int]`

Returns `{group_name: variable_count}`.

```python
groups = mgr.list_groups()
# {"dev": 3, "prod": 2}
```

#### `delete_group(group, dry_run=False) -> str`

Delete all variables in a group.

```python
mgr.delete_group('dev')
```

**Raises**: `GroupOperationError` if `group == 'default'`, `GroupNotFoundError` if group is empty.

#### `move_to_group(key, new_group, dry_run=False) -> str`

Move a variable to a different group.

```python
mgr.move_to_group('API_KEY', 'prod')
```

**Raises**: `KeyNotFoundError` / `KeyAlreadyExistsError` if the target group already has a variable with the same name.

---

### Import / Export

#### `export(format_type='json', output_file=None, group=None, dry_run=False) -> str`

Export variables to a file.

```python
msg = mgr.export(format_type='env', output_file='.env')
msg = mgr.export(format_type='sh', output_file='setup.sh')
msg = mgr.export(group='dev')  # Export only dev group
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format_type` | `str` | `'json'` | `'json'`, `'env'`, or `'sh'` |
| `output_file` | `str \| None` | `None` | Output path (default: `./env.<format>` in cwd) |
| `group` | `str \| None` | `None` | Export only this group |
| `dry_run` | `bool` | `False` | Preview |

**Raises**: `ExportError` on I/O failure, `GroupNotFoundError` if group is empty.

---

#### `load(input_file, format_type=None, replace=False, group=None, nest=False, dry_run=False) -> str`

Import variables from a file.

```python
msg = mgr.load('config.json')
msg = mgr.load('.env', format_type='env')
msg = mgr.load('backup.json', replace=True)  # Replace all existing vars
msg = mgr.load('config.json', group='staging')  # Add group prefix
msg = mgr.load('multi.json', nest=True)  # Auto-detect nested groups
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_file` | `str` | — | Path to input file |
| `format_type` | `str \| None` | `None` | Force format (`'json'`, `'env'`, `'backup'`). Auto-detected if `None`. |
| `replace` | `bool` | `False` | Replace all variables instead of merging |
| `group` | `str \| None` | `None` | Add group prefix to imported keys |
| `nest` | `bool` | `False` | Treat top-level dict keys as group names |
| `dry_run` | `bool` | `False` | Preview |

**Returns**: Status message. If `.env` import skips invalid keys, the message includes `"Skipped N invalid key(s): ..."`.

**Raises**: `ImportFailedError` on file not found, parse error, or I/O error.

---

### Backup / Restore / Diff

#### `backup(backup_file=None) -> str`

Create a timestamped backup.

```python
msg = mgr.backup()  # → env_file.parent/backup_YYYYMMDD_HHMMSS.json
msg = mgr.backup('/tmp/my_backup.json')
```

---

#### `restore(backup_file, merge=False) -> str`

Restore from a backup file.

```python
msg = mgr.restore('backup.json')              # Replace all
msg = mgr.restore('backup.json', merge=True)   # Merge into existing
```

**Raises**: `BackupError` on file not found, invalid format, or I/O error.

---

#### `diff(backup_file) -> dict[str, dict]`

Compare current state with a backup file.

```python
result = mgr.diff('backup.json')
# {
#     'added':   {'NEW_KEY': 'value'},
#     'removed': {'OLD_KEY': 'value'},
#     'changed': {'KEY': {'current': 'new', 'backup': 'old'}},
#     'backup_timestamp': '2026-01-01T00:00:00'
# }
```

**Raises**: `BackupError` on file not found or parse error.

---

### Encryption

EVM uses HKDF + HMAC-CTR + Encrypt-then-MAC (v3 format). Variables stored as `ENCv3:<salt>:<iv>:<mac>:<ciphertext>`.

> ⚠️ Encryption keys are derived from machine identity (`hostname + uid + arch`). Changing any of these will make secrets unrecoverable.

#### `set_secret(key, value, dry_run=False) -> str`

Encrypt and store a variable.

```python
msg = mgr.set_secret('DB_PASS', 'my_password')
# msg: "Set secret: DB_PASS=*** (encrypted) [WARNING: ...]"
```

The first call per instance includes a machine-binding warning.

---

#### `get_secret(key) -> str`

Decrypt and return the plaintext value.

```python
password = mgr.get_secret('DB_PASS')
```

Supports automatic migration: reading v1/v2 encrypted values transparently upgrades them to v3.

**Raises**: `KeyNotFoundError` if key doesn't exist, `DecryptionError` if the value is not encrypted or integrity check fails.

---

### Schema & Validation

#### `set_schema(key, format=None, required=None, pattern=None, description=None) -> str`

Define a schema for a variable.

```python
mgr.set_schema('API_URL', format='url', required=True)
mgr.set_schema('PORT', format='port')
mgr.set_schema('EMAIL', pattern=r'^.+@.+\..+$')
```

Built-in formats: `url`, `email`, `port`, `integer`, `boolean`, `path`, `ipv4`, `ipv6`.

**Raises**: `SchemaError` on unknown format or invalid regex pattern.

---

#### `get_schema(key=None) -> dict`

Retrieve schema definitions. Pass `key=None` to get all.

```python
all_schemas = mgr.get_schema()
port_schema = mgr.get_schema('PORT')
```

**Raises**: `SchemaError` if `key` is specified but has no schema.

---

#### `delete_schema(key) -> str`

Remove a schema definition.

**Raises**: `SchemaError` if key has no schema.

---

#### `validate(key, value=None) -> dict`

Validate a value against its schema.

```python
result = mgr.validate('API_URL')
# {'valid': True, 'errors': [], 'warnings': []}

result = mgr.validate('PORT', value='99999')
# {'valid': False, 'errors': ["Value '99999' does not match format 'port'"], 'warnings': []}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `str` | — | Variable name (must have schema defined) |
| `value` | `str \| None` | `None` | Value to validate. If `None`, uses the current stored value. |

**Raises**: `SchemaError` if no schema is defined for `key`.

---

#### `validate_all() -> dict[str, dict]`

Validate all variables that have schemas defined.

```python
results = mgr.validate_all()
# {'PORT': {'valid': True, ...}, 'URL': {'valid': False, ...}}
```

---

### Template Expansion

#### `expand(key, depth=0, max_depth=10) -> str`

Expand `{{VAR}}` template references in a variable's value.

```python
mgr.set('HOST', 'example.com')
mgr.set('URL', 'https://{{HOST}}/api')
expanded = mgr.expand('URL')
# "https://example.com/api"
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | `str` | — | Variable name to expand |
| `depth` | `int` | `0` | Current recursion depth (internal) |
| `max_depth` | `int` | `10` | Maximum nesting depth |

**Raises**: `KeyNotFoundError` / `EVMError` (circular reference).

---

### History

#### `get_history(limit=20, offset=0) -> list[dict]`

Retrieve operation history (newest first).

```python
entries = mgr.get_history(limit=10)
# [{'timestamp': '...', 'operation': 'set', 'key': 'API_KEY', 'status': 'success'}, ...]
```

---

#### `clear_history() -> str`

Delete all history entries.

```python
msg = mgr.clear_history()  # "History cleared"
```

---

### Execute & Edit

#### `execute(command) -> int`

Run a command with all EVM variables injected into the environment.

```python
exit_code = mgr.execute(['python', 'app.py'])
```

**Returns**: The child process exit code.

**Raises**: `CommandNotFoundError` if the executable is not found.

---

#### `inject(shell='sh', group=None, include_secrets=False, prefix=None) -> dict`

Generate shell-sourceable export statements (for `eval "$(evm inject)"`).

```python
result = mgr.inject(shell='bash')
# {'shell': 'bash', 'count': 2,
#  'variables': {'API_KEY': 'abc123', 'DB_URL': 'localhost'},
#  'skipped': [], 'output': "export API_KEY=abc123\nexport DB_URL=localhost\n"}
```

**Behavior**:
- Plain variables → exported
- Grouped variables (e.g. `dev:DB_URL`) → silently skipped (invalid shell identifiers); use `group='dev'` to strip the prefix and export them
- Encrypted secrets (`--secret`) → skipped by default (would leak ciphertext); `include_secrets=True` decrypts and exports them
- Invalid shell identifiers → skipped, reported in `skipped`

**Args**:
- `shell`: `'bash'` / `'zsh'` / `'sh'` → POSIX `export KEY=VALUE`; `'fish'` → `set -gx KEY VALUE`. Other values fall back to POSIX.
- `group`: only export this group's variables (strips the `group:` prefix)
- `include_secrets`: decrypt and include encrypted variables
- `prefix`: add a prefix to every exported key (e.g. `'EVM_'`)

**Returns**: `dict` with keys `shell`, `count`, `variables`, `skipped`, `output`.

---

#### `edit(key) -> str`

Open a variable's value in `$EDITOR` (or `$VISUAL`, fallback `vi`).

```python
msg = mgr.edit('API_KEY')
# "Updated: API_KEY" or "No changes made to 'API_KEY'"
```

**Raises**: `KeyNotFoundError` / `EditorError`.

---

### Utility Methods

#### `load_to_memory(filter_prefix=None, add_evm_prefix=True) -> tuple[int, bool, str | None]`

Load all EVM variables into `os.environ`.

```python
count, prefix_used, filter_used = mgr.load_to_memory()
# Variables available as os.environ['EVM:API_KEY']

count, _, _ = mgr.load_to_memory(add_evm_prefix=False)
# Variables available as os.environ['API_KEY']
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filter_prefix` | `str \| None` | `None` | Only load keys starting with this prefix |
| `add_evm_prefix` | `bool` | `True` | Prefix keys with `EVM:` in `os.environ` |

---

#### `info() -> dict[str, object]`

Return metadata about the EVM instance.

```python
info = mgr.info()
# {
#     'version': '2.3.0',
#     'python': '3.13.0',
#     'platform': 'Darwin',
#     'storage_path': '/Users/.../env.json',
#     'total_variables': 5,
#     'total_groups': 2,
#     'secret_variables': 1,
#     'groups': {'dev': 3, 'prod': 2},
#     ...
# }
```

---

#### `search(pattern, search_value=False) -> dict[str, str]`

Search variables by key and/or value.

---

## Exception Hierarchy

All exceptions inherit from `EVMError`, which inherits from `Exception`.

```
Exception
└── EVMError
    ├── KeyNotFoundError(key)
    ├── KeyAlreadyExistsError(key)
    ├── StorageError
    │   ├── CorruptedStorageError
    │   ├── StoragePermissionError
    │   └── LockTimeoutError(path, timeout)
    ├── ExportError
    ├── ImportFailedError(message, file_path=None)
    ├── CommandNotFoundError(command)
    ├── GroupNotFoundError(group)
    ├── GroupOperationError
    ├── BackupError
    ├── EditorError
    ├── DecryptionError
    ├── ValidationError(key, value, expected_format)
    ├── SchemaError(message, key=None)
    └── OperationCancelledError
```

### Exception Attributes

| Exception | Extra Attributes |
|-----------|-----------------|
| `KeyNotFoundError` | `.key` |
| `KeyAlreadyExistsError` | `.key` |
| `LockTimeoutError` | `.path`, `.timeout` |
| `ImportFailedError` | `.file_path` |
| `CommandNotFoundError` | `.command` |
| `GroupNotFoundError` | `.group` |
| `ValidationError` | `.key`, `.value`, `.expected_format` |
| `SchemaError` | `.key` |

### Catching All EVM Errors

```python
from evm import EVMError

try:
    mgr.get('MISSING')
except EVMError as e:
    print(f"EVM error: {e}")
```

---

## Formatters Module

`evm.formatters` provides terminal output functions. All return `None` (they print directly).

```python
from evm.formatters import (
    print_vars_table,
    print_vars_by_group,
    print_search_results,
    print_groups,
    print_info,
    print_diff,
    print_load_memory_result,
    print_history,
    print_validate_result,
    print_validate_all,
    print_schema,
)
```

| Function | Parameters | Description |
|----------|-----------|-------------|
| `print_vars_table(vars_dict, title, show_total)` | `dict`, `str`, `bool` | Table display of variables |
| `print_vars_by_group(vars_dict)` | `dict` | Grouped display |
| `print_search_results(results, pattern, search_value)` | `dict`, `str`, `bool` | Search results |
| `print_groups(groups)` | `dict[str, int]` | Group listing |
| `print_info(info)` | `dict` | Tool metadata |
| `print_diff(diff_result)` | `dict` | Diff comparison |
| `print_load_memory_result(loaded, prefix, filter)` | `int`, `bool`, `str\|None` | Load-to-memory result |
| `print_history(entries)` | `list[dict]` | History entries |
| `print_validate_result(key, result)` | `str`, `dict` | Single validation result |
| `print_validate_all(results)` | `dict[str, dict]` | All validation results |
| `print_schema(schema)` | `dict` | Schema definitions |

All formatters use `shutil.get_terminal_size()` for dynamic width adaptation (capped at 80–120 columns depending on context).

---

## Crypto Module

`evm._crypto` provides low-level cryptographic primitives.

```python
from evm._crypto import (
    hkdf_expand,
    derive_subkeys,
    hmac_ctr_keystream,
    encrypt_v3,
    decrypt_v3,
    HKDF_HASH_LEN,  # = 32 (SHA-256 output length)
)
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `hkdf_expand` | `(prk: bytes, info: bytes, length: int = 32) -> bytes` | HKDF-Expand (RFC 5869) |
| `derive_subkeys` | `(master_key: bytes, salt: bytes) -> tuple[bytes, bytes]` | Derive independent `(enc_key, mac_key)` |
| `hmac_ctr_keystream` | `(key: bytes, iv: bytes, length: int) -> bytes` | HMAC-CTR stream cipher |
| `encrypt_v3` | `(plaintext: str, derive_key_fn) -> str` | Encrypt to `ENCv3:` format |
| `decrypt_v3` | `(encoded: str, derive_key_fn) -> str` | Decrypt from `ENCv3:` format |

### Encryption Format

```
ENCv3:<salt_b64>:<iv_b64>:<mac_b64>:<ciphertext_b64>
```

- **Key derivation**: PBKDF2-HMAC-SHA256 (100k iterations) → master key → HKDF-Expand → `(enc_key, mac_key)`
- **Encryption**: HMAC-CTR stream cipher with `enc_key`
- **Authentication**: HMAC-SHA256 with `mac_key` over `salt || iv || ciphertext` (Encrypt-then-MAC)

---

## CLI Exit Codes

When using EVM via subprocess, these exit codes indicate the result:

| Code | Meaning | Exception |
|------|---------|-----------|
| 0 | Success | — |
| 1 | General error / cancelled | `OperationCancelledError` |
| 2 | Variable not found | `KeyNotFoundError` / `KeyAlreadyExistsError` |
| 3 | Storage error | `StorageError` / `CorruptedStorageError` / `LockTimeoutError` |
| 4 | Import/export error | `ImportFailedError` / `ExportError` |
| 5 | Decryption error | `DecryptionError` |
| 6 | Validation error | `ValidationError` / `SchemaError` |
| 7 | Group error | `GroupNotFoundError` / `GroupOperationError` |
| 8 | Backup error | `BackupError` |
| 9 | Editor error | `EditorError` |
| 10 | Command not found | `CommandNotFoundError` |

```python
import subprocess

result = subprocess.run(['evm', 'get', 'MISSING_KEY'])
if result.returncode == 2:
    print("Key not found")
elif result.returncode == 0:
    print("Found")
```

---

## Quick-Start Recipes

### Isolated Per-Project Storage

```python
from evm import EnvironmentManager

mgr = EnvironmentManager(env_file='/path/to/project/.evm/env.json')
mgr.set('DATABASE_URL', 'postgres://localhost/dev')
```

### Batch Import from .env

```python
from evm import EnvironmentManager, ImportFailedError

mgr = EnvironmentManager()
try:
    msg = mgr.load('.env', format_type='env')
    print(msg)  # May include "Skipped N invalid key(s): ..."
except ImportFailedError as e:
    print(f"Import failed: {e}")
```

### Programmatic Validation

```python
mgr.set_schema('PORT', format='port', required=True)
mgr.set('PORT', '8080')

result = mgr.validate('PORT')
if result['valid']:
    print("OK")
else:
    for err in result['errors']:
        print(f"Error: {err}")
```

### Encrypted Secrets with Error Handling

```python
from evm import EnvironmentManager, DecryptionError, KeyNotFoundError

mgr = EnvironmentManager()

try:
    password = mgr.get_secret('DB_PASS')
except KeyNotFoundError:
    print("Secret not set. Use: mgr.set_secret('DB_PASS', 'value')")
except DecryptionError:
    print("Secret is corrupted or machine identity has changed")
```

### Agent Integration Pattern

```python
import json, subprocess

def evm_json(*args):
    """Run an EVM command and return parsed JSON data."""
    result = subprocess.run(
        ['evm', '--json', *args],
        capture_output=True, text=True
    )
    envelope = json.loads(result.stdout)
    if envelope['status'] == 'error':
        raise RuntimeError(envelope['error'])
    return envelope['data']

# Usage
all_vars = evm_json('list')
value = evm_json('get', 'API_KEY')['value']
```
