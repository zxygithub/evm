# Eval 2: Import .env → Validate → Export (baseline - no skill)

## Approach
Used general knowledge of EVM CLI tool.

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
evm --env-file /tmp/eval2_baseline.json load /tmp/app2.env
```
Output: `Loaded 5 environment variables from /tmp/app2.env`

### Step 3: Try to validate
```bash
evm --env-file /tmp/eval2_baseline.json validate DATABASE_URL
```
Got error: `Error: No schema defined for 'DATABASE_URL'`

Had to look up how to define schemas:
```bash
evm --env-file /tmp/eval2_baseline.json schema set DATABASE_URL -f url
evm --env-file /tmp/eval2_baseline.json schema set PORT -f port
evm --env-file /tmp/eval2_baseline.json validate
```
Output showed DATABASE_URL and PORT both valid.

### Step 4: Export
```bash
evm --env-file /tmp/eval2_baseline.json export -f sh -o /tmp/deploy.sh
```
Generated shell script.

### Step 5: Cleanup
Deleted temp files.

## Key observations
- Did NOT use `--json` flag (not aware of it as a best practice)
- Hit the "no schema defined" error before learning to set schemas first
- Used `-f` short flag instead of `--format`
- Successfully completed the workflow but with trial-and-error on validation
- No dry-run preview before making changes
