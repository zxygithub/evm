# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2026-05-30

### Test Coverage Deep Dive & Code Review Remediation

This release pushes test coverage from 94% to **98%** and adds a comprehensive development review.

#### Code Review Fixes (M2/L1-L4)
- **M2: Schema I/O** — `_load_schema()` replaced `print(stderr)` with `warnings.warn(RuntimeWarning)`, maintaining the "mixin does no I/O" principle.
- **L1: `_completion.py` dynamic key errors** — Silenced `OSError`/`json.JSONDecodeError` in completion key lookup so shell completion degrades gracefully.
- **L2: `_history.py` JSON decode** — `json.JSONDecodeError` caught alongside `ValueError` for robustness.
- **L3: `formatters.py` terminal width** — `shutil.get_terminal_size()` fallback for non-TTY environments.
- **L4: `_crypto.py` HKDF length guard** — Explicit `ValueError` on zero-length HKDF output request.

#### Test Improvements (521 → 575, +54 tests)
- **`test_coverage_gap.py`** — 54 new tests targeting hard-to-reach error paths across all modules (encryption edge cases, I/O boundary conditions, CLI error handling, schema validation corners).
- **`test_cli_boundary.py`** — Boundary tests for `cli.py` error branches.
- **`test_io_boundary.py`** — Boundary tests for `_io.py` import/export edge cases.
- **`test_v230_fixes.py`** — Additional v1/v2 encryption migration path tests.

#### Coverage Results
- **Total coverage: 94% → 98%**
- **`_crypto.py`: 100%** (v1/v2 auto-migration paths fully covered)
- **`_schema.py`: 99%**
- **`cli.py`: 98%**
- **`manager.py`: 97%**
- **`_completion.py`, `_json.py`, `_groups.py`, `_typing.py`, `formatters.py`, `exceptions.py`, `__init__.py`: 100%**

#### Documentation
- **Development Review** (`docs/DEVELOPMENT_REVIEW.md`) — Comprehensive project assessment covering engineering quality, feature completeness, gap analysis, and phased roadmap recommendations.
- **Code Review v2.0.0 Final** (`docs/CODE_REVIEW_v2.0.0_FINAL.md`) — Post-remediation verification report.

#### Other
- **`.gitignore` optimization** — Consolidated rules, removed test artifacts.

### Verification
```bash
$ mypy evm/
Success: no issues found in 14 source files

$ ruff check .
All checks passed!

$ pytest tests/ -v
============================= 575 passed in 4.58s ==============================

$ pytest --cov=evm --cov-report=term-missing tests/
TOTAL                 1664     41    98%
```

## [2.3.0] - 2026-05-30

### Code Review Remediation (CODE_REVIEW_v2.2.0.md)

Based on the v2.2.0 code review, this release addresses all High and Medium priority issues.

#### High Priority Fixes
- **H1: StorageProtocol applied to all mixins** — All 4 mixin classes (`IOMixin`, `GroupMixin`, `HistoryMixin`, `SchemaMixin`) now inherit `EnvironmentManagerProtocol`, eliminating all `# type: ignore[attr-defined]` comments. `_typing.py` coverage: 0% → 100%.
- **H2: History trim lazy + atomic** — `_trim_history()` replaced with `_trim_history_if_needed()` that only fires when entries exceed 1.5× MAX_HISTORY_ENTRIES (was: every call, O(N) scan). Trim operation now uses atomic write (temp file + `os.replace`) to prevent data loss on crash.
- **H3: Non-interactive confirmation** — `clear` and `delete-group` in non-TTY mode now raise a clear `EVMError` with "Use --force to skip confirmation" message, instead of silently cancelling with a misleading "user cancelled" error.

#### Medium Priority Fixes
- **M1: Encryption machine-binding docs** — README now prominently documents the machine-binding limitation of encryption keys.
- **M2: Schema I/O cleanup** — `_load_schema()` replaced `print(stderr)` with `warnings.warn(RuntimeWarning)`, maintaining the "mixin does no I/O" design principle.
- **M3: Shell completion dynamic keys** — bash/zsh/fish completion scripts now include dynamic variable name completion for `get`, `delete`, `edit`, `expand`, `validate`, `rename`, `copy` commands (calls `evm list --json --quiet`).

