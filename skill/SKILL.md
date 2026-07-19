---
name: evm-agent
version: 2.6.2
description: Environment Variable Manager (EVM) CLI skill for AI agents. Use this skill whenever you need to manage environment variables, handle .env files, store/retrieve secrets, set up multi-environment configurations (dev/staging/prod), validate configuration values against schemas, run commands with specific environment contexts, or perform any task involving environment variable management. This includes scenarios like setting up environment configs, importing/exporting .env files, managing encrypted credentials, running applications with injected environment variables, backing up configurations, or automating environment variable workflows. Trigger this skill even if the user doesn't explicitly mention "EVM" — any environment variable, .env, or configuration management task should activate it.
---

# EVM Agent Skill

EVM (Environment Variable Manager) is a CLI tool for managing environment variables. This skill teaches you how to use it effectively as an agent.

## Installation

```bash
# Check if installed
evm --version

# Install from source (recommended for development)
pip install -e .

# Install with development dependencies (includes pytest, ruff, mypy)
pip install -e ".[dev]"

# Install from PyPI (if available)
pip install evm-cli
```

**Note**: EVM uses `pyproject.toml` for modern Python packaging (PEP 621). The `setup.py` is kept as a backward-compatibility shim.

## Core Principles for Agent Usage

### 1. Always Use `--json` for Structured Output

EVM supports `--json` on all commands. This gives you predictable, parseable output on stdout. Errors go to stderr as JSON.

**Important**: The `--json` flag can be placed **before or after** the subcommand (fixed in v2.0.1):

```bash
# Both forms work:
evm --json get API_KEY
evm get API_KEY --json

# stdout: {"status": "ok", "data": {"key": "API_KEY", "value": "abc123"}}
evm get API_KEY --json

# stdout: {"status": "ok", "data": {"API_KEY": "abc123", "DB_URL": "..."}}
evm list --json

# stderr: {"status": "error", "error": "...", "error_code": 2}
evm get MISSING --json
```

### 2. Use `--env-file` for Isolation

Never touch the user's default `~/.evm/env.json` unless explicitly asked. Use `--env-file` to create isolated storage:

```bash
evm --env-file /tmp/my_project.json set API_KEY abc123
evm --env-file /tmp/my_project.json list --json
```

### 3. Use `--force` for Non-Interactive Execution

Destructive operations (`clear`, `delete-group`) prompt for confirmation in interactive mode. Always use `--force` in agent contexts:

```bash
evm --force clear
evm --force delete-group staging
```

### 4. Use `--dry-run` to Preview Changes

Before executing write operations, preview what would happen:

```bash
evm --dry-run set API_KEY new_value --json
# stdout: {"status": "ok", "data": {"key": "API_KEY", "value": "new_value", "message": "[DRY-RUN] Would set: API_KEY=new_value"}}
```

### 5. Use `--quiet` to Suppress Human Output

When you only need the exit code or JSON data:

```bash
# Silent success check
evm --quiet set KEY value
echo $?  # 0 = success

# JSON-only mode
evm --json --quiet list
```

### 6. Silence the First-Run Shell-Integration Notice

On the **first** `evm` command a user runs, EVM auto-installs a shell-integration block into their rc file (`~/.zshrc` etc.) and prints a notice to stderr. This is harmless and idempotent, but in automation/agent contexts you usually want clean stderr. Set `EVM_NO_AUTO_INSTALL=1` to skip it entirely:

```bash
export EVM_NO_AUTO_INSTALL=1   # in the agent's environment
# or per-command:
EVM_NO_AUTO_INSTALL=1 evm --env-file config.json list --json
```

The `init`, `completion`, and `upgrade` commands never trigger auto-install.

## Exit Codes

EVM returns granular exit codes so you can distinguish error types without parsing messages:

| Code | Meaning | When to expect |
|------|---------|---------------|
| 0 | Success | Command completed |
| 1 | General error / cancelled | Unknown error or user cancel |
| 2 | Key not found | `get`/`delete` on missing variable |
| 3 | Storage error | Corrupt JSON, permission denied, lock timeout |
| 4 | Import/export error | Bad file format, file not found |
| 5 | Decryption error | Wrong format or tampered ciphertext |
| 6 | Validation/schema error | Value doesn't match schema |
| 7 | Group error | Group not found, can't delete default |
| 8 | Backup error | Backup file not found or corrupt |
| 9 | Editor error | $EDITOR failed |
| 10 | Command not found | `exec` target doesn't exist |

