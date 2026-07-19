# EVM - Environment Variable Manager

A powerful command-line tool for managing environment variables on macOS and Linux systems.

**Version**: 2.6.2

## Features

- ✅ **Set/Get/Delete**: Manage environment variables
- ✅ **List/Search**: View and find variables easily
- ✅ **Import/Export**: JSON, .env, and shell script formats
- ✅ **Backup/Restore**: Timestamps and merge support
- ✅ **Groups**: Namespace-based organization
- ✅ **Execute**: Run commands with custom environment
- ✅ **Inject**: Load variables into the current shell via `eval "$(evm inject)"`
- ✅ **Load to Memory**: Sync variables to system environment
- ✅ **Secrets**: HKDF+HMAC-CTR encrypted storage (v3) with auto-migration from v1/v2
- ✅ **Templates**: `{{VAR}}` reference expansion
- ✅ **Diff**: Compare current state with backups
- ✅ **Dry-run**: Preview changes before writing
- ✅ **Validate**: Schema-based variable value validation (URL, email, port, etc.)
- ✅ **Schema**: Define and enforce variable formats and constraints
- ✅ **History**: Operation audit log with JSONL storage
- ✅ **Shell Completion**: bash, zsh, fish completion script generation
- ✅ **Shell Integration**: `evm init` auto-installs `evm-load` + completion into your rc on first use
- ✅ **Self-Upgrade**: `evm upgrade` checks PyPI and pip-installs the latest version
- ✅ **Interactive Safety**: Confirmation prompts for destructive operations (`--force` to skip)
- ✅ **JSON Output**: `--json` flag for structured output (agent-friendly, stdout=data, stderr=errors)
- ✅ **Quiet Mode**: `--quiet` suppresses all human-readable output
- ✅ **Granular Exit Codes**: 11 distinct codes for programmatic error handling
- ✅ **Secure**: Shell-safe export (key+value), chmod 600, atomic writes, shared lock file, HKDF key separation
- ✅ **Pure Python**: No external dependencies, Python 3.9+

## Platform Support

**Supported Platforms:**
- ✅ macOS (Darwin)
- ✅ Linux (POSIX-compliant systems)
- ❌ Windows (not supported - uses `fcntl` for file locking)

**Requirements:**
- Python 3.9 or higher
- POSIX-compliant operating system (for file locking with `fcntl`)

## Project Structure

```
evm/
├── evm/
│   ├── __init__.py           # Package init, version info
│   ├── __main__.py           # Module entry point
│   ├── cli.py                # CLI parsing and command dispatch
│   ├── manager.py            # Core business logic (CRUD, encryption, templates)
│   ├── _io.py                # IOMixin (import/export/backup/restore/diff)
│   ├── _groups.py            # GroupMixin (namespace management)
│   ├── _history.py           # HistoryMixin (operation logging)
│   ├── _schema.py            # SchemaMixin (format validation)
│   ├── _completion.py        # Shell completion generators (bash/zsh/fish)
│   ├── _json.py              # JSON output helpers (agent-friendly)
│   ├── _crypto.py            # HKDF + HMAC-CTR encryption module
│   ├── _upgrade.py           # Self-upgrade: PyPI version check + pip install
│   ├── _typing.py            # Shared typing helpers (Protocol mixins)
│   ├── formatters.py         # Terminal output formatting
│   └── exceptions.py         # Custom exception hierarchy (17 classes)
├── examples/                 # Example scripts
├── tests/                    # Test suite
│   ├── test_main.py          # Unit + integration tests
│   ├── test_inject.py        # `evm inject` + `evm-load` tests
│   ├── test_shell_integration.py  # `evm init` + auto-install tests
│   ├── test_upgrade.py       # `evm upgrade` tests
│   ├── test_io_boundary.py   # _io.py boundary tests
│   ├── test_cli_boundary.py  # cli.py boundary tests
│   ├── test_cli_additional.py  # cli.py additional coverage
│   ├── test_cli_coverage.py  # cli.py coverage gap tests
│   ├── test_main_entry.py    # `evm` entry-point tests
│   ├── test_main_module.py   # `python -m evm` entry tests
│   ├── test_v230_fixes.py    # v2.3.0 code review fix tests
│   ├── test_coverage_gap.py  # Coverage gap tests (98% target)
│   ├── test_formatters.py    # Formatter output tests
│   └── test_case/            # Test configuration files
├── docs/
│   ├── API_REFERENCE.md      # Python API reference
│   ├── CHANGELOG.md          # Version history
│   ├── DEVELOPMENT_REVIEW.md # Development review & roadmap
│   ├── ANALYSIS.md           # Project analysis report
│   ├── USER_GUIDE_CN.md      # 中文系统功能说明书
│   ├── AGENT_CLI_EVALUATION.md
│   ├── CODE_REVIEW.md
│   ├── CODE_REVIEW_v2.0.0_FINAL.md
│   └── CODE_REVIEW_v2.2.0.md
├── skill/                    # AI Agent Skill (evm-agent)
├── pyproject.toml            # PEP 621 project metadata & tool config
├── setup.py                  # Backward-compatible setup shim
├── requirements.txt          # Thin wrapper pointing to pyproject.toml
├── README.md                 # This file
├── LICENSE                   # MIT License
└── Makefile                  # Build automation
```

