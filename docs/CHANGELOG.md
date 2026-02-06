# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