## Common Workflows

### Store and Retrieve Variables

```bash
# Store
evm --env-file config.json set DATABASE_URL "postgresql://localhost/mydb"

# Retrieve (parse JSON)
RESULT=$(evm --env-file config.json get DATABASE_URL --json 2>/dev/null)
VALUE=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['value'])")

# Check existence (exit code 2 = not found)
if evm --env-file config.json --quiet get DATABASE_URL 2>/dev/null; then
    echo "exists"
else
    echo "not found"
fi
```

### Multi-Environment Setup

```bash
# Create separate configs per environment
evm --env-file dev.json set DATABASE_URL "localhost:5432/dev"
evm --env-file staging.json set DATABASE_URL "staging.example.com:5432/staging"
evm --env-file prod.json set DATABASE_URL "prod.example.com:5432/prod"

# Or use groups in a single file
evm --env-file config.json setg dev DATABASE_URL "localhost:5432/dev"
evm --env-file config.json setg prod DATABASE_URL "prod.example.com:5432/prod"
evm --env-file config.json listg dev --json
```

### Import and Export

```bash
# Import .env file
evm --env-file config.json load .env

# Import JSON
evm --env-file config.json load config.json

# Export to .env format
evm --env-file config.json export --format env --output .env

# Export to shell script
evm --env-file config.json export --format sh --output env.sh

# Export specific group
evm --env-file config.json export --group prod --format env --output prod.env
```

### Encrypted Secrets

```bash
# Store encrypted (key derived from machine identity)
evm --env-file config.json set --secret DB_PASSWORD "super_secret"

# Retrieve decrypted
evm --env-file config.json get --secret DB_PASSWORD --json
# Note: stderr will show a WARNING about terminal scrollback if stdout is a TTY
```

**Important**: Encryption keys are derived from machine identity (hostname + uid + arch). Secrets cannot be migrated to different machines. Warn users about this limitation.

### Schema Validation

```bash
# Define schemas
evm --env-file config.json schema set API_URL --format url --required
evm --env-file config.json schema set PORT --format port
evm --env-file config.json schema set ADMIN_EMAIL --format email

# Validate all
evm --env-file config.json validate --json
# stdout: {"status": "ok", "data": {"API_URL": {"valid": true, ...}, "PORT": {"valid": true, ...}}}

# Available formats: url, email, port, integer, boolean, path, ipv4, ipv6
# Custom regex also supported:
evm --env-file config.json schema set API_KEY --pattern '^[a-zA-Z0-9]{32,}$'
```

### Run Commands with Environment

```bash
# Execute with all EVM variables injected
evm --env-file config.json exec -- python app.py
# Exit code is passed through from the child process

# Check child process exit code
evm --env-file config.json exec -- sh -c 'exit 1'
echo $?  # 1
```

### Backup and Restore

```bash
# Create backup
evm --env-file config.json backup --file backup_$(date +%Y%m%d).json

# Restore (replace mode)
evm --env-file config.json restore backup.json

# Restore (merge mode)
evm --env-file config.json restore backup.json --merge

# Compare current state with backup
evm --env-file config.json diff backup.json --json
```

### Template Expansion

```bash
# Set variables with template references
evm --env-file config.json set API_HOST "api.example.com"
evm --env-file config.json set API_URL "https://{{API_HOST}}/v1"

# Expand templates
evm --env-file config.json expand API_URL --json
# stdout: {"status": "ok", "data": {"key": "API_URL", "expanded": "https://api.example.com/v1"}}
```

### Operation History

```bash
# View recent operations
evm --env-file config.json history --json

# Clear history
evm --env-file config.json history --clear
```

### Load Variables into the Current Shell

A child process **cannot** modify its parent shell's environment, so `evm loadmemory` only affects the `evm` process itself (useless for an interactive shell). To actually load EVM variables into the current shell, use `evm inject` wrapped in `eval`:

