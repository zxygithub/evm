# Eval 1: Multi-Environment Setup (with skill)

## Task
Set up dev/prod environment variables using EVM with grouped configs and encrypted secret for prod API key.

## Approach (following SKILL.md guidance)

### Skill principles applied:
1. **`--env-file` isolation** → `/tmp/eval1_test.json` (no user config affected)
2. **Groups** → `setg dev`/`setg prod` for multi-environment in single file
3. **`--secret`** → Encrypted storage for prod API key
4. **`--dry-run`** → Previewed before executing

### Commands executed:

**Step 1: Preview (dry-run)**
```bash
evm --env-file /tmp/eval1_test.json --dry-run setg dev DATABASE_URL "localhost:5432/mydb"
# Output: [DRY-RUN] Would set: [dev]DATABASE_URL = localhost:5432/mydb
```

**Step 2: Set dev variables**
```bash
evm --env-file /tmp/eval1_test.json setg dev DATABASE_URL "localhost:5432/mydb"
# Output: Set: [dev]DATABASE_URL = localhost:5432/mydb

evm --env-file /tmp/eval1_test.json setg dev API_KEY "dev-key-123"
# Output: Set: [dev]API_KEY = dev-key-123
```

**Step 3: Set prod DB URL (non-secret)**
```bash
evm --env-file /tmp/eval1_test.json setg prod DATABASE_URL "prod-db.example.com:5432/mydb"
# Output: Set: [prod]DATABASE_URL = prod-db.example.com:5432/mydb
```

**Step 4: Store prod API key as encrypted secret**
```bash
evm --env-file /tmp/eval1_test.json set --secret prod:API_KEY "prod-key-456"
# Output: Set secret: prod:API_KEY=*** (encrypted)
#         [WARNING: Encryption key is derived from machine identity...]
```

**Verification:**
```bash
evm --env-file /tmp/eval1_test.json list           # 4 variables in 2 groups
evm --env-file /tmp/eval1_test.json listg dev       # dev:API_KEY, dev:DATABASE_URL
evm --env-file /tmp/eval1_test.json listg prod      # prod:API_KEY (encrypted), prod:DATABASE_URL
evm --env-file /tmp/eval1_test.json getg dev DATABASE_URL   # localhost:5432/mydb
evm --env-file /tmp/eval1_test.json getg prod DATABASE_URL  # prod-db.example.com:5432/mydb
evm --env-file /tmp/eval1_test.json get --secret prod:API_KEY 2>/dev/null  # prod-key-456
evm --env-file /tmp/eval1_test.json groups          # dev (2), prod (2)
```

## Results

| Variable | Group | Value | Encrypted |
|----------|-------|-------|-----------|
| dev:DATABASE_URL | dev | localhost:5432/mydb | No |
| dev:API_KEY | dev | dev-key-123 | No |
| prod:DATABASE_URL | prod | prod-db.example.com:5432/mydb | No |
| prod:API_KEY | prod | prod-key-456 | Yes (ENCv3) |

## Key observations
- Machine-binding warning appeared on first `--secret` use (as documented in skill)
- All variables correctly grouped under `dev:` and `prod:` prefixes
- Encrypted secret decrypts correctly back to original value
- History log shows `set_secret` operation (without logging the value)
