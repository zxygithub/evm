# Eval 5: CI/CD Python Workflow — With Skill

## Task
"I'm setting up a CI/CD pipeline and need to manage environment variables programmatically. Show me how to use EVM's Python API to: create a fresh config, import from a JSON file, validate all variables against schemas, and handle errors gracefully with specific exception types."

## Approach
Following the EVM agent skill guidance, I wrote a comprehensive Python script demonstrating the full CI/CD environment management workflow using EVM's Python API.

## Script: `cicd_workflow.py`

The script demonstrates 7 steps:

1. **Initialize EnvironmentManager** with isolated storage (`/tmp/eval5_test.json`)
2. **Import Configuration** from a JSON file (`/tmp/eval5_config.json`) — 7 variables imported
3. **Define Validation Schemas** for 6 variables (DATABASE_URL, API_URL, PORT, APP_NAME, DEBUG, CACHE_TTL)
4. **Validate Configuration** against schemas — all 6 variables passed
5. **Error Handling** with 5 specific exception types:
   - `KeyNotFoundError` — variable not found
   - `KeyAlreadyExistsError` — (demonstrated that `set` allows overwrite)
   - `LockTimeoutError` — simulated concurrent access
   - `SchemaError` — invalid format type caught
   - `EVMError` — generic catch-all
6. **Export Validated Configuration** to JSON file — 8 variables exported
7. **Display Operation History** — last 10 operations

## Key Skill Guidance Applied

| Principle | Applied |
|-----------|---------|
| Use `--env-file` for isolation | ✓ Used `/tmp/eval5_test.json` |
| Proper exception handling | ✓ Used specific exception types from `evm.exceptions` |
| Schema validation | ✓ Defined schemas with format, required, description |
| Python API patterns | ✓ Used `EnvironmentManager`, `set_schema`, `validate_all`, `export` |
| Error handling patterns | ✓ Demonstrated try/except with specific exception types |

## Execution Output (summary)

```
Step 1: ✓ EnvironmentManager initialized successfully
Step 2: ✓ Configuration imported successfully (7 variables)
Step 3: ✓ Schema defined for 6 variables
Step 4: ✓ All 6 variables validated successfully
Step 5: ✓ Error handling demonstrated (5 exception types)
Step 6: ✓ Configuration exported successfully (8 variables)
Step 7: ✓ Last 10 operations displayed

CI/CD pipeline can proceed with validated configuration
```

## Files
- `cicd_workflow.py` — Complete Python script (314 lines)
- `output.txt` — Full execution output
- `result.md` — This summary

## Result
**PASS** — The script successfully demonstrated the complete CI/CD workflow using EVM's Python API with proper exception handling, following the skill's guidance for isolation, schema validation, and error handling patterns.
