# EVM - Environment Variable Manager

A powerful command-line tool for managing environment variables on macOS and Linux systems.

**Version**: 2.0.0

## Features

- ✅ **Set/Get/Delete**: Manage environment variables
- ✅ **List/Search**: View and find variables easily
- ✅ **Import/Export**: JSON, .env, and shell script formats
- ✅ **Backup/Restore**: Timestamps and merge support
- ✅ **Groups**: Namespace-based organization
- ✅ **Execute**: Run commands with custom environment
- ✅ **Load to Memory**: Sync variables to system environment
- ✅ **Secrets**: HKDF+HMAC-CTR encrypted storage (v3) with auto-migration from v1/v2
- ✅ **Templates**: `{{VAR}}` reference expansion
- ✅ **Diff**: Compare current state with backups
- ✅ **Dry-run**: Preview changes before writing
- ✅ **Validate**: Schema-based variable value validation (URL, email, port, etc.)
- ✅ **Schema**: Define and enforce variable formats and constraints
- ✅ **History**: Operation audit log with JSONL storage
- ✅ **Shell Completion**: bash, zsh, fish completion script generation
- ✅ **Interactive Safety**: Confirmation prompts for destructive operations (`--force` to skip)
- ✅ **JSON Output**: `--json` flag for structured output (agent-friendly, stdout=data, stderr=errors)
- ✅ **Quiet Mode**: `--quiet` suppresses all human-readable output
- ✅ **Granular Exit Codes**: 11 distinct codes for programmatic error handling
- ✅ **Secure**: Shell-safe export (key+value), chmod 600, atomic writes, shared lock file, HKDF key separation
- ✅ **Pure Python**: No external dependencies, Python 3.6+

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
│   ├── formatters.py         # Terminal output formatting
│   └── exceptions.py         # Custom exception hierarchy (17 classes)
├── examples/                 # Example scripts
├── tests/                    # Test suite (225 tests)
│   ├── test_main.py          # Unit + integration tests
│   ├── run_tests.py          # Integration test runner
│   └── test_case/            # Test configuration files
├── docs/
│   ├── CHANGELOG.md          # Version history
│   └── ANALYSIS.md           # Project analysis report
├── README.md                 # This file
├── LICENSE                   # MIT License
├── Makefile                  # Build automation
├── setup.py                  # Python package setup
└── requirements.txt          # Python dependencies
```

## Quick Start

### Installation

```bash
# From source (development mode)
pip install -e .

# For current user only
pip install --user -e .

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
evm backup                 # Create backup
evm validate               # Check schemas
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

```bash
# Load all variables to memory (with EVM: prefix)
evm loadmemory

# Load without prefix
evm loadmemory --no-prefix

# Load with filter
evm loadmemory --prefix DEMO_

# Check in Python
python -c "import os; print(os.environ.get('EVM:API_KEY'))"
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

EVM can also be used as a Python library:

```python
from evm.manager import EnvironmentManager
from evm.exceptions import EVMError, KeyNotFoundError, ImportFailedError
from evm.formatters import print_vars_table, print_validate_all

manager = EnvironmentManager()

# Basic operations
manager.set('API_KEY', 'secret123')
value = manager.get('API_KEY')
manager.set_grouped('dev', 'DEBUG', 'true')

# Encrypted secrets (HKDF+HMAC-CTR v3, auto-migration from v1/v2)
manager.set_secret('DB_PASS', 'encrypted_value')
plain = manager.get_secret('DB_PASS')

# Schema validation
manager.set_schema('API_URL', format='url', required=True)
result = manager.validate('API_URL')
all_results = manager.validate_all()

# Operation history
history = manager.get_history(limit=10)

# Template expansion
manager.set('HOST', 'example.com')
manager.set('URL', 'https://{{HOST}}/api')
expanded = manager.expand('URL')  # → https://example.com/api

# List variables
print_vars_table(manager.list_vars())

# Handle errors properly
try:
    manager.get('MISSING')
except KeyNotFoundError as e:
    print(f"Not found: {e.key}")
```

## Development

```bash
# Install for development
pip install -e .

# Run tests
make test

# Run tests with coverage
make test-coverage

# Lint
make lint

# Format code
make format

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

- **Python 3.6+**
- **No external dependencies** (uses only standard library)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
