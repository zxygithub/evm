# EVM - Environment Variable Manager

A powerful cross-platform command-line tool for managing environment variables. Supports macOS, Linux, and Windows.

**Version**: 1.5.0

## Features

- ✅ **Set/Get/Delete**: Manage environment variables
- ✅ **List/Search**: View and find variables easily
- ✅ **Import/Export**: JSON, .env, and shell script formats
- ✅ **Backup/Restore**: Timestamps and merge support
- ✅ **Groups**: Namespace-based organization
- ✅ **Execute**: Run commands with custom environment
- ✅ **Cross-Platform**: Native support for macOS, Linux, Windows

## Project Structure

```
evm/
├── bin/                      # Pre-built binaries
│   ├── evm                   # macOS/Linux executable
│   ├── evm.exe              # Windows executable
│   ├── evm-cli-macos.tar.gz # macOS distribution
│   └── evm-cli-windows.zip  # Windows distribution
├── evm/
│   ├── c/                    # C implementation
│   │   ├── main.c, main_win.c
│   │   ├── core.c, io.c, list.c, group.c
│   │   ├── utils.c, utils_win.c
│   │   ├── evm.h, evm_win.h
│   │   ├── Makefile, Makefile.win
│   │   └── ...
│   └── python/               # Python implementation
│       ├── main.py
│       ├── __init__.py
│       └── __main__.py
├── examples/                 # Example scripts
├── tests/                    # Test suite
├── docs/
│   └── CHANGELOG.md
├── README.md                 # This file
├── LICENSE                   # MIT License
├── Makefile                  # Build automation
├── setup.py                  # Python package setup
└── requirements.txt          # Python dependencies
```

## Quick Start

### Option 1: Pre-built Binaries (Recommended)

**macOS/Linux:**
```bash
cp bin/evm /usr/local/bin/
chmod +x /usr/local/bin/evm
evm --version
```

**Windows:**
```cmd
# Extract bin/evm-cli-windows.zip
copy evm.exe C:\Windows\System32\
evm --version
```

### Option 2: Build from Source

**C Version (All Platforms):**
```bash
# macOS/Linux
cd evm/c
make
sudo make install-local  # Install to /usr/local/bin

# Windows (Cross-compile from macOS/Linux)
cd evm/c
make -f Makefile.win
# Output: evm.exe
```

**Python Version:**
```bash
pip install -e .
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

Environment variables are stored as JSON:

- **macOS/Linux**: `~/.evm/env.json`
- **Windows**: `%USERPROFILE%\.evm\env.json`

Example storage format:
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

## Development

### Building

**C Version:**
```bash
cd evm/c

# Native build (macOS/Linux)
make
make install          # Copy to ../../bin/

# Windows cross-compile
make -f Makefile.win
make -f Makefile.win install

# Create distribution packages
make dist-macos       # macOS tar.gz
make -f Makefile.win dist-windows  # Windows zip
```

**Python Version:**
```bash
# Run as module
python -m evm.python --help

# Install for development
pip install -e .
```

### Testing

```bash
# Python tests
make test
python -m pytest tests/ -v

# C version tests
cd evm/c
make test
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

### Production Deployment

```bash
# Backup before changes
evm backup

# Set production values
evm setg prod NODE_ENV production
evm setg prod API_URL https://api.example.com

# Export deployment script
evm export --format sh -o deploy.sh
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

- **C Version**: C99 compiler (gcc/clang for Unix, MinGW for Windows)
- **Python Version**: Python 3.6+
- **No runtime dependencies**

## Platform Support

| Platform | Binary Size | Format |
|----------|-------------|--------|
| macOS | ~69KB | ELF/Mach-O |
| Linux | ~69KB | ELF |
| Windows | ~298KB | PE32+ |

Windows binary is larger due to static linking of C runtime.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
