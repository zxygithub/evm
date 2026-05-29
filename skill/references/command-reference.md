# EVM Command Reference

Complete command reference for all EVM CLI commands.

## Global Options

| Option | Description |
|--------|-------------|
| `--json` | Structured JSON output (stdout=data, stderr=errors) |
| `--quiet` / `-q` | Suppress all human-readable output |
| `--env-file PATH` | Use custom storage file (default: `~/.evm/env.json`) |
| `--dry-run` | Preview changes without writing |
| `--force` | Skip confirmation for destructive operations |
| `--verbose` / `-v` | Show detailed version information |
| `--version` | Show version and exit |

## Basic CRUD

### `evm set KEY VALUE`
Set an environment variable.
- `--secret` / `-s`: Encrypt the value before storing
- JSON output: `{"key": "...", "value": "...", "message": "..."}`

### `evm get KEY`
Get a variable's value. Exit code 2 if not found.
- `--secret` / `-s`: Decrypt the value before displaying
- JSON output: `{"key": "...", "value": "..."}`

### `evm delete KEY`
Delete a variable. Exit code 2 if not found.
- JSON output: `{"key": "...", "deleted": true, "message": "..."}`

### `evm list [PATTERN]`
List all variables, optionally filtered by pattern.
- `--group` / `-g GROUP`: Filter by group
- `--show-groups`: Group output by namespace
- `--no-prefix`: Remove group prefix from display
- JSON output: `{"KEY1": "val1", "KEY2": "val2", ...}`

### `evm clear`
Clear all variables. Requires `--force` in non-interactive mode.
- JSON output: `{"cleared": N, "message": "..."}`

## Group Management

### `evm setg GROUP KEY VALUE`
Set a variable in a specific group.
- JSON output: `{"group": "...", "key": "...", "value": "...", "message": "..."}`

### `evm getg GROUP KEY`
Get a variable from a specific group.
- JSON output: `{"group": "...", "key": "...", "value": "..."}`

### `evm deleteg GROUP KEY`
Delete a variable from a specific group.

### `evm listg GROUP`
List variables in a group.
- `--no-prefix`: Remove group prefix

### `evm groups`
List all groups with variable counts.
- JSON output: `{"groups": {"dev": 3, "prod": 5}}`

### `evm delete-group GROUP`
Delete an entire group. Requires `--force`. Cannot delete "default".

### `evm move-group KEY GROUP`
Move a variable to a different group.

## Import / Export

### `evm load FILE`
Import variables from a file.
- `--format` / `-f`: Force format (`json`, `env`, `backup`)
- `--replace` / `-r`: Replace existing instead of merging
- `--group` / `-g GROUP`: Add variables to a specific group
- `--nest` / `-n`: Treat first-level JSON keys as group names

### `evm export`
Export variables to a file.
- `--format` / `-f`: Output format (`json`, `env`, `sh`)
- `--output` / `-o PATH`: Output file path
- `--group` / `-g GROUP`: Export only from a specific group

## Backup / Restore

### `evm backup`
Create a timestamped backup.
- `--file` / `-f PATH`: Custom backup path

### `evm restore FILE`
Restore from backup.
- `--merge` / `-m`: Merge with existing instead of replacing

### `evm diff FILE`
Compare current state with a backup file.
- JSON output: `{"added": {}, "removed": {}, "changed": {}, "backup_timestamp": "..."}`

## Search / Rename / Copy

### `evm search PATTERN`
Search variables by key.
- `--value` / `-v`: Also search in values

### `evm rename OLD_KEY NEW_KEY`
Rename a variable.

### `evm copy SRC_KEY DST_KEY`
Copy a variable.

## Execution

### `evm exec -- COMMAND [ARGS...]`
Execute a command with all EVM variables injected into the environment.
- Exit code is passed through from the child process
- Exit code 10 if command not found

### `evm loadmemory`
Load variables into `os.environ` of the current process.
- `--prefix` / `-p PREFIX`: Only load variables with matching key prefix
- `--no-prefix`: Don't add `EVM:` prefix to variable names
- Note: Only affects the current process and its children

## Advanced

### `evm edit KEY`
Open the variable's value in `$EDITOR` (or `$VISUAL`, falls back to `vi`).

### `evm info`
Display tool metadata (version, storage path, variable counts, etc.).
- JSON output: full metadata dictionary

### `evm expand KEY`
Expand `{{OTHER_VAR}}` template references in a variable's value.
- JSON output: `{"key": "...", "expanded": "..."}`

### `evm validate [KEY]`
Validate variables against schema definitions.
- Omit KEY to validate all schema-defined variables
- JSON output: `{"key": "...", "valid": bool, "errors": [...], "warnings": [...]}`

### `evm history`
Show operation audit log.
- `--limit` / `-n N`: Number of entries (default: 20)
- `--clear`: Clear all history

### `evm schema set KEY`
Define a schema for a variable.
- `--format` / `-f`: Built-in format (`url`, `email`, `port`, `integer`, `boolean`, `path`, `ipv4`, `ipv6`)
- `--required` / `-r`: Mark as required
- `--pattern` / `-p REGEX`: Custom regex pattern
- `--description` / `-d TEXT`: Description

### `evm schema get [KEY]`
View schema definition(s).

### `evm schema delete KEY`
Remove a schema definition.

### `evm schema list`
List all schema definitions.

### `evm schema validate [KEY]`
Validate variables against schema (same as `evm validate`).

### `evm completion SHELL`
Generate shell completion script.
- Supports: `bash`, `zsh`, `fish`
- This command ignores `--json` (outputs raw shell script)