## Quick Start

### Installation

```bash
# Core install (no third-party dependencies)
pip install .

# Development install (includes pytest, ruff, mypy)
pip install ".[dev]"

# Test-only install
pip install ".[test]"

# Lint-only install
pip install ".[lint]"

# From source (editable/development mode)
pip install -e ".[dev]"

# For current user only
pip install --user -e ".[dev]"

# Verify installation
evm --version
evm --help
```

### Run as Module

```bash
python -m evm --help
```

### Your First 5 Minutes with EVM

**1. Basic Operations**

```bash
# Set a variable
evm set API_KEY "abc123"

# Get the value back
evm get API_KEY
# Output: abc123

# List all variables
evm list
# Shows all stored variables in a table format
```

**2. Use Isolated Storage (Recommended)**

By default, EVM uses `~/.evm/env.json`. For project-specific configs, use `--env-file`:

```bash
# Create a project-specific config
evm --env-file ./project.json set DATABASE_URL "postgresql://localhost/mydb"
evm --env-file ./project.json set API_KEY "project_secret"

# Only affects this file, not your global config
evm --env-file ./project.json list
```

**3. JSON Output for Scripts & Agents**

Use `--json` to get structured output (works before or after the command):

```bash
# Get as JSON (both work)
evm --env-file ./project.json --json get API_KEY
evm --env-file ./project.json get API_KEY --json
# stdout: {"status": "ok", "data": {"key": "API_KEY", "value": "project_secret"}}

# List all as JSON
evm --env-file ./project.json list --json
# stdout: {"status": "ok", "data": {"API_KEY": "project_secret", "DATABASE_URL": "..."}}

# Errors go to stderr with error codes
evm --env-file ./project.json get MISSING --json
# stderr: {"status": "error", "error": "Environment variable 'MISSING' not found", "error_code": 2}
# exit code: 2
```

**4. Preview Changes with Dry-Run**

```bash
# Preview what would happen without actually writing
evm --env-file ./project.json set NEW_KEY "value" --dry-run
# Output: [DRY-RUN] Would set: NEW_KEY=value
# (Nothing is actually written)

# Works with delete, clear, etc.
evm --env-file ./project.json delete API_KEY --dry-run
# Output: [DRY-RUN] Would delete: API_KEY
```

**5. Manage Multiple Environments**

Use groups to organize dev/staging/prod configurations:

```bash
# Set variables for different environments
evm --env-file ./project.json setg dev DATABASE_URL "localhost:5432/dev"
evm --env-file ./project.json setg prod DATABASE_URL "prod.example.com:5432/prod"

# List by group
evm --env-file ./project.json listg dev
# Shows only dev group variables

# List all groups
evm --env-file ./project.json groups
# Shows: dev (1 variable), prod (1 variable)

# Export a specific environment
evm --env-file ./project.json export --group prod --format env -o .env.prod
```

**6. Encrypt Sensitive Data**

```bash
# Store encrypted (HKDF + HMAC-CTR encryption)
evm --env-file ./project.json set --secret DB_PASSWORD "super_secret_password"

# Retrieve decrypted
evm --env-file ./project.json get --secret DB_PASSWORD
# Output: super_secret_password
# Warning: Decrypted secret displayed on terminal (visible in scrollback).

# Note: Encryption keys are machine-bound (hostname + uid + arch)
# Secrets cannot be migrated to different machines
```

**7. Run Commands with Environment Variables**

