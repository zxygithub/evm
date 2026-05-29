# Eval 1: Multi-Environment Setup (Baseline - No Skill)

## Task
Set up dev/prod environment variables with EVM, including encrypted secret for prod API key.

## Commands Executed

### 1. Set dev environment variables (grouped)
```bash
evm --env-file /tmp/eval1_baseline.json setg dev DATABASE_URL "localhost:5432/mydb"
evm --env-file /tmp/eval1_baseline.json setg dev API_KEY "dev-key-123"
```
Output: Both set successfully.

### 2. Set prod environment variables (grouped)
```bash
evm --env-file /tmp/eval1_baseline.json setg prod DATABASE_URL "prod-db.example.com:5432/mydb"
evm --env-file /tmp/eval1_baseline.json setg prod API_KEY "prod-key-456"
```
Output: Both set successfully.

### 3. Store prod API key as encrypted secret
```bash
evm --env-file /tmp/eval1_baseline.json set --secret prod:API_KEY_SECRET "prod-key-456"
```
Output: `Set secret: prod:API_KEY_SECRET=*** (encrypted)` with machine-binding warning.

### 4. Verify all variables
```bash
evm --env-file /tmp/eval1_baseline.json list
```
Output: 5 variables displayed (dev:API_KEY, dev:DATABASE_URL, prod:API_KEY, prod:API_KEY_SECRET [encrypted], prod:DATABASE_URL).

### 5. Verify secret decryption
```bash
evm --env-file /tmp/eval1_baseline.json get --secret prod:API_KEY_SECRET
```
Output: `prod-key-456` with terminal scrollback warning.

## Observations
- Used `setg` for grouped variables (dev/prod namespaces)
- Used `set --secret` for encrypted storage (separate key name)
- Both plaintext and encrypted versions of prod API_KEY stored
- Did NOT use `--json` flag (not aware of it)
- Did NOT use `--dry-run` for preview
- Did NOT use `--quiet` for silent operation
- Machine-binding warning was unexpected (not pre-warned about it)
- Terminal scrollback warning appeared when decrypting

## Approach
- Chose grouped variables (`setg`) for environment separation
- Used `--env-file` for isolation as instructed
- Stored secret under a separate key name (`prod:API_KEY_SECRET`) since `setg` doesn't support `--secret`
- No JSON output used for scripting
