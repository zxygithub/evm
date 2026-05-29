# Eval 4: Backup/Diff/Restore Workflow (Without Skill)

## Task
Create a backup before make changes, load a new config file, diff against the backup, and restore if needed. Use JSON output for scripting.

## Commands Executed

### 1. Setup Initial State
```bash
evm --env-file /tmp/eval4_baseline.json --json set DB_HOST localhost
evm --env-file /tmp/eval4_baseline.json --json set DB_PORT 5432
evm --env-file /tmp/eval4_baseline.json --json set APP_NAME myapp
```
**Output:**
```json
{"status": "ok", "data": {"key": "DB_HOST", "value": "localhost", "message": "Set: DB_HOST=localhost"}}
{"status": "ok", "data": {"key": "DB_PORT", "value": "5432", "message": "Set: DB_PORT=5432"}}
{"status": "ok", "data": {"key": "APP_NAME", "value": "myapp", "message": "Set: APP_NAME=myapp"}}
```

### 2. Create Backup
```bash
evm --env-file /tmp/eval4_baseline.json --json backup --file /tmp/eval4_backup_v2.json
```
**Output:**
```json
{"status": "ok", "data": {"message": "Backup created: /tmp/eval4_backup_v2.json"}}
```

### 3. Create New Config and Load (Replace Mode)
Created `/tmp/eval4_new_config.json`:
```json
{
  "DB_HOST": "prod-db.example.com",
  "DB_PORT": "3306",
  "APP_NAME": "myapp-prod",
  "CACHE_ENABLED": "true"
}
```

```bash
evm --env-file /tmp/eval4_baseline.json --json load /tmp/eval4_new_config.json --replace
```
**Output:**
```json
{"status": "ok", "data": {"message": "Replaced environment variables (4 total)", "file": "/tmp/eval4_new_config.json"}}
```

### 4. Diff Against Backup
```bash
evm --env-file /tmp/eval4_baseline.json --json diff /tmp/eval4_backup_v2.json
```
**Output:**
```json
{
  "status": "ok",
  "data": {
    "added": {"CACHE_ENABLED": "true"},
    "removed": {},
    "changed": {
      "DB_HOST": {"current": "prod-db.example.com", "backup": "localhost"},
      "DB_PORT": {"current": "3306", "backup": "5432"},
      "APP_NAME": {"current": "myapp-prod", "backup": "myapp"}
    },
    "backup_timestamp": "2026-05-30T02:47:09.773297"
  }
}
```

### 5. Restore from Backup
```bash
evm --env-file /tmp/eval4_baseline.json --json restore /tmp/eval4_backup_v2.json
```
**Output:**
```json
{"status": "ok", "data": {"message": "Restored 3 variables from backup\nBackup timestamp: 2026-05-30T02:47:09.773297", "file": "/tmp/eval4_backup_v2.json"}}
```

### 6. Verify Restored State
```bash
evm --env-file /tmp/eval4_baseline.json --json list
```
**Output:**
```json
{"status": "ok", "data": {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_NAME": "myapp"}}
```

## Summary
Successfully demonstrated the complete backup → load → diff → restore workflow using `--json` for structured output. The diff command clearly showed added, removed, and changed variables. The restore successfully reverted to the pre-change state. All commands used `--env-file` for isolation.
