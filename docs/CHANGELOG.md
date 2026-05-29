# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.0] - 2026-05-30

### Security (P0)
- **Shell export escaping**: `export` to `.sh` format now uses `shlex.quote()` to prevent command injection via `$(...)`, backticks, etc.
- **File permissions**: Storage file (`env.json`) and backups now set to `chmod 600` (owner read/write only)
- **No more silent error swallowing**: Corrupted JSON files raise `CorruptedStorageError`, permission errors raise `StorageError`

### Architecture (P1)
- **Module split**: Replaced single `main.py` (832 lines) with modular structure:
  - `cli.py` — argparse parsing + command dispatch
  - `manager.py` — pure business logic (no print/sys.exit)
  - `formatters.py` — terminal output formatting
  - `exceptions.py` — custom exception hierarchy (`EVMError` base class)
- **Exception-based error handling**: Business methods raise typed exceptions instead of `sys.exit(1)`, making the library safe for programmatic use
- **Atomic writes**: Storage uses temp file + rename to prevent data corruption
- **File locking**: Uses `fcntl.flock` for exclusive write access

### Features (P2)
- **`evm edit KEY`**: Edit variable value in `$EDITOR` (or `$VISUAL`, falls back to `vi`)
- **`evm info`**: Display tool metadata (version, storage path, variable/group counts, secrets count)
- **`evm expand KEY`**: Expand `{{OTHER_VAR}}` template references in variable values
- **`evm set --secret KEY VALUE` / `evm get --secret KEY`**: Encrypt/decrypt sensitive variables using machine-key XOR encryption
- **`evm diff FILE`**: Compare current state with a backup file (shows added/removed/changed)
- **`--dry-run`**: Global flag to preview changes without writing (supported by set, delete, clear, rename, copy, export, load, setg, deleteg, delete-group, move-group, set --secret)

### Changed
- Entry point updated to `evm.cli:main`
- `main.py` removed; all code now in `cli.py`, `manager.py`, `formatters.py`, `exceptions.py`
- Test suite expanded from 39 to 101 tests covering all new features
- Version bumped to 1.7.0

## [1.6.0] - 2026-05-30

### Removed
- **Removed C implementation**: Deleted the entire C codebase (`evm/c/` directory)
- **Removed pre-built binaries**: Deleted `bin/` directory (macOS pkg, tar.gz, executable)
- Dropped dual-language maintenance to focus on a single Python implementation

### Changed
- **Project structure flattened**: Moved `evm/python/main.py` → `evm/main.py`, removed `evm/python/` subdirectory
- Updated entry point from `evm.python.main:main` to `evm.main:main`
- Updated all import paths (`from evm.main import ...`)
- Updated Makefile: removed C build targets (`build-macos`, `install-macos`)
- Updated README: removed all C version references and binary installation instructions
- Updated examples to use new import paths

## [1.5.0] - 2025-02-07

### Changed
- **Project Structure Reorganization**: Restructured codebase for multi-language support
  - Moved Python source code to `evm/python/` directory
  - Created `evm/c/` directory for future C implementation
  - Updated all import paths to reflect new structure
  - Added `evm/__init__.py` for proper package exports
  - Added `evm/python/__main__.py` for module execution support

### Fixed
- Fixed search functionality to handle non-string values correctly
- Updated all version references from 1.4.0 to 1.5.0

## [1.6.0] - 2024-01-06

### Added
- **Nested JSON Import Support**: Implemented `--nest` / `-n` parameter for load command
  - Automatically treat first-level keys as group names
  - Support importing multi-environment configurations in one file
  - Handle nested JSON structures with two levels
  - Detect and report number of imported groups
  - Added NEST_IMPORT.md comprehensive documentation
- **Verbose Version Command**: Added `-v` / `--verbose` option for detailed version information
  - Displays version, author, license, Python version, storage location
  - Shows repository and documentation links

### Changed
- load command accepts nest parameter for nested JSON support
- Enhanced JSON loading logic to handle nested structures
- Improved group prefix handling with nest parameter support
- Main function handles verbose flag before command processing

### Documentation
- Added NEST_IMPORT.md with comprehensive guide for nested imports
- Updated test_case README.md with format problem explanation
- Created test_group_config_correct.json as proper nested format example
- Created FORMAT_ISSUE.md explaining EVM format requirements

## [1.5.0] - 2024-01-06

