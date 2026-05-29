# Eval 3: Exec + Python API (with skill)

## Approach (following SKILL.md)
1. **`--env-file`** isolation → `/tmp/eval3_test.json`
2. **`--json`** for structured output
3. **`exec`** with exit code passthrough
4. **Python API** using `EnvironmentManager` + `execute()`

## Execution

### Step 1: Set up variable
```bash
evm --env-file /tmp/eval3_test.json --json set DATABASE_URL "postgresql://localhost/testdb"
```
Output: `{"status": "ok", "data": {"key": "DATABASE_URL", "value": "postgresql://localhost/testdb", ...}}`

### Step 2: Create test script
```python
# /tmp/test_env_script.py
import os, sys
db_url = os.environ.get('DATABASE_URL', 'NOT SET')
print(f"DATABASE_URL = {db_url}")
sys.exit(0)
```

### Step 3: CLI approach — evm exec
```bash
evm --env-file /tmp/eval3_test.json exec -- python3 /tmp/test_env_script.py
```
Output: `DATABASE_URL = postgresql://localhost/testdb`
Exit code: `0` (passed through from child process)

Verified exit code passthrough with:
```bash
evm --env-file /tmp/eval3_test.json exec -- sh -c 'exit 42'
echo $?  # → 42
```

### Step 4: Python API approach
```python
from evm.manager import EnvironmentManager
from evm.exceptions import KeyNotFoundError

mgr = EnvironmentManager("/tmp/eval3_test.json")

# Read value directly
value = mgr.get("DATABASE_URL")  # "postgresql://localhost/testdb"

# Execute with env vars injected
exit_code = mgr.execute(["python3", "script.py"])
# exit_code = child process return code
```

### Step 5: Cleanup
Deleted temp files.

## Key observations
- Used `--json` for set command, showing structured confirmation
- `exec` correctly passed through exit code 0 from child
- Demonstrated both CLI (`evm exec`) and Python API (`mgr.execute()`) approaches
- Exit code passthrough works (verified with `exit 42`)
- Used `--env-file` for isolation throughout
