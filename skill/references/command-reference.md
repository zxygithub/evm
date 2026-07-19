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
- The script also defines an `evm-load` shell function (a shortcut for `eval "$(evm inject)"`)

## Shell Integration

### `evm inject`
Print shell-sourceable `export` statements to stdout. Wrap in `eval "$(evm inject)"` to load variables into the **current** shell — the only mechanism that works, since a child process cannot modify its parent's environment.
- `--shell` / `-s bash|zsh|sh|fish`: Target shell (auto-detected from `$SHELL`; fish uses `set -gx KEY VALUE`)
- `--group` / `-g GROUP`: Inject only this group (strips the `group:` prefix)
- `--include-secrets`: Decrypt and inject secret variables (skipped by default to avoid leaking ciphertext)
- `--prefix PREFIX`: Namespace all exported keys (e.g. `EVM_`) to avoid collisions
- Plain (non-grouped) variables are exported by default; grouped vars are skipped unless `--group` is given
- Values are escaped with `shlex.quote` (spaces, quotes, `$` all handled)
- JSON output: `{"shell": "...", "count": N, "variables": [...], "skipped": [...], "output": "..."}`
- `--dry-run`: Preview what would be injected (human-readable, not eval-able)

```bash
eval "$(evm inject)"                  # load all plain vars
eval "$(evm inject --group prod)"     # load only the prod group
eval "$(evm inject --include-secrets)" # also decrypt and inject secrets
```

### `evm init [SHELL]`
Output the shell-integration script (for `eval "$(evm init zsh)"` in your rc), or manage rc-file installation. The integration block re-evaluates `evm init` on every shell start, so `evm-load` and tab completion stay in sync with the installed evm version automatically.
- `SHELL`: `bash` / `zsh` / `fish` (default: detect from `$SHELL`)
- `--install`: Append the integration block to the shell rc file (`~/.zshrc` / `~/.bashrc` / `~/.config/fish/config.fish`)
- `--uninstall`: Remove the integration block (line-level deletion, preserves surrounding content)
- `--reinstall`: Remove then re-add (useful if rc got out of sync)
- `--check`: Report whether installed (exit 0 = installed, 1 = not installed)
- JSON output: `{"shell": "...", "installed": bool}` (for `--check`); `{"shell": "...", "message": "...", "ok": bool}` (for install/uninstall/reinstall)

**Auto-install on first use**: the first time you run any `evm` command (except `init`/`completion`/`upgrade` themselves), EVM appends the integration block to your rc and prints a notice to stderr. Set `EVM_NO_AUTO_INSTALL=1` to skip.

## Self-Upgrade

### `evm upgrade`
Check PyPI for a newer `evm` release and pip-install it. Pure standard-library implementation (urllib + subprocess), no new dependencies.
- `--check`: Only check, don't install. Exit 0 = up to date, 1 = update available (or network error)
- `--dry-run`: Print the pip command that would run, without executing it
- `--force`: Skip the pre-check and run pip directly
- Runs `pip install --upgrade evm-cli` with the **same Python interpreter** that runs `evm` (so the correct installation is upgraded)
- JSON output (`--check`): `{"current": "...", "latest": "...", "update_available": bool}`
- JSON output (upgrade): `{"current": "...", "new_version": "...", "action": "upgraded|already_latest|dry_run|failed|network_error", "upgraded": bool, "message": "..."}`
- Network-unreachable is handled gracefully: `--check` reports `latest: unknown` and exits 1; a plain `evm upgrade` aborts before touching pip