```bash
# Run a command with all EVM variables injected
evm --env-file ./project.json exec -- python app.py
# Your app can access DATABASE_URL, API_KEY, etc. from os.environ

# Exit codes are passed through from the child process
evm --env-file ./project.json exec -- sh -c 'exit 42'
echo $?  # Output: 42
```

**8. Validate Configuration**

```bash
# Define schemas for validation
evm --env-file ./project.json schema set DATABASE_URL --format url --required
evm --env-file ./project.json schema set API_KEY --pattern '^[a-zA-Z0-9]+$'

# Validate all variables
evm --env-file ./project.json validate
# Shows which variables pass/fail validation

# Validate a specific variable
evm --env-file ./project.json validate DATABASE_URL
```

**9. Backup and Restore**

```bash
# Create a backup
evm --env-file ./project.json backup --file backup.json

# Make some changes
evm --env-file ./project.json set NEW_VAR "value"

# Compare with backup
evm --env-file ./project.json diff backup.json
# Shows what was added/removed/changed

# Restore from backup
evm --env-file ./project.json restore backup.json
```

**10. Quick Reference**

```bash
# Essential flags
--env-file PATH    # Use custom storage file
--json             # Structured JSON output
--dry-run          # Preview changes
--quiet / -q       # Suppress output
--force            # Skip confirmation prompts

# Common commands
evm set KEY VALUE          # Set a variable
evm get KEY                # Get a variable
evm list                   # List all variables
evm delete KEY             # Delete a variable
evm setg GROUP KEY VALUE   # Set in a group
evm groups                 # List groups
evm exec -- COMMAND        # Run with env vars
eval "$(evm inject)"       # Load vars into current shell
evm backup                 # Create backup
evm validate               # Check schemas
evm upgrade                # Upgrade to latest PyPI release
evm upgrade --check        # Check for updates only
```

## Usage

### Basic Commands

```bash
# Set a variable
evm set API_KEY your_secret_key
evm set DATABASE_URL "postgresql://localhost/mydb"

# Get a variable
evm get API_KEY

# List all variables
evm list

# Delete a variable
evm delete API_KEY

# Clear all
evm clear
```

### Group Management

```bash
# Set variables in groups
evm setg dev API_URL http://localhost:3000
evm setg prod API_URL https://api.example.com

# List variables in a group
evm listg dev

# List all groups
evm groups

# Show variables grouped by namespace
evm list --show-groups

# Move variable to group
evm move-group API_KEY prod

# Delete entire group
evm delete-group test
```

### Import/Export

```bash
# Export to different formats
evm export --format json -o config.json
evm export --format env -o .env
evm export --format sh -o export.sh

# Import from file (auto-detects format)
evm load config.json
evm load config.env

# Import with options
evm load config.json --replace    # Replace existing
evm load config.json --group dev  # Add to group
evm load config.json --nest       # Import nested JSON (first-level keys as groups)
```

### Backup & Restore

```bash
# Create backup (auto-timestamped)
evm backup

# Backup to specific file
evm backup --file mybackup.json

# Restore
evm restore backup.json
evm restore backup.json --merge   # Merge with existing
```

### Load to System Memory

> ⚠️ **Scope note**: `evm loadmemory` sets `os.environ` inside the **evm process itself**. When the CLI command exits, those variables are gone — your interactive shell does **not** see them. Use `evm inject` (below) to get variables into the current shell, or `manager.load_to_memory()` from a Python script to set them in your own process.

```bash
# Load all variables to memory (with EVM: prefix)
evm loadmemory

# Load without prefix
evm loadmemory --no-prefix

# Load with filter
evm loadmemory --prefix DEMO_

# Only meaningful when called from a Python script that imports evm:
#   from evm import EnvironmentManager
#   EnvironmentManager().load_to_memory()
```

### Inject to Current Shell

`evm inject` prints shell-sourceable `export` statements to stdout. Wrap it in `eval "$( ... )"` to load variables into your **current** shell session:

```bash
# Inject all non-grouped variables into the current shell
eval "$(evm inject)"

# Verify they're now in your shell
echo "$API_KEY"

# Target a specific shell (auto-detected from $SHELL by default)
eval "$(evm inject --shell bash)"
eval "$(evm inject --shell fish)"   # fish uses `set -gx KEY VALUE`

# Inject only a group's variables (the `group:` prefix is stripped)
eval "$(evm inject --group prod)"

# Add a prefix to every exported key
eval "$(evm inject --prefix EVM_)"

# Also decrypt and inject secret variables (stored with --secret)
eval "$(evm inject --include-secrets)"

# Preview what would be injected, without eval-ing it
evm inject --dry-run

# Structured output for scripts/agents
evm inject --json
```

