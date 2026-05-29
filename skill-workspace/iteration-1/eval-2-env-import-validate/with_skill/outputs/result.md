# Eval 2: Import .env → Validate → Export (with skill)

## Approach (following SKILL.md)
1. **`--env-file`** isolation → `/tmp/eval2_test.json`
2. **`--json`** on every command for structured output
3. **Schema validation** before export
4. **Export to `.sh`** format

## Execution

### Step 1: Create .env file
```
DATABASE_URL=https://api.example.com/v1
PORT=8080
APP_NAME=MyApp
DEBUG=true
SECRET_KEY=my-secret-key-123
```

### Step 2: Import
```bash
evm --env-file /tmp/eval2_test.json --json load /tmp/app.env
```
Output: `{"status": "ok", "data": {"message": "Loaded 5 environment variables from /tmp/app.env", "file": "/tmp/app.env"}}`

### Step 3: Define schemas
```bash
evm --env-file /tmp/eval2_test.json --json schema set DATABASE_URL --format url
evm --env-file /tmp/eval2_test.json --json schema set PORT --format port
```
Both returned: `{"status": "ok", "data": {"key": "...", "message": "Schema set for '...'"}}`

### Step 4: Validate
```bash
evm --env-file /tmp/eval2_test.json --json validate
```
Output: `{"status": "ok", "data": {"DATABASE_URL": {"valid": true, ...}, "PORT": {"valid": true, ...}}}`

Both DATABASE_URL and PORT passed validation.

### Step 5: Export as shell script
```bash
evm --env-file /tmp/eval2_test.json --json export --format sh --output /tmp/deploy.sh
```
Generated deploy.sh with proper `export` statements and `shlex.quote` escaping.

### Step 6: Cleanup
Deleted temp files.

## Key observations
- Used `--json` on all 5 commands (load, 2× schema set, validate, export)
- Schema validation confirmed both variables match expected formats
- Export used `shlex.quote` for shell-safe values (from skill security guidance)
- All operations used `--env-file` isolation