#### Additional Fixes
- **`backup()` uses `self.env_file.parent`** — Default backup path is now relative to the storage file location, not hardcoded `~/.evm/`. Fixes isolation semantics when using `--env-file`.
- **`move_to_group` conflict detection** — Now raises `KeyAlreadyExistsError` when the target group already has a key with the same name.
- **`_load_env_file` reports skipped keys** — Load message now includes "Skipped N invalid key(s): ..." when .env import skips invalid key names.
- **`__init__.py` exports core API** — `EnvironmentManager` and all 17 exceptions now importable from `evm` directly (`from evm import EnvironmentManager, KeyNotFoundError`).
- **`_secret_warning_shown` instance-level** — Moved from class variable to instance variable, preventing shared state across multiple `EnvironmentManager` instances.
- **`history.jsonl` file locking** — Write operations now use `fcntl.flock(LOCK_EX)` to prevent line interleaving in concurrent scenarios.
- **Makefile `format` target** — Updated from `black` to `ruff format`.

#### Documentation
- **Python API Reference** (`docs/API_REFERENCE.md`) — Comprehensive API documentation covering all 36 public methods of `EnvironmentManager`, the full exception hierarchy (17 classes), formatters module, crypto module, CLI exit codes, and quick-start recipes.
- **README Python API section** — Updated import paths to use `from evm import ...` (package root), added link to full API reference, added import/export/backup examples.
- **Project structure** — Updated test count (521) and docs listing in README.

#### Test Improvements
- **Total tests: 360 → 521** (+161 tests across 3 rounds of additions)
- **Total coverage: 89% → 94%**
- **`_completion.py`: 100%**
- **`_typing.py`: 0% → 100%** (protocol now used by all mixins)
- **`formatters.py`: 100%** (dynamic terminal width via `shutil.get_terminal_size()`)
- New test files:
  - `tests/test_v230_fixes.py` — 45 tests covering review fixes + encryption error paths
  - `tests/test_io_boundary.py` — 55 boundary tests for `_io.py`
  - `tests/test_cli_boundary.py` — 61 boundary tests for `cli.py`

### Verification
```bash
$ mypy evm/
Success: no issues found in 14 source files

$ ruff check .
All checks passed!

$ pytest tests/ -v
============================= 521 passed in 4.06s ==============================

$ pytest --cov=evm --cov-report=term-missing tests/
TOTAL                 1664    102    94%
```

## [2.2.0] - 2026-05-30

### Code Quality and Test Coverage Improvements

Based on comprehensive code review (CODE_REVIEW.md), this release addresses all critical issues and significantly improves test coverage.

#### Type System Improvements (mypy)
- **Fixed 36 mypy errors** → 0 errors
- Added `# type: ignore[attr-defined]` comments to Mixin classes (standard practice for Mixin pattern)
- Added `# type: ignore[no-any-return]` for `Dict.get()` and `json.loads()` returns
- Created `_typing.py` with `EnvironmentManagerProtocol` for Mixin type hints
- Unified Python version to 3.9+ across all tools (pyproject.toml, ruff, mypy)

#### Code Quality Improvements (ruff)
- **Fixed 43 ruff errors** → 0 errors
- Auto-fixed import sorting issues
- Replaced deprecated `typing.Dict`, `typing.List`, `typing.Tuple` with built-in `dict`, `list`, `tuple` (Python 3.9+)
- Updated Makefile `lint` target to use `ruff check` instead of `flake8`

#### Test Coverage Improvements
- **Total coverage: 78% → 89%**
- **formatters.py: 47% → 100%** (added 39 comprehensive tests in `test_formatters.py`)
- **cli.py: 74% → 87%** (added 63 new tests across multiple test files)
- **__main__.py: 0% → 67%** (added 13 tests in `test_main_module.py`)
- **Total tests: 237 → 360** (+123 tests)

#### New Test Files
- `tests/test_formatters.py`: Comprehensive tests for all formatter functions
- `tests/test_main_module.py`: Tests for `__main__.py` entry point
- `tests/test_cli_additional.py`: Additional CLI command tests
- `tests/test_cli_coverage.py`: Extended CLI coverage tests

#### Documentation Updates
- Added Platform Support section to README (explicitly stating POSIX-only, no Windows)
- Updated Python requirement from 3.6+ to 3.9+
- Updated test count from 225 to 360
- Created comprehensive Chinese system functional specification (`docs/USER_GUIDE_CN.md`)

#### Configuration Updates
- Unified Python version requirement to 3.9+ in:
  - `pyproject.toml` (`requires-python`)
  - `pyproject.toml` (`[tool.ruff]` target-version)
  - `pyproject.toml` (`[tool.mypy]` python_version)
  - `README.md` (requirements section)
- Updated `Makefile` lint target to use `ruff check` instead of `flake8`

### Technical Details