How `inject` decides what to export:

| Variable kind | Default | With flag |
|---|---|---|
| Plain (e.g. `API_KEY`) | ✅ exported | — |
| Grouped (e.g. `dev:DB_URL`) | ⏭️ silently skipped (invalid shell identifier) | `--group dev` strips the prefix and exports |
| Secret (stored with `--secret`) | ⏭️ skipped (would leak ciphertext) | `--include-secrets` decrypts and exports |
| Invalid shell identifier | ⏭️ skipped, reported in `--json`/`--dry-run` | — |

### The `evm-load` shortcut

Installing shell completion (see [Shell Completion](#shell-completion)) also defines an `evm-load` shell function that wraps `eval "$(evm inject)"` for you. It correctly handles the `--env-file` global-flag positioning so you don't have to:

```bash
# After sourcing the completion script (bash/zsh/fish), just:
evm-load                              # inject from default ~/.evm/env.json
evm-load --env-file ./project.json    # inject from a project-specific file
evm-load --group prod                 # inject only the prod group
evm-load --include-secrets            # also decrypt and inject secrets
evm-load --prefix EVM_                # namespace all keys to avoid collisions

# Verify
echo "$API_KEY"
```

Without completion installed, you can still type the `eval` form by hand, or add the alias yourself:

```bash
# ~/.zshrc or ~/.bashrc
alias evm-load='eval "$(evm inject)"'
```

### Execute Commands

```bash
# Run with environment variables
evm exec -- python script.py
evm exec -- npm start
```

### Search

```bash
# Search by key
evm search api

# Search by key and value
evm search localhost --value
```

## Storage

Environment variables are stored as JSON in `~/.evm/env.json`:

```json
{
  "API_KEY": "secret123",
  "dev:DATABASE_URL": "localhost:5432",
  "prod:DATABASE_URL": "prod.example.com:5432"
}
```

Use custom storage:
```bash
evm --env-file /path/to/custom.json list
```

### Secrets (Encrypted Variables)

> ⚠️ **Machine-bound encryption**: Encryption keys are derived from machine identity (hostname + uid + arch). Changing hostname, migrating to another machine, or rebuilding Docker containers will make secrets unrecoverable. Use a dedicated secrets manager (Vault, AWS Secrets Manager) for cross-machine scenarios.

```bash
# Store an encrypted secret
evm set --secret DB_PASSWORD "super_secret_password"

# Retrieve and decrypt
evm get --secret DB_PASSWORD
```

### Template Expansion

```bash
# Use {{VAR}} references
evm set API_HOST "api.example.com"
evm set API_URL "https://{{API_HOST}}/v1"

# Expand templates
evm expand API_URL   # → https://api.example.com/v1
```

### Diff

```bash
# Compare current state with a backup
evm diff backup_20260530_120000.json
```

### Dry-run

```bash
# Preview changes without writing
evm --dry-run set NEW_KEY value
evm --dry-run delete EXISTING_KEY
evm --dry-run clear
```

### Schema & Validate

```bash
# Define schemas for variables
evm schema set API_URL --format url --required
evm schema set PORT --format port
evm schema set EMAIL --format email --description "Admin email"

# Available formats: url, email, port, integer, boolean, path, ipv4, ipv6
# Custom regex also supported:
evm schema set CODE --pattern '^[A-Z]{3}-\d{4}$'

# List all schemas
evm schema list

# Validate a specific variable
evm validate API_URL

# Validate all variables with schemas
evm validate

# Delete a schema
evm schema delete API_URL
```

### History

```bash
# View operation history (latest first)
evm history

# Show more entries
evm history --limit 50

# Clear history
evm history --clear
```

### Self-Upgrade (`evm upgrade`)

Check PyPI for a newer `evm` release and pip-install it in one step. Uses only the standard library — no extra dependencies.

```bash
# Check whether a newer version is available (no changes made)
evm upgrade --check
# exit 0 = up to date, exit 1 = update available (or network error)

# Upgrade to the latest release
evm upgrade
#  → Upgraded from 2.5.0 to 2.6.0.

# Preview the pip command without running it
evm upgrade --dry-run

# Skip the pre-check and run pip directly
evm upgrade --force

# Structured JSON output (stdout = data, stderr = errors)
evm upgrade --check --json
# stdout: {"status": "ok", "data": {"current": "2.5.0", "latest": "2.6.0", "update_available": true}}

evm upgrade --json
# stdout: {"status": "ok", "data": {"current": "2.5.0", "new_version": "2.6.0", "action": "upgraded", "upgraded": true, "message": "Upgraded from 2.5.0 to 2.6.0."}}
```

`evm upgrade` calls `pip install --upgrade evm-cli` using the **same Python interpreter** that runs `evm`, so it upgrades the correct installation. If the network is unreachable, `--check` reports `unknown` and exits 1; a plain `evm upgrade` aborts before touching pip.

### Shell Integration (`evm init`)

EVM can install a shell-integration snippet into your rc file (`~/.zshrc`, `~/.bashrc`, `~/.config/fish/config.fish`). The snippet is **one line** that re-evaluates `evm init` on every shell start — so `evm-load`, tab completion, and any future integration stay in sync with the installed `evm` version automatically (no need to re-install after an upgrade).

**Auto-install on first use:** the first time you run any `evm` command, EVM detects your shell from `$SHELL`, appends the integration block to the matching rc file, and prints a notice to stderr. Subsequent commands skip (idempotent). This is the zero-config path — you don't have to do anything.

```bash
# Just use evm normally — on first run it prints:
#   Installed evm shell integration to ~/.zshrc
#   Restart your shell (or source the rc file) to enable `evm-load` and tab completion.
#   Set EVM_NO_AUTO_INSTALL=1 to skip this.

# After restarting the shell, both `evm-load` and tab completion are available.
```

**Manual control** (if you prefer explicit, or the auto-install didn't fit your setup):

```bash
# Explicitly install (same as what auto-install does, but on demand)
evm init zsh --install        # or bash / fish

# Check whether it's installed
evm init zsh --check          # exit 0 = installed, 1 = not

# Remove the integration block from your rc file
evm init zsh --uninstall

# Force re-add (useful if your rc got out of sync)
evm init zsh --reinstall
```

**What the rc block looks like** (conda-style markers, easy to grep/remove):

```bash
# >>> evm shell integration >>>
# Auto-added by evm. Remove with: evm init zsh --uninstall
eval "$(evm init zsh)"
# <<< evm shell integration <<<
```

**Opt out of auto-install** — if you don't want EVM touching your rc file automatically:

```bash
export EVM_NO_AUTO_INSTALL=1   # in your rc, or just for one command:
EVM_NO_AUTO_INSTALL=1 evm get API_KEY
```

> 💡 The integration block installs both **tab completion** and the **`evm-load`** function (a shortcut for `eval "$(evm inject)"` that handles `--env-file` positioning). See [The `evm-load` shortcut](#the-evm-load-shortcut).

### Shell Completion

```bash
# Generate and install bash completion
evm completion bash > ~/.evm-completion.bash
echo 'source ~/.evm-completion.bash' >> ~/.bashrc

# zsh
evm completion zsh > ~/.evm-completion.zsh
echo 'source ~/.evm-completion.zsh' >> ~/.zshrc

# fish
evm completion fish > ~/.config/fish/completions/evm.fish
```

> 💡 Each completion script also installs an **`evm-load`** shell function — a shortcut for `eval "$(evm inject)"` that handles `--env-file` flag positioning for you. See [The `evm-load` shortcut](#the-evm-load-shortcut) above.

### Interactive Safety

```bash
# clear and delete-group now prompt for confirmation
evm clear                        # Asks: "This will clear all N variables. Continue? [y/N]"
evm delete-group dev             # Asks: "This will delete group 'dev'... Continue? [y/N]"

# Skip confirmation with --force
evm --force clear
evm --force delete-group dev
```

## Agent-Friendly Usage

EVM is designed to be easily called by AI agents and scripts:

### JSON Output (`--json`)

All commands support structured JSON output. stdout contains data, stderr contains errors:

```bash
# Get a variable as JSON
evm get API_KEY --json
# stdout: {"status": "ok", "data": {"key": "API_KEY", "value": "secret123"}}

# List all variables
evm list --json
# stdout: {"status": "ok", "data": {"API_KEY": "secret123", "DB_URL": "..."}}

# Errors go to stderr as JSON
evm get MISSING --json
# stderr: {"status": "error", "error": "Environment variable 'MISSING' not found", "error_code": 2}
# exit code: 2
```

### Quiet Mode (`--quiet` / `-q`)

Suppress all human-readable output. Combined with `--json`, only structured data on stdout:

```bash
evm --quiet set KEY value        # No output, exit code 0
evm --quiet get MISSING          # No output, exit code 2
evm --json --quiet list          # No stdout, only exit code
```

### Granular Exit Codes

| Code | Meaning | Exception Type |
|------|---------|---------------|
| 0 | Success | — |
| 1 | General error / cancelled | OperationCancelledError |
| 2 | Variable not found | KeyNotFoundError, KeyAlreadyExistsError |
| 3 | Storage error | StorageError, CorruptedStorageError, LockTimeoutError |
| 4 | Import/export format error | ImportError, ExportError |
| 5 | Decryption error | DecryptionError |
| 6 | Validation/schema error | ValidationError, SchemaError |
| 7 | Group error | GroupNotFoundError, GroupOperationError |
| 8 | Backup error | BackupError |
| 9 | Editor error | EditorError |
| 10 | Command not found | CommandNotFoundError |

### Agent Usage Patterns

```bash
# Read a value (parse JSON from stdout)
VALUE=$(evm get API_KEY --json | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['value'])")

# Check if variable exists
if evm get KEY --quiet 2>/dev/null; then echo "exists"; fi

# Conditional set with dry-run preview
evm --dry-run set KEY value --json    # Preview without writing

# Execute with env vars (exit code is passed through)
evm exec -- python script.py
echo "Script exited with: $?"

# Use --env-file for isolated storage (no interference with user config)
evm --env-file /tmp/agent_env.json set KEY value
evm --env-file /tmp/agent_env.json --json list
```

## Python API

EVM can also be used as a Python library. See [**API Reference**](docs/API_REFERENCE.md) for full documentation.

```python
from evm import EnvironmentManager, EVMError, KeyNotFoundError

manager = EnvironmentManager()                    # default: ~/.evm/env.json
# manager = EnvironmentManager('/path/to/env.json')  # custom storage

# Basic operations
manager.set('API_KEY', 'secret123')
value = manager.get('API_KEY')
manager.set_grouped('dev', 'DEBUG', 'true')

# Encrypted secrets (HKDF+HMAC-CTR v3, auto-migration from v1/v2)
manager.set_secret('DB_PASS', 'encrypted_value')
plain = manager.get_secret('DB_PASS')

# Schema validation
manager.set_schema('API_URL', format='url', required=True)
result = manager.validate('API_URL')       # {'valid': True, 'errors': [], 'warnings': []}
all_results = manager.validate_all()

# Operation history
history = manager.get_history(limit=10)

# Template expansion
manager.set('HOST', 'example.com')
manager.set('URL', 'https://{{HOST}}/api')
expanded = manager.expand('URL')           # → https://example.com/api

# Import / Export / Backup
manager.load('.env')
manager.export(format_type='env', output_file='.env')
manager.backup()

# Error handling — all exceptions inherit EVMError
try:
    manager.get('MISSING')
except KeyNotFoundError as e:
    print(f"Not found: {e.key}")
except EVMError as e:
    print(f"EVM error: {e}")
```

## Development

```bash
# Install for development (includes pytest, ruff, mypy)
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=evm --cov-report=term-missing

# Lint with ruff
ruff check evm/ tests/

# Auto-fix lint issues
ruff check --fix evm/ tests/

# Type check with mypy
mypy evm/

# Run demo
make demo
```

## Examples

### Development Workflow

```bash
# Setup dev environment
evm setg dev NODE_ENV development
evm setg dev API_URL http://localhost:3000
evm setg dev DEBUG true

# Export for team
evm export --format env -o .env

# Run application
evm exec -- npm start
```

### Multi-Environment Management

```bash
# Setup environments
evm setg dev DATABASE_URL "localhost:5432/dev"
evm setg test DATABASE_URL "test-server:5432/test"
evm setg prod DATABASE_URL "prod-server:5432/prod"

# View all
evm list --show-groups

# Export specific environment
evm listg dev
evm export --group dev --format env
```

## Requirements

- **Python 3.9+**
- **No external dependencies** (uses only standard library)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