```bash
# Load all plain (non-grouped) variables into the current shell
eval "$(evm --env-file config.json inject)"
echo "$API_KEY"   # now set in the current shell

# Load only a specific group (strips the group: prefix)
eval "$(evm --env-file config.json inject --group prod)"

# Also decrypt and inject secret variables
eval "$(evm --env-file config.json inject --include-secrets)"

# Namespace all keys to avoid collisions with existing env vars
eval "$(evm --env-file config.json inject --prefix EVM_)"

# Preview without eval-ing (human-readable)
evm --env-file config.json inject --dry-run

# Structured output (count, variables, skipped, output) for scripting
evm --env-file config.json inject --json
```

`--shell` defaults to the value detected from `$SHELL`; fish uses `set -gx KEY VALUE` instead of `export`. Grouped variables (e.g. `dev:DB_URL`) are **skipped by default** (invalid shell identifier) — use `--group dev` to strip the prefix and export them.

### Shell Integration Setup (`evm init` / `evm-load`)

Install `evm-load` (a shortcut for `eval "$(evm inject)"` that handles `--env-file` positioning) plus tab completion into the shell rc:

```bash
# Auto path: just use evm normally — first run installs the rc block.
# Manual control:
evm init zsh --install      # append integration block to ~/.zshrc
evm init zsh --check        # exit 0 = installed, 1 = not
evm init zsh --uninstall    # remove the block (preserves surrounding content)
evm init zsh --reinstall    # force re-add (useful if rc got out of sync)

# The block re-runs `evm init` on every shell start, so evm-load + completion
# stay in sync with the installed evm version automatically.

# After install, in the shell:
evm-load                           # ≡ eval "$(evm inject)"
evm-load --env-file config.json    # with project-specific storage
evm-load --group prod
```

Opt out of auto-install with `EVM_NO_AUTO_INSTALL=1` (see Core Principle 6).

### Self-Upgrade (`evm upgrade`)

Check PyPI for a newer `evm` release and pip-install it in one step (pure stdlib, no new dependencies):

```bash
# Check only — no changes (exit 0 = up to date, 1 = update available)
evm upgrade --check

# Actually upgrade (runs `pip install --upgrade evm-cli` with the current interpreter)
evm upgrade

# Preview the pip command without running it
evm upgrade --dry-run

# Skip the pre-check and run pip directly
evm upgrade --force

# Structured JSON output
evm upgrade --check --json
# {"status": "ok", "data": {"current": "2.6.0", "latest": "2.7.0", "update_available": true}}
```

If the network is unreachable, `--check` reports `latest: unknown` and exits 1; a plain `evm upgrade` aborts before touching pip.

## Python API Usage

EVM can also be used as a Python library:

```python
from evm.manager import EnvironmentManager
from evm.exceptions import (
    EVMError, KeyNotFoundError, KeyAlreadyExistsError,
    StorageError, DecryptionError, SchemaError, ImportFailedError
)

mgr = EnvironmentManager("/tmp/my_config.json")

# Basic CRUD
mgr.set("API_KEY", "abc123")
value = mgr.get("API_KEY")  # raises KeyNotFoundError if missing
mgr.delete("API_KEY")

# Encrypted secrets
mgr.set_secret("DB_PASS", "super_secret")
plain = mgr.get_secret("DB_PASS")  # auto-migrates v1/v2 → v3

# Schema validation
mgr.set_schema("URL", format="url", required=True)
result = mgr.validate("URL")  # {"valid": True, "errors": [], "warnings": []}

# Import/Export
mgr.load("config.env")
mgr.export("json", "/tmp/export.json")

# Groups
mgr.set_grouped("dev", "PORT", "3000")
mgr.list_groups()  # {"dev": 1}

# Templates
mgr.set("HOST", "localhost")
mgr.set("URL", "http://{{HOST}}:3000")
mgr.expand("URL")  # "http://localhost:3000"

# Shell injection — generate export text (consume via `eval` in a shell)
result = mgr.inject(shell="zsh", group="prod")
# {"shell": "zsh", "count": 3, "variables": [...], "skipped": [...], "output": "export ..."}
# inject() only *generates* text; it cannot set vars in the parent shell itself.
```

## Error Handling Patterns

### Shell Pattern