#### Mixin Type Annotations
The project uses Mixin pattern for code organization. Mixin classes access attributes (`self.env_file`, `self._env_vars`, `self._save_env_vars()`) from the main `EnvironmentManager` class. Standard practice is to use `# type: ignore[attr-defined]` comments since these attributes are provided by the main class at runtime.

#### Python 3.9+ Requirement
Updated to Python 3.9+ to:
- Use built-in generic types (`dict`, `list`, `tuple`) instead of `typing.Dict`, `typing.List`, `typing.Tuple`
- Align with mypy's minimum supported version
- Take advantage of modern Python features

#### Test Coverage Strategy
- **formatters.py**: Tested all 11 public functions with various input combinations
- **cli.py**: Tested command registry pattern, error handling, and edge cases
- **__main__.py**: Tested module entry point with `python -m evm` invocation

### Verification

All checks pass:
```bash
$ mypy evm/
Success: no issues found in 14 source files

$ ruff check .
All checks passed!

$ pytest tests/ -v
============================= 360 passed in 2.16s ==============================

$ pytest --cov=evm --cov-report=term-missing tests/
TOTAL                 1590    181    89%
```

## [2.1.0] - 2026-05-30

### 工程化：迁移到 pyproject.toml

#### 构建系统现代化
- **新增 `pyproject.toml`**：采用 PEP 621 标准，使用 `setuptools` 构建后端
- **`setup.py` 精简为兼容性 shim**：仅保留 `setup()` 调用，所有元数据迁移到 `pyproject.toml`
- **`requirements.txt` 重构**：指向 `pyproject.toml`，保留向后兼容

#### 可选依赖组
- `[dev]`：完整开发环境（pytest, pytest-cov, ruff, mypy）
- `[test]`：仅测试工具（pytest, pytest-cov）
- `[lint]`：仅代码检查工具（ruff, mypy）

#### 工具链配置
- **ruff**：替代 black + flake8，统一 linter + formatter（配置在 `[tool.ruff]`）
- **mypy**：类型检查配置（`[tool.mypy]`）
- **pytest**：测试配置（`[tool.pytest.ini_options]`）
- **coverage**：覆盖率配置（`[tool.coverage]`）

#### 代码质量改进
- ruff 自动修复 import 排序（33 处）
- 清理 3 处未使用变量（`_completion.py`、`cli.py`、`test_main.py`）
- ruff check 全部通过，237 个测试全部通过

### 安装方式变更
```bash
# 核心安装（无第三方依赖）
pip install .

# 开发安装（含 pytest, ruff, mypy）
pip install ".[dev]"

# 仅测试工具
pip install ".[test]"

# 仅 lint 工具
pip install ".[lint]"
```

## [2.0.0] - 2026-05-30

### Code Review 全部修复（18 项安全/质量改进）

#### CRITICAL 修复
- **#1 文件锁竞态条件**：改用独立 `.lock` 文件加锁，替代锁临时文件的竞态窗口
- **#3 裸 except Exception: pass**：`_history.py` 改为 `except OSError`，不再吞没编程错误

#### HIGH 修复
- **#4 重复密钥 XOR → HMAC-CTR**：消除 32 字节密钥循环复用弱点
- **#5 机器密钥低熵**：通过 HKDF-Expand 从 PBKDF2 主密钥派生高熵子密钥
- **#6 历史日志泄露 value**：`set` 操作不再记录明文 value；history.jsonl 设置 chmod 600
- **#7 IPv6 正则过宽**：改用 `ipaddress.IPv6Address()` 标准库校验
- **#8 .env 引号解析**：支持平衡双引号/单引号，不平衡引号按字面量处理
- **#9 Shell 导出 key 未转义**：key 名也用 `shlex.quote()` 转义；导入时校验 key 名格式
- **#10 Schema 损坏静默丢弃**：损坏时打印 warning 到 stderr

#### MEDIUM 修复
- **#12 异常链丢失**：全部 `raise ... from e` 保留原始 traceback
- **#13 .env 导出换行**：值含换行时用双引号包裹并转义 `\n`
- **#14 异常命名规范化**：`PermissionError_` → `StoragePermissionError`，`ImportError_` → `ImportFailedError`（保留向后兼容别名）
- **#15 加密/MAC 同钥**：HKDF-Expand 派生独立 enc_key 和 mac_key
- **#16 v1 加密自动迁移**：读取 v1/v2 密文时自动升级到 v3 格式
- **#17 历史文件非原子写入**：`_history.py` 仅捕获 OSError
- **#18 解密值终端暴露**：`get --secret` 输出到终端时显示 scrollback 警告

