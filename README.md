# EVM - Environment Variable Manager

A powerful command-line tool for managing environment variables on macOS and Linux systems.

## Features

- ✅ **Set**: Add or update environment variables
- ✅ **Get**: Retrieve environment variable values
- ✅ **Delete**: Remove environment variables
- ✅ **List**: List all or filtered environment variables
- ✅ **Clear**: Clear all environment variables
- ✅ **Export**: Export to JSON, .env, or shell script formats
- ✅ **Import**: Import from JSON, .env, or backup files with advanced options
- ✅ **Execute**: Run commands with custom environment variables
- ✅ **Rename**: Rename environment variables
- ✅ **Copy**: Copy environment variables
- ✅ **Search**: Search environment variables by key or value
- ✅ **Backup**: Create backups with timestamps
- ✅ **Restore**: Restore from backups (replace or merge)
- ✅ **Groups**: Manage environment variables by namespace/groups
- ✅ **Grouped Operations**: Set, get, delete, and list variables in specific groups

## Installation

```bash
# Clone the repository
git clone https://github.com/example/evm.git
cd evm

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

## Usage

### Basic Commands

#### Set an environment variable
```bash
evm set API_KEY abc123
evm set DATABASE_URL "postgresql://user:pass@localhost/db"
```

#### Get an environment variable
```bash
evm get API_KEY
```

#### List all environment variables
```bash
evm list
```

#### List filtered environment variables
```bash
evm list API
```

#### Delete an environment variable
```bash
evm delete API_KEY
```

#### Clear all environment variables
```bash
evm clear
```

### Advanced Commands

#### Rename an environment variable
```bash
evm rename OLD_KEY NEW_KEY
```

#### Copy an environment variable
```bash
evm copy SRC_KEY DST_KEY
```

#### Search environment variables
```bash
# Search by key
evm search api

# Search by key and value
evm search api --value
```

### Import/Export

#### Export to JSON (default)
```bash
evm export
evm export --output myenv.json
```

#### Export to .env format
```bash
evm export --format env
evm export -f env -o myenv.env
```

#### Export to shell script
```bash
evm export --format sh -o export.sh
```

#### Import from JSON (auto-detect)
```bash
evm load config.json
```

#### Import from .env file (auto-detect)
```bash
evm load config.env
```

#### Import with forced format
```bash
evm load config.txt --format json
evm load config.txt --format env
```

#### Import in replace mode
```bash
evm load config.json --replace
```

#### Import to a specific group
```bash
evm load config.json --group dev
```

#### Import backup file
```bash
evm load backup.json --format backup
# Auto-detects backup format and shows timestamp
```

### Backup & Restore

#### Create a backup (with auto timestamp)
```bash
evm backup
```

#### Create a backup to a specific file
```bash
evm backup --file mybackup.json
```

#### Restore from backup (replaces all variables)
```bash
evm restore backup_20240101_120000.json
```

#### Merge backup with existing variables
```bash
evm restore backup.json --merge
```

### Group/Namespace Management

#### List all groups
```bash
evm groups
```

#### Set a variable in a group
```bash
evm setg dev DATABASE_URL "postgresql://localhost/dev"
evm setg prod DATABASE_URL "postgresql://prod-server/app"
```

#### Get a variable from a group
```bash
evm getg dev DATABASE_URL
```

#### List variables in a specific group
```bash
evm listg dev
# Or use the --group option
evm list --group dev
```

#### Display all variables grouped by namespace
```bash
evm list --show-groups
```

#### Delete a variable from a group
```bash
evm deleteg dev DEBUG
```

#### Delete an entire group
```bash
evm delete-group test
```

#### Move a variable to a different group
```bash
evm move-group API_KEY prod
```

### Execute Commands

#### Run a command with environment variables
```bash
evm exec -- python script.py
evm exec -- npm run dev
evm exec -- node app.js
```

### Custom Storage Location

By default, EVM stores environment variables in `~/.evm/env.json`. You can specify a custom location:

```bash
evm --env-file /path/to/custom.json set KEY value
evm --env-file /path/to/custom.json list
```

## Configuration

EVM stores all environment variables in JSON format in `~/.evm/env.json`. The directory structure:

```
~/.evm/
├── env.json          # Main storage file
├── backup_*.json     # Backup files (created with evm backup)
└── ...
```

## Examples

### Development Workflow

```bash
# Set up your development environment
evm set NODE_ENV development
evm set API_URL http://localhost:3000
evm set DEBUG true

# Export to .env for other tools
evm export --format env -o .env

# Run your app with these variables
evm exec -- npm start
```

### Production Workflow

```bash
# Create a backup before making changes
evm backup

# Update production variables
evm set NODE_ENV production
evm set API_URL https://api.example.com
evm set DEBUG false

# Export to shell script for deployment
evm export --format sh -o production.env.sh

# Source the script
source production.env.sh
```

### Team Sharing

```bash
# Export your environment configuration
evm export --output team-env.json

# Share team-env.json with your team
# Team members can import it
evm load team-env.json
```

### Multi-Environment Management

```bash
# Set up different environments using groups
evm setg dev DATABASE_URL "postgresql://localhost/dev"
evm setg dev DEBUG "true"

evm setg test DATABASE_URL "postgresql://test-server/app"
evm setg test DEBUG "true"

evm setg prod DATABASE_URL "postgresql://prod-server/app"
evm setg prod DEBUG "false"

# View all environments at once
evm list --show-groups

# Switch between environments by listing specific group
evm listg dev
evm listg test
evm listg prod

# Export specific environment
evm export --format json -o dev-env.json
# Then edit the file to keep only dev:* variables
```

## Testing

EVM includes a comprehensive test suite and sample configuration files for testing.

### Running Tests

```bash
# Run all tests
make test

# Or directly with pytest
python -m pytest tests/ -v
```

### Test Case Files

The `tests/test_case/` directory contains sample configuration files for testing various features:

- `test_config.json` - Standard JSON configuration (15 variables)
- `test_config.env` - Standard .env configuration (25 variables)
- `test_backup.json` - Backup file format (11 variables)
- `test_export.sh` - Shell script format (12 variables)
- `dev_config.json` - Development environment (8 variables)
- `prod_config.json` - Production environment (10 variables)
- `test_env.json` - Testing environment (8 variables)

### Running Test Cases

```bash
# Use the provided test runner
cd tests
python run_tests.py
```

This will demonstrate:
- JSON import
- .env import
- Backup file import
- Multi-environment management with groups
- And more...

For detailed information about test files, see [tests/test_case/README.md](tests/test_case/README.md).

## Tips

- Use the `list` command with a pattern to quickly find related variables
- Always create a backup before making bulk changes
- Use the `--merge` option when restoring to preserve existing variables
- The `exec` command is useful for running one-off commands with custom environment
- Use `.env` export format for compatibility with dotenv tools

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only Python standard library)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