```bash
# Robust EVM call with error handling
evm_call() {
    local output
    local exit_code

    output=$(evm --env-file "$EVM_FILE" --json "$@" 2>/dev/null)
    exit_code=$?

    case $exit_code in
        0) echo "$output" ;;
        2) echo "Error: Variable not found" >&2 ;;
        3) echo "Error: Storage problem" >&2 ;;
        4) echo "Error: Import/export failed" >&2 ;;
        5) echo "Error: Decryption failed" >&2 ;;
        6) echo "Error: Validation failed" >&2 ;;
        *) echo "Error: Unknown (code $exit_code)" >&2 ;;
    esac

    return $exit_code
}
```

### Python Pattern

```python
from evm.manager import EnvironmentManager
from evm.exceptions import KeyNotFoundError, DecryptionError, SchemaError

mgr = EnvironmentManager("config.json")

try:
    value = mgr.get("API_KEY")
except KeyNotFoundError as e:
    print(f"Variable '{e.key}' not found")
except DecryptionError as e:
    print(f"Decryption failed: {e}")
except SchemaError as e:
    print(f"Schema violation: {e}")
```

## Architecture Notes for Agents

**Command Registry Pattern**: EVM uses a command registry pattern (introduced in v2.1.0) where each CLI command is a standalone handler function registered in `COMMAND_HANDLERS`. This makes it easy to:
- Add new commands by creating handler functions
- Test commands in isolation
- Extend EVM with plugins

**Module Organization**:
- `cli.py`: CLI parsing and command dispatch
- `manager.py`: Core business logic (CRUD, templates, execution, inject)
- `_io.py`: Import/export/backup/restore (IOMixin)
- `_groups.py`: Namespace/group management (GroupMixin)
- `_history.py`: Operation logging (HistoryMixin)
- `_schema.py`: Validation schemas (SchemaMixin)
- `_crypto.py`: HKDF + HMAC-CTR encryption
- `_completion.py`: Shell completion generators + rc-file integration (`evm init`/`evm-load`)
- `_upgrade.py`: PyPI version check + pip self-upgrade (`evm upgrade`)
- `_json.py`: JSON output helpers (`json_output`/`json_error`)
- `_typing.py`: Shared typing helpers (Protocol mixin base)
- `formatters.py`: Terminal output formatting
- `exceptions.py`: Exception hierarchy

When debugging issues, check the relevant module based on the operation type.

## Security Considerations

1. **File permissions**: EVM automatically sets `chmod 600` on storage files, backups, schema files, and history files
2. **Shell export safety**: Both keys and values are escaped with `shlex.quote()` in `.sh` exports
3. **Import key validation**: `.env` imports reject keys that don't match `^[A-Za-z_][A-Za-z0-9_]*$`
4. **Secret storage**: Uses HKDF key separation + HMAC-CTR encryption + Encrypt-then-MAC (v3 format)
5. **Machine binding**: Encryption keys are derived from machine identity — secrets cannot cross machines
6. **History safety**: `set` operations do not log plaintext values to history

## Reference

For complete command reference, read `references/command-reference.md`.
For detailed exit code mapping, read `references/exit-codes.md`.
For Python API patterns, read `references/python-api.md`.
For security architecture, read `references/security.md`.

## Agent Quick Reference

Common patterns you can copy-paste:

### Check if variable exists
```bash
if evm --env-file config.json --quiet get KEY 2>/dev/null; then
    echo "exists"
else
    echo "not found (exit code 2)"
fi
```

### Get variable value safely
```bash
VALUE=$(evm --env-file config.json get KEY --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['value'])")
```

### Set variable with dry-run preview
```bash
evm --env-file config.json set KEY value --dry-run --json
# Review output, then execute without --dry-run
evm --env-file config.json set KEY value --json
```

### Multi-environment setup
```bash
for env in dev staging prod; do
    evm --env-file ${env}.json set DATABASE_URL "${env}.example.com:5432/db"
    evm --env-file ${env}.json set LOG_LEVEL "debug"
done
```

### Validate all variables
```bash
RESULT=$(evm --env-file config.json validate --json)
INVALID=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print([k for k,v in d.items() if not v['valid']])")
if [ "$INVALID" != "[]" ]; then
    echo "Validation failed for: $INVALID"
    exit 1
fi
```

### Run command with environment
```bash
evm --env-file config.json exec -- python app.py
# Exit code from app.py is passed through
```

### Backup before changes
```bash
evm --env-file config.json backup --file backup_$(date +%Y%m%d_%H%M%S).json
# Make changes...
# Restore if needed:
# evm --env-file config.json restore backup_file.json
```
