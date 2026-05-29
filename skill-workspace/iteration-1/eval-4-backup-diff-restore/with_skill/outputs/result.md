# Eval 4: Backup → Load → Diff → Restore (with_skill)

## Task
Create a backup before making changes, load a new config file, diff against the backup, and restore. Use JSON output for scripting.

## Approach
Followed the skill's core principles:
1. **`--env-file`** for isolation (`/tmp/eval4_test.json`)
2. **`--json`** on every command for structured output
3. Complete workflow: set initial → backup → load new → diff → restore

## Execution

### Step 1: Set initial variables
```bash
evm --env-file /tmp/eval4_test.json --json set DATABASE_URL "postgresql://localhost/mydb"
evm --env-file /tmp/eval4_test.json --json set API_KEY "original-key-123"
evm --env-file /tmp/eval4_test.json --json set APP_NAME "MyApp"
```
All returned `{"status": "ok", ...}` with key/value confirmation.

### Step 2: Create backup
```bash
evm --env-file /tmp/eval4_test.json --json backup --file /tmp/eval4_backup.json
```
Output: `{"status": "ok", "data": {"message": "Backup created: /tmp/eval4_backup.json"}}`

### Step 3: Load new config (replace mode)
Created a new JSON config with changed values and an added variable:
```json
{"DATABASE_URL":"postgresql://prod-server/proddb","API_KEY":"new-key-456","NEW_VAR":"added"}
```
```bash
evm --env-file /tmp/eval4_test.json --json load /tmp/eval4_new_config.json --replace
```
Output: `{"status": "ok", "data": {"message": "Replaced environment variables (3 total)", "file": "/tmp/eval4_new_config.json"}}`

### Step 4: Verify current state
```bash
evm --env-file /tmp/eval4_test.json --json list
```
Output showed 3 variables: DATABASE_URL (changed), API_KEY (changed), NEW_VAR (added). APP_NAME was removed by replace.

### Step 5: Diff against backup
```bash
evm --env-file /tmp/eval4_test.json --json diff /tmp/eval4_backup.json
```
Output:
```json
{
  "status": "ok",
  "data": {
    "added": {"NEW_VAR": "added"},
    "removed": {"APP_NAME": "MyApp"},
    "changed": {
      "DATABASE_URL": {"current": "postgresql://prod-server/proddb", "backup": "postgresql://localhost/mydb"},
      "API_KEY": {"current": "new-key-456", "backup": "original-key-123"}
    },
    "backup_timestamp": "2026-05-30T02:38:43.300475"
  }
}
```

### Step 6: Restore from backup
```bash
evm --env-file /tmp/eval4_test.json --json restore /tmp/eval4_backup.json
```
Output: `{"status": "ok", "data": {"message": "Restored 3 variables from backup\nBackup timestamp: 2026-05-30T02:38:43.300475", "file": "/tmp/eval4_backup.json"}}`

### Step 7: Verify restored state
```bash
evm --env-file /tmp/eval4_test.json --json list
```
Output confirmed original 3 variables restored: DATABASE_URL=localhost, API_KEY=original-key-123, APP_NAME=MyApp.

### Step 8: Cleanup
Deleted all temp files.

## Key Observations
- `--json` output was consistent and parseable at every step
- `diff` command provided structured added/removed/changed breakdown — ideal for scripting
- `--replace` mode in `load` cleanly swapped all variables
- Restore successfully reverted to backup state
- All commands used `--env-file` for isolation — user's personal config was never touched