### Added
- **Test Case Directory**: Added `tests/test_case/` directory for storing test configuration files
  - Sample JSON configurations for various scenarios
  - Sample .env files for environment variable imports
  - Backup file examples for testing restore functionality
  - Shell script examples for export/import testing
  - Multi-environment configuration files (dev, prod, test)
  - Comprehensive documentation for each test file
  - Test runner script (`tests/run_tests.py`) for automated testing
  - 9 test configuration files covering all major features

### Added
- **Enhanced JSON Import**: Advanced import functionality with multiple options
  - `--format` option: Force file format (json, env, backup)
  - `--replace` option: Replace mode instead of merge mode
  - `--group` option: Import variables into a specific group
  - Auto-detection: Automatically detect file format from content
  - Backup file support: Import EVM backup files with timestamp display
  - 8 new test cases for enhanced import functionality
  - New documentation: JSON_IMPORT.md with comprehensive guide
  - New documentation: JSON_IMPORT_UPDATE.md with feature update summary

### Changed
- Import command now accepts optional format, replace, and group parameters
- Better error messages for import operations
- Improved file format detection logic

## [1.4.0] - 2024-01-06

### Added
- **Group/Namespace Management**: Support for organizing environment variables by namespace/groups
  - New commands: groups, setg, getg, deleteg, listg, delete-group, move-group
  - Enhanced list command: --group and --show-groups options
  - Support for managing variables in specific groups
  - Group-based variable organization and filtering
  - 10 new test cases for group functionality
  - New documentation: GROUPS.md with detailed guide

### Added
- **Enhanced JSON Import**: Advanced import functionality with multiple options
  - `--format` option: Force file format (json, env, backup)
  - `--replace` option: Replace mode instead of merge mode
  - `--group` option: Import variables into a specific group
  - Auto-detection: Automatically detect file format from content
  - Backup file support: Import EVM backup files with timestamp display
  - 8 new test cases for enhanced import functionality
  - New documentation: JSON_IMPORT.md with comprehensive guide
  - New documentation: JSON_IMPORT_UPDATE.md with feature update summary

### Changed
- load command now accepts optional format, replace, and group parameters
- Better error messages for import operations
- Improved file format detection logic

## [1.3.0] - 2024-01-06

### Added
- **Command Line Behavior**: Improved `evm` command to show help instead of error
  - When no subcommand is provided, displays full help information
  - Exits with code 0 (success) instead of 1 (failure)
  - Better user experience for new users

## [1.2.0] - 2024-01-06

### Added
- **Test Case Directory**: Added `tests/test_case/` directory for storing test configuration files
  - Sample JSON configurations for various scenarios
  - Sample .env files for environment variable imports
  - Backup file examples for testing restore functionality
  - Shell script examples for export/import testing
  - Multi-environment configuration files (dev, prod, test)
  - Comprehensive documentation for each test file
  - Test runner script (`tests/run_tests.py`) for automated testing
  - 9 test configuration files covering all major features
  - Total 89 test variables across all files

### Added
- **Enhanced JSON Import**: Advanced import functionality with multiple options
  - `--format` option: Force file format (json, env, backup)
  - `--replace` option: Replace mode instead of merge mode
  - `--group` option: Import variables into a specific group
  - Auto-detection: Automatically detect file format from content
  - Backup file support: Import EVM backup files with timestamp display
  - 8 new test cases for enhanced import functionality
  - New documentation: JSON_IMPORT.md with comprehensive guide
  - New documentation: JSON_IMPORT_UPDATE.md with feature update summary

### Changed
- Import command now accepts optional format, replace, and group parameters
- Better error messages for import operations
- Improved file format detection logic

## [1.1.0] - 2024-01-06

### Added
- **Initial Release of EVM (Environment Variable Manager)**
  - Core functionality for managing environment variables on macOS and Linux
  - `set` - Set environment variables
  - `get` - Get environment variable values
  - `delete` - Remove environment variables
  - `list` - List all or filtered environment variables
  - `clear` - Clear all environment variables
  - `export` - Export to JSON, .env, or shell script formats
  - `load` - Import from JSON or .env files
  - `exec` - Execute commands with custom environment variables
  - `rename` - Rename environment variables
  - `copy` - Copy environment variables
  - `search` - Search environment variables by key or value
  - `backup` - Create backups with timestamps
  - `restore` - Restore from backups (replace or merge)
  - Pattern filtering for list command
  - Custom storage location support via `--env-file` flag
  - Comprehensive test suite with 21 test cases
  - Command-line interface with help and examples
  - Python API for programmatic usage
  - Documentation including README and examples
  - Makefile for common development tasks

### Changed
- Initial implementation with all core features
- Complete test coverage
- Full documentation set
