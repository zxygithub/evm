# EVM Python API Reference

## EnvironmentManager

The core class for all EVM operations.

### Initialization

```python
from evm.manager import EnvironmentManager

# Default storage (~/.evm/env.json)
mgr = EnvironmentManager()

# Custom storage file
mgr = EnvironmentManager("/path/to/config.json")

# Custom lock timeout (default: 5 seconds)
mgr = EnvironmentManager(lock_timeout=10.0)
```

### CRUD Operations

```python
# Set
mgr.set("KEY", "value")                    # Returns: "Set: KEY=value"
mgr.set("KEY", "value", dry_run=True)      # Returns: "[DRY-RUN] Would set: KEY=value"

# Get (raises KeyNotFoundError if missing)
value = mgr.get("KEY")                     # Returns: "value"

# Delete (raises KeyNotFoundError if missing)
mgr.delete("KEY")                          # Returns: "Deleted: KEY"

# Exists
mgr.exists("KEY")                          # Returns: True/False

# List
mgr.list_vars()                            # Returns: {"KEY": "value", ...}
mgr.list_vars(pattern="API")              # Filter by pattern
mgr.list_vars(group="dev")               # Filter by group
mgr.list_vars(group="dev", no_prefix=True) # Remove group prefix

# Clear
mgr.clear()                                # Returns: "All environment variables cleared (N variables)"
```

### Encrypted Secrets

```python
# Store encrypted (v3 format: HKDF + HMAC-CTR + Encrypt-then-MAC)
mgr.set_secret("DB_PASS", "super_secret")

# Retrieve decrypted (auto-migrates v1/v2 → v3)
plain = mgr.get_secret("DB_PASS")

# Note: set_secret returns a warning on first use about machine binding
```

### Groups

```python
# Set/Get/Delete in groups
mgr.set_grouped("dev", "PORT", "3000")
value = mgr.get_grouped("dev", "PORT")
mgr.delete_grouped("dev", "PORT")

# List groups
groups = mgr.list_groups()  # {"dev": 3, "prod": 5}

# Delete entire group
mgr.delete_group("dev")

# Move between groups
mgr.move_to_group("KEY", "prod")
```

### Import / Export

```python
# Load from file
mgr.load("config.env")                           # Auto-detect format
mgr.load("config.json", format_type="json")      # Force format
mgr.load("config.json", replace=True)            # Replace mode
mgr.load("config.json", group="staging")         # Add group prefix
mgr.load("nested.json", nest=True)               # Nested JSON (first-level keys as groups)

# Export
mgr.export("json", "/tmp/export.json")
mgr.export("env", "/tmp/export.env")
mgr.export("sh", "/tmp/export.sh")
mgr.export("json", group="prod")                 # Export specific group
```

### Backup / Restore

```python
# Backup
mgr.backup()                                     # Auto-timestamped
mgr.backup("/tmp/my_backup.json")                # Custom path

# Restore
mgr.restore("/tmp/backup.json")                  # Replace mode
mgr.restore("/tmp/backup.json", merge=True)      # Merge mode

# Diff
diff = mgr.diff("/tmp/backup.json")
# Returns: {"added": {}, "removed": {}, "changed": {}, "backup_timestamp": "..."}
```

### Schema Validation

```python
# Define schema
mgr.set_schema("API_URL", format="url", required=True)
mgr.set_schema("PORT", format="port")
mgr.set_schema("CODE", pattern=r'^[A-Z]{3}-\d{4}$')

# Available formats: url, email, port, integer, boolean, path, ipv4, ipv6

# Validate single
result = mgr.validate("API_URL")
# Returns: {"valid": True, "errors": [], "warnings": []}

# Validate all
results = mgr.validate_all()
# Returns: {"API_URL": {"valid": True, ...}, "PORT": {"valid": True, ...}}

# Get/Delete schema
schema = mgr.get_schema()                        # All definitions
schema = mgr.get_schema("API_URL")               # Single definition
mgr.delete_schema("API_URL")
```

### Templates

```python
mgr.set("HOST", "localhost")
mgr.set("URL", "http://{{HOST}}:3000")
expanded = mgr.expand("URL")  # "http://localhost:3000"

# Recursive expansion
mgr.set("BASE", "http://{{HOST}}")
mgr.set("API", "{{BASE}}/api")
mgr.expand("API")  # "http://localhost/api"
```

### Execution

```python
# Run command with EVM variables injected
exit_code = mgr.execute(["python", "app.py"])
# Returns: child process exit code
```

### Shell Injection

```python
# Generate shell-sourceable exports (for `eval "$(evm inject)"`)
result = mgr.inject(shell="zsh")
# Returns: {"shell": "zsh", "count": 5, "variables": ["API_KEY", ...],
#           "skipped": ["dev:DB_URL"], "output": "export API_KEY='...'\n..."}

result = mgr.inject(shell="bash", group="prod")          # strip group prefix
result = mgr.inject(shell="zsh", include_secrets=True)   # decrypt + inject secrets
result = mgr.inject(shell="bash", prefix="EVM_")         # namespace all keys

# In a shell script this is consumed via eval:
#   eval "$(evm inject --group prod)"
# `inject()` only *generates* the export text — it cannot modify the parent
# shell's environment (no child process can). The CLI's `eval` wrapper is what
# actually loads the vars.
```

### History

```python
# Get history (newest first)
entries = mgr.get_history(limit=20)
# Returns: [{"timestamp": "...", "operation": "set", "key": "KEY", ...}, ...]

# Clear history
mgr.clear_history()
```

### Tool Info

```python
info = mgr.info()
# Returns: {
#     "version": "2.6.0",   # derived from evm.__version__
#     "storage_path": "/path/to/env.json",
#     "total_variables": 10,
#     "total_groups": 3,
#     "secret_variables": 2,
#     "groups": {"dev": 3, "prod": 5},
#     ...
# }
```

## Exception Hierarchy

```
EVMError
├── KeyNotFoundError
├── KeyAlreadyExistsError
├── StorageError
│   ├── CorruptedStorageError
│   ├── StoragePermissionError
│   └── LockTimeoutError
├── ExportError
├── ImportFailedError
├── CommandNotFoundError
├── GroupNotFoundError
├── GroupOperationError
├── BackupError
├── EditorError
├── DecryptionError
├── ValidationError
├── SchemaError
└── OperationCancelledError
```

## Best Practices

1. **Always use try/except** around `get()` and `get_secret()` — they raise `KeyNotFoundError`/`DecryptionError`
2. **Use `exists()` for checks** instead of catching exceptions
3. **Use `dry_run=True`** to preview destructive operations
4. **Use isolated `env_file`** for agent-specific storage
5. **Don't log secret values** — `set_secret` doesn't log values, and neither should your code
