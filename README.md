# EVM - Environment Variable Manager

A powerful command-line tool for managing environment variables on macOS and Linux systems.

**Version**: 1.5.0

## Features

- ✅ **Set**: Add or update environment variables
- ✅ **Get**: Retrieve environment variable values
- ✅ **Delete**: Remove environment variables
- ✅ **List**: List all or filtered environment variables
- ✅ **Clear**: Clear all environment variables
- ✅ **Export**: Export to JSON, .env, or shell script formats
- ✅ **Import**: Import from JSON, .env, or backup files
- ✅ **Execute**: Run commands with custom environment variables
- ✅ **Rename**: Rename environment variables
- ✅ **Copy**: Copy environment variables
- ✅ **Search**: Search environment variables by key or value
- ✅ **Backup**: Create backups with timestamps
- ✅ **Restore**: Restore from backups (replace or merge)
- ✅ **Groups**: Manage environment variables by namespace/groups

## Project Structure

This project provides two implementations:

```
evm/
├── bin/                      # Compiled binaries
│   ├── evm                   # C implementation (69KB)
│   └── evm-cli-macos.tar.gz  # macOS distribution package
├── evm/
│   ├── c/                    # C implementation source
│   │   ├── main.c
│   │   ├── core.c
│   │   └── ...
│   └── python/               # Python implementation source
│       ├── main.py
│       └── ...
├── examples/                 # Example scripts
├── tests/                    # Test suite
├── README.md                 # This file
├── Makefile                  # Build automation
└── setup.py                  # Python package setup
```

## Quick Start

### Option 1: Use Pre-built Binary (Recommended for macOS)

```bash
# Download from bin/ directory or releases page
cp bin/evm /usr/local/bin/
chmod +x /usr/local/bin/evm

# Verify installation
evm --version
evm --help
```

### Option 2: Build from C Source

```bash
# Clone repository
git clone https://github.com/zxygithub/evm.git
cd evm

# Build C implementation
cd evm/c
make
make install  # Copies to ../../bin/

# Or install system-wide
sudo make install-local  # Installs to /usr/local/bin/
```

### Option 3: Install Python Version

```bash
# Install from source
pip install -e .

# Or for development
pip install -e ".[dev]"
```

## Usage

### Basic Commands

```bash
# Set a variable
evm set API_KEY abc123

# Get a variable
evm get API_KEY

# List all variables
evm list

# Delete a variable
evm delete API_KEY

# Clear all variables
evm clear
```

### Group Management

```bash
# Set variable in a group
evm setg dev DATABASE_URL "localhost:5432"
evm setg prod DATABASE_URL "prod.example.com:5432"

# List variables in a group
evm listg dev

# List all groups
evm groups

# Show all variables grouped by namespace
evm list --show-groups
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
```

### Backup & Restore

```bash
# Create backup (auto-timestamped)
evm backup

# Create backup to specific file
evm backup --file mybackup.json

# Restore from backup
evm restore backup.json
evm restore backup.json --merge   # Merge with existing
```

### Execute Commands

```bash
# Run command with environment variables
evm exec -- python script.py
evm exec -- npm start
```

## Development

### Building C Version

```bash
cd evm/c

# Build
make

# Build and copy to bin/
make install

# Create distribution package
make dist-macos

# Run tests
make test

# Clean build files
make clean
```

### Running Python Version

```bash
# Run as module
python -m evm.python --help

# Or after installation
evm --help
```

### Running Tests

```bash
# Run Python tests
make test
# or
python -m pytest tests/ -v

# Run C version tests
cd evm/c
make test
```

## Configuration

EVM stores environment variables in `~/.evm/env.json`:

```
~/.evm/
├── env.json              # Main storage
└── backup_*.json         # Backup files
```

Use custom storage location:
```bash
evm --env-file /path/to/custom.json set KEY value
```

## Examples

### Development Workflow

```bash
# Setup development environment
evm setg dev NODE_ENV development
evm setg dev API_URL http://localhost:3000
evm setg dev DEBUG true

# Export for sharing
evm export --format env -o .env

# Run app with variables
evm exec -- npm start
```

### Production Deployment

```bash
# Backup before changes
evm backup

# Set production variables
evm setg prod NODE_ENV production
evm setg prod API_URL https://api.example.com

# Export deployment script
evm export --format sh -o deploy.sh
```

## Requirements

- **C Version**: C99 compiler (gcc/clang), macOS or Linux
- **Python Version**: Python 3.6+
- **No external dependencies** for runtime

## Storage Format

Environment variables are stored as JSON:

```json
{
  "API_KEY": "secret123",
  "dev:DATABASE_URL": "localhost:5432",
  "prod:DATABASE_URL": "prod.example.com:5432"
}
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
