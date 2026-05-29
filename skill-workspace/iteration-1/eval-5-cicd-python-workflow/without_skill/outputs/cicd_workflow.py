#!/usr/bin/env python3
"""CI/CD pipeline environment variable management using EVM Python API."""

import json
import os
import sys

ENV_FILE = "/tmp/eval5_baseline.json"

try:
    from evm.manager import EnvironmentManager
    from evm.exceptions import (
        EVMError,
        KeyNotFoundError,
        SchemaError,
        ImportFailedError,
        ExportError,
    )
except ImportError as e:
    print(f"EVM not installed: {e}")
    sys.exit(1)


def main():
    print("=" * 60)
    print("EVM Python API - CI/CD Workflow Demo (Baseline)")
    print("=" * 60)

    # 1. Create fresh config
    print("\n1. Creating fresh EVM config...")
    try:
        mgr = EnvironmentManager(ENV_FILE)
        print(f"   Initialized: {ENV_FILE}")
    except Exception as e:
        print(f"   Failed to initialize: {e}")
        sys.exit(1)

    # 2. Set variables directly
    print("\n2. Setting CI/CD variables...")
    vars_to_set = {
        "DATABASE_URL": "postgresql://localhost:5432/mydb",
        "API_KEY": "sk-test-12345",
        "DEBUG": "false",
        "LOG_LEVEL": "info",
        "MAX_CONNECTIONS": "10",
    }
    for key, value in vars_to_set.items():
        mgr.set(key, value)
    print(f"   Set {len(vars_to_set)} variables")

    # 3. Create a JSON config and import it
    print("\n3. Creating and importing JSON config...")
    config_data = {
        "REDIS_URL": "redis://localhost:6379",
        "CACHE_TTL": "300",
        "APP_NAME": "my-cicd-app",
    }
    config_file = "/tmp/eval5_baseline_config.json"
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)

    try:
        result = mgr.load(config_file)
        print(f"   Import result: {result}")
    except ImportFailedError as e:
        print(f"   Import failed: {e}")
    except EVMError as e:
        print(f"   EVM error: {e}")

    # 4. Set up schemas
    print("\n4. Setting up validation schemas...")
    try:
        mgr.set_schema("DATABASE_URL", format="url")
        print("   DATABASE_URL: url format")
    except SchemaError as e:
        print(f"   Schema error for DATABASE_URL: {e}")

    try:
        mgr.set_schema("REDIS_URL", format="url")
        print("   REDIS_URL: url format")
    except SchemaError as e:
        print(f"   Schema error for REDIS_URL: {e}")

    try:
        mgr.set_schema("DEBUG", format="boolean")
        print("   DEBUG: boolean format")
    except SchemaError as e:
        print(f"   Schema error for DEBUG: {e}")

    try:
        mgr.set_schema("CACHE_TTL", format="integer")
        print("   CACHE_TTL: integer format")
    except SchemaError as e:
        print(f"   Schema error for CACHE_TTL: {e}")

    try:
        mgr.set_schema("MAX_CONNECTIONS", format="integer")
        print("   MAX_CONNECTIONS: integer format")
    except SchemaError as e:
        print(f"   Schema error for MAX_CONNECTIONS: {e}")

    # 5. Validate all
    print("\n5. Validating all variables against schemas...")
    try:
        results = mgr.validate_all()
        for var_name, result in sorted(results.items()):
            valid = result.get("valid", False)
            errors = result.get("errors", [])
            status = "PASS" if valid else "FAIL"
            print(f"   [{status}] {var_name}")
            for err in errors:
                print(f"          error: {err}")
    except EVMError as e:
        print(f"   Validation error: {e}")

    # 6. Error handling demonstration
    print("\n6. Testing error handling...")

    # KeyNotFoundError
    print("   Testing KeyNotFoundError...")
    try:
        mgr.get("NONEXISTENT_VAR")
    except KeyNotFoundError as e:
        print(f"   Caught KeyNotFoundError: {e}")

    # SchemaError - invalid value
    print("   Testing SchemaError (invalid URL)...")
    try:
        mgr.set("DATABASE_URL", "not-a-valid-url")
        result = mgr.validate("DATABASE_URL")
        if not result["valid"]:
            print(f"   Validation failed (expected): {result['errors']}")
    except SchemaError as e:
        print(f"   Caught SchemaError: {e}")

    # Restore valid value
    mgr.set("DATABASE_URL", "postgresql://localhost:5432/mydb")

    # SchemaError - no schema defined
    print("   Testing SchemaError (no schema defined)...")
    try:
        mgr.validate("APP_NAME")
    except SchemaError as e:
        print(f"   Caught SchemaError: {e}")

    # 7. Export validated config
    print("\n7. Exporting validated config...")
    export_file = "/tmp/eval5_baseline_export.json"
    try:
        result = mgr.export("json", export_file)
        print(f"   Export result: {result}")
    except ExportError as e:
        print(f"   Export failed: {e}")

    # 8. Final state
    print("\n8. Final environment state...")
    all_vars = mgr.list_vars()
    print(f"   Total variables: {len(all_vars)}")
    for key, value in sorted(all_vars.items()):
        print(f"   {key} = {value}")

    print("\n" + "=" * 60)
    print("CI/CD Workflow Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