#### 加密模块重构
- 新增 `_crypto.py` 独立加密模块
- HKDF-Expand (RFC 5869) 密钥分离
- HMAC-CTR 模式流密码（替代重复密钥 XOR）
- Encrypt-then-MAC（HMAC-SHA256 认证）
- v3 格式：`ENCv3:<salt>:<iv>:<mac>:<ciphertext>`

#### 异常体系更新
- `PermissionError_` → `StoragePermissionError`
- `ImportError_` → `ImportFailedError`
- 保留向后兼容别名

#### 其他
- 首次使用 `--secret` 时打印机器绑定警告
- `set` 操作不再记录 value 到历史日志
- 测试从 201 增加到 225 个

### Changed
- 版本号升级到 2.0.0（major bump：加密格式不兼容变更 + 异常重命名）

## [1.9.0] - 2026-05-30

### Agent-Friendly CLI (from AGENT_CLI_EVALUATION.md)

#### JSON Output (`--json`) — P0
- All 29 commands support `--json` flag for structured output
- JSON envelope format: `{"status": "ok", "data": {...}}` for success, `{"status": "error", "error": "...", "error_code": N}` for errors
- stdout = data (JSON), stderr = errors (JSON) — clean separation for agent parsing
- New module `_json.py` with `json_output()` and `json_error()` helpers

#### Granular Exit Codes — P0
- 11 distinct exit codes mapped from exception types:
  - 0=success, 1=general, 2=key not found, 3=storage error, 4=import/export error
  - 5=decryption error, 6=validation/schema error, 7=group error, 8=backup error
  - 9=editor error, 10=command not found
- Agents can programmatically distinguish error types without parsing messages

#### `exec` Uses `subprocess.run` — P1
- Replaced `os.execvpe()` with `subprocess.run()` for better agent control
- `exec` now returns the child process exit code (transparent passthrough)
- Agent can capture exit codes and handle failures programmatically
- `KeyboardInterrupt` handled gracefully (returns 130)

#### Quiet Mode (`--quiet`) — P2
- `--quiet` / `-q` flag suppresses all human-readable output
- Combined with `--json`: only structured data on stdout, no decoration
- Exit codes still reflect operation result even in quiet mode

### Changed
- `manager.py` `execute()` now returns `int` (subprocess exit code) instead of `None`
- New module `_json.py` for JSON output helpers
- Test suite expanded from 150 to 201 tests (51 new tests for JSON/exit codes/exec/quiet)
- Version bumped to 1.9.0

## [1.8.0] - 2026-05-30

### Architecture (P1)
- **Module decomposition**: Split `manager.py` into mixin-based modules:
  - `_io.py` — IOMixin (import/export/backup/restore/diff)
  - `_groups.py` — GroupMixin (namespace management)
  - `_history.py` — HistoryMixin (operation logging)
  - `_schema.py` — SchemaMixin (format validation)
- **`load()` refactored**: Split into `_detect_format()`, `_load_json_file()`, `_load_env_file()`, `_load_nested()`, `_apply_group_prefix()` — each independently testable
- **File lock timeout**: `fcntl.flock` now uses `LOCK_NB` with configurable timeout (default 5s), raises `LockTimeoutError` instead of blocking indefinitely
- **Encryption enhanced**: PBKDF2-HMAC-SHA256 key derivation (100k iterations) + HMAC integrity verification. Format: `ENCv2:<salt>:<hmac>:<ciphertext>`. Backward compatible with v1 (`ENC:`) secrets

### Features (P2)
- **`evm validate [KEY]`**: Validate variables against schema definitions. Supports formats: url, email, port, integer, boolean, path, ipv4, ipv6, plus custom regex patterns
- **`evm schema set|get|delete|list|validate`**: Full schema management — define formats, required flags, custom patterns, and descriptions for variables
- **`evm history [--limit N] [--clear]`**: Operation audit log stored as JSONL. Tracks set/delete/rename/copy/clear/edit/set_secret with timestamps
- **`evm completion bash|zsh|fish`**: Generate shell completion scripts for all three major shells
- **Interactive confirmation**: `clear` and `delete-group` now prompt for confirmation before executing. Use `--force` to skip
- **`--force` global flag**: Skip confirmation for destructive operations

### New Exceptions
- `LockTimeoutError` — file lock acquisition timeout
- `ValidationError` — variable value format mismatch
- `SchemaError` — schema definition errors
- `OperationCancelledError` — user cancelled destructive operation

### Changed
- Entry point remains `evm.cli:main`
- `EnvironmentManager` now inherits from `IOMixin`, `GroupMixin`, `HistoryMixin`, `SchemaMixin`
- Test suite expanded from 101 to 150 tests
- Version bumped to 1.8.0

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
