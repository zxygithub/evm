# Eval 3: Exec and Python API — Without Skill (Baseline)

## Task
Set up EVM with DATABASE_URL and run a Python script that reads it, demonstrating both CLI (`evm exec`) and Python API approaches.

## Approach 1: CLI with `evm exec`

### Setup
```bash
evm --env-file /tmp/eval3_baseline.json set DATABASE_URL "postgresql://localhost/testdb"
# Output: Set: DATABASE_URL=postgresql://localhost/testdb
```

### Python Script
```python
#!/usr/bin/env python3
import os
db_url = os.environ.get('DATABASE_URL', 'NOT SET')
print(f"DATABASE_URL = {db_url}")
```

### Run
```bash
evm --env-file /tmp/eval3_baseline.json exec -- python3 /tmp/read_db_url.py
# Output: DATABASE_URL = postgresql://localhost/testdb
# Exit Code: 0
```

## Approach 2: Python API

### Script
```python
#!/usr/bin/env python3
import os
from evm.manager import EnvironmentManager

# Load variables into os.environ
mgr = EnvironmentManager("/tmp/eval3_baseline.json")
mgr.load_to_memory(add_evm_prefix=False)

db_url = os.environ.get('DATABASE_URL', 'NOT SET')
print(f"DATABASE_URL = {db_url}")

# Direct read from EVM
print(f"Direct read: {mgr.get('DATABASE_URL')}")
```

### Run
```bash
/opt/homebrew/anaconda3/bin/python /tmp/read_db_url_api.py
# Output:
# DATABASE_URL = postgresql://localhost/testdb
# Direct read: postgresql://localhost/testdb
# Exit Code: 0
```

## Summary
- Both approaches successfully injected DATABASE_URL into the Python script's environment
- `evm exec` is simpler for one-off command execution
- Python API offers more control (direct reads, load_to_memory with prefix options)
- Used `--env-file` for isolation to avoid affecting default EVM storage
- Exit code from exec was passed through correctly (0)
- Did NOT use `--json` flag for structured output
- Did NOT demonstrate exit code passthrough for non-zero exits
- Did NOT mention `mgr.execute()` returning child exit code
- Did NOT show error handling with exception types
