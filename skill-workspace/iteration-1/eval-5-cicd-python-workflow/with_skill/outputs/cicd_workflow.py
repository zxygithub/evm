#!/usr/bin/env python3
"""
CI/CD Pipeline Environment Management with EVM Python API

This script demonstrates a complete workflow for managing environment variables
in a CI/CD pipeline using EVM's Python API with proper exception handling.
"""

import json
import os
import sys
from pathlib import Path

# Import EVM Python API
from evm.manager import EnvironmentManager
from evm.exceptions import (
    EVMError,
    KeyNotFoundError,
    KeyAlreadyExistsError,
    StorageError,
    CorruptedStorageError,
    LockTimeoutError,
    ExportError,
    ImportFailedError,
    SchemaError,
    ValidationError,
    GroupNotFoundError,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print('='*70)


def main():
    """Execute the complete CI/CD environment management workflow."""
    
    # Use isolated storage for this demo
    env_file = "/tmp/eval5_test.json"
    config_file = "/tmp/eval5_config.json"
    export_file = "/tmp/eval5_export.json"
    
    print_section("CI/CD Pipeline Environment Management Demo")
    print("Using EVM Python API with proper exception handling")
    print(f"Storage: {env_file}")
    print(f"Config source: {config_file}")
    
    # =========================================================================
    # STEP 1: Create fresh EnvironmentManager instance
    # =========================================================================
    print_section("Step 1: Initialize EnvironmentManager")
    
    try:
        # Create manager with isolated storage
        mgr = EnvironmentManager(env_file=env_file)
        print("✓ EnvironmentManager initialized successfully")
        print(f"  Storage path: {mgr.env_file}")
        print(f"  Current variables: {len(mgr.list_vars())}")
    except StorageError as e:
        print(f"✗ Storage error: {e}")
        sys.exit(3)
    except EVMError as e:
        print(f"✗ EVM error: {e}")
        sys.exit(1)
    
    # =========================================================================
    # STEP 2: Import configuration from JSON file
    # =========================================================================
    print_section("Step 2: Import Configuration from JSON")
    
    try:
        # Load variables from JSON config file
        mgr.load(config_file)
        print("✓ Configuration imported successfully")
        
        # Display imported variables
        variables = mgr.list_vars()
        print(f"  Imported {len(variables)} variables:")
        for key, value in variables.items():
            # Mask sensitive values
            display_value = value if len(value) < 20 else value[:17] + "..."
            print(f"    - {key}: {display_value}")
    
    except ImportFailedError as e:
        print(f"✗ Import failed: {e}")
        sys.exit(4)
    except CorruptedStorageError as e:
        print(f"✗ Corrupted config file: {e}")
        sys.exit(3)
    except EVMError as e:
        print(f"✗ EVM error during import: {e}")
        sys.exit(1)
    
    # =========================================================================
    # STEP 3: Define schemas for validation
    # =========================================================================
    print_section("Step 3: Define Validation Schemas")
    
    schemas = [
        ("DATABASE_URL", None, True, "Database connection string (postgresql, mysql, etc.)"),
        ("API_URL", "url", True, "API endpoint URL (http/https)"),
        ("PORT", "port", True, "Application port number"),
        ("APP_NAME", None, True, "Application name"),
        ("DEBUG", "boolean", False, "Debug mode flag"),
        ("CACHE_TTL", "integer", False, "Cache time-to-live in seconds"),
    ]
    
    try:
        for var_name, format_type, required, description in schemas:
            mgr.set_schema(
                var_name,
                format=format_type,
                required=required,
                description=description
            )
            print(f"✓ Schema defined for {var_name}")
            print(f"    Format: {format_type or 'any'}")
            print(f"    Required: {required}")
            print(f"    Description: {description}")
    
    except SchemaError as e:
        print(f"✗ Schema definition error: {e}")
        sys.exit(6)
    except EVMError as e:
        print(f"✗ EVM error during schema setup: {e}")
        sys.exit(1)
    
    # =========================================================================
    # STEP 4: Validate all variables against schemas
    # =========================================================================
    print_section("Step 4: Validate Configuration")
    
    try:
        validation_results = mgr.validate_all()
        
        valid_count = 0
        invalid_count = 0
        warning_count = 0
        
        print("Validation Results:")
        print("-" * 70)
        
        for var_name, result in validation_results.items():
            status = "✓ VALID" if result["valid"] else "✗ INVALID"
            print(f"{status}: {var_name}")
            
            if result["valid"]:
                valid_count += 1
            else:
                invalid_count += 1
            
            # Display errors
            if result.get("errors"):
                for error in result["errors"]:
                    print(f"    ERROR: {error}")
            
            # Display warnings
            if result.get("warnings"):
                for warning in result["warnings"]:
                    print(f"    WARNING: {warning}")
                    warning_count += 1
        
        print("-" * 70)
        print(f"Summary: {valid_count} valid, {invalid_count} invalid, {warning_count} warnings")
        
        # Fail CI/CD pipeline if validation failed
        if invalid_count > 0:
            print("\n✗ Configuration validation FAILED")
            print("  CI/CD pipeline cannot proceed with invalid configuration")
            sys.exit(6)
        else:
            print("\n✓ Configuration validation PASSED")
            print("  CI/CD pipeline can proceed")
    
    except ValidationError as e:
        print(f"✗ Validation error: {e}")
        sys.exit(6)
    except SchemaError as e:
        print(f"✗ Schema error: {e}")
        sys.exit(6)
    except EVMError as e:
        print(f"✗ EVM error during validation: {e}")
        sys.exit(1)
    
    # =========================================================================
    # STEP 5: Demonstrate error handling with specific exceptions
    # =========================================================================
    print_section("Step 5: Error Handling Examples")
    
    # Example 1: KeyNotFoundError
    print("\nExample 1: Handling KeyNotFoundError")
    try:
        value = mgr.get("NONEXISTENT_VAR")
    except KeyNotFoundError as e:
        print(f"  ✓ Caught KeyNotFoundError: {e}")
    except EVMError as e:
        print(f"  ✗ Unexpected EVM error: {e}")
    
    # Example 2: KeyAlreadyExistsError
    print("\nExample 2: Handling KeyAlreadyExistsError")
    try:
        mgr.set("DATABASE_URL", "postgresql://new-db:5432/newdb")
        print("  ✓ Variable updated (set allows overwrite)")
    except KeyAlreadyExistsError as e:
        print(f"  ✓ Caught KeyAlreadyExistsError: {e}")
    except EVMError as e:
        print(f"  ✗ Unexpected EVM error: {e}")
    
    # Example 3: LockTimeoutError
    print("\nExample 3: Handling LockTimeoutError")
    print("  (Simulated - would occur with concurrent access)")
    try:
        # This would fail if another process held the lock
        mgr.set("TEST_VAR", "test_value")
        print("  ✓ Lock acquired successfully")
    except LockTimeoutError as e:
        print(f"  ✓ Caught LockTimeoutError: {e}")
        print("    Retry logic would go here")
    except StorageError as e:
        print(f"  ✓ Caught StorageError: {e}")
    except EVMError as e:
        print(f"  ✗ Unexpected EVM error: {e}")
    
    # Example 4: SchemaError with invalid schema
    print("\nExample 4: Handling SchemaError")
    try:
        mgr.set_schema("INVALID_VAR", format="nonexistent_format")
    except SchemaError as e:
        print(f"  ✓ Caught SchemaError: {e}")
    except EVMError as e:
        print(f"  ✗ Unexpected EVM error: {e}")
    
    # Example 5: Generic EVMError catch-all
    print("\nExample 5: Generic EVMError catch-all")
    try:
        # Some operation that might fail
        info = mgr.info()
        print(f"  ✓ Operation succeeded")
        print(f"    EVM version: {info.get('version', 'unknown')}")
    except EVMError as e:
        print(f"  ✓ Caught EVMError: {e}")
    
    # =========================================================================
    # STEP 6: Export validated configuration
    # =========================================================================
    print_section("Step 6: Export Validated Configuration")
    
    try:
        mgr.export(format_type="json", output_file=export_file)
        print("✓ Configuration exported successfully")
        print(f"  Export file: {export_file}")
        
        # Read and display export summary
        with open(export_file, 'r') as f:
            exported = json.load(f)
        print(f"  Exported {len(exported)} variables")
        
    except ExportError as e:
        print(f"✗ Export failed: {e}")
        sys.exit(4)
    except EVMError as e:
        print(f"✗ EVM error during export: {e}")
        sys.exit(1)
    
    # =========================================================================
    # STEP 7: Display operation history
    # =========================================================================
    print_section("Step 7: Operation History")
    
    try:
        history = mgr.get_history(limit=10)
        print(f"Last {len(history)} operations:")
        for entry in history:
            timestamp = entry.get("timestamp", "unknown")
            operation = entry.get("operation", "unknown")
            key = entry.get("key", "")
            print(f"  [{timestamp}] {operation}: {key}")
    except EVMError as e:
        print(f"✗ Error reading history: {e}")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_section("CI/CD Pipeline Summary")
    print("✓ EnvironmentManager initialized")
    print("✓ Configuration imported from JSON")
    print("✓ Schemas defined for validation")
    print("✓ All variables validated successfully")
    print("✓ Error handling demonstrated with specific exceptions")
    print("✓ Configuration exported")
    print("✓ Operation history recorded")
    print("\n" + "="*70)
    print("CI/CD pipeline can proceed with validated configuration")
    print("="*70)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
