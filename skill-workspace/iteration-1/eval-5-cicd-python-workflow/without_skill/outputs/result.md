# Eval 5: CI/CD Python Workflow (baseline - no skill)

## Approach
Used general Python knowledge and basic EVM API usage.

## Python Script
```python
#!/usr/bin/env python3
import json
from evm.manager import EnvironmentManager

env_file = "/tmp/eval5_baseline.json"
mgr = EnvironmentManager(env_file)

# Create config
config = {
    "DATABASE_URL": "postgresql://db.example.com/prod",
    "API_KEY": "ci-key-abc123",
    "PORT": "5432",
    "APP_NAME": "MyService",
}
with open("/tmp/ci_config2.json", "w") as f:
    json.dump(config, f)

# Import
try:
    mgr.load("/tmp/ci_config2.json")
    print("Imported config")
except Exception as e:
    print(f"Import error: {e}")

# Set schemas
mgr.set_schema("DATABASE_URL", format="url")
mgr.set_schema("PORT", format="port")

# Validate
results = mgr.validate_all()
for key, result in results.items():
    print(f"{key}: {'valid' if result['valid'] else 'invalid'}")

# Error handling (generic)
try:
    mgr.get("MISSING")
except Exception as e:
    print(f"Error: {e}")

# Cleanup
import os
os.unlink(env_file, missing_ok=True) if hasattr(os, 'unlink') else None
```

## Output
```
Imported config
DATABASE_URL: valid
PORT: valid
Error: Environment variable 'MISSING' not found
```

## Key observations
- Used bare `except Exception` instead of specific exception types
- Did not import from `evm.exceptions` module
- Missing `ImportFailedError`, `SchemaError`, `KeyNotFoundError` specific handling
- No `required=True` on schemas
- Incomplete cleanup (used `os.unlink` with wrong signature)
- No `CorruptedStorageError` or `StorageError` handling
- Script works but error handling is not graceful — catches everything as generic Exception
- Did not demonstrate the full CI/CD workflow (no summary, no info)
