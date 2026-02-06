#!/usr/bin/env python3
"""
Example script demonstrating how to use EVM in Python code.
"""

from evm.main import EnvironmentManager

def main():
    """Demonstrate EVM usage in Python code."""

    # Initialize with default location (~/.evm/env.json)
    manager = EnvironmentManager()

    print("=== EVM Python API Demo ===\n")

    # Set environment variables
    print("1. Setting environment variables...")
    manager.set('APP_NAME', 'My Application')
    manager.set('APP_VERSION', '1.0.0')
    manager.set('DEBUG', 'true')
    print()

    # Get environment variables
    print("2. Getting environment variables...")
    app_name = manager.get('APP_NAME')
    print(f"Application Name: {app_name}")
    print()

    # List all variables
    print("3. Listing all variables...")
    manager.list()
    print()

    # Search for variables
    print("4. Searching for 'APP'...")
    manager.search('APP')
    print()

    # Copy a variable
    print("5. Copying variable...")
    manager.copy('APP_NAME', 'APP')
    print()

    # Rename a variable
    print("6. Renaming variable...")
    manager.rename('DEBUG', 'DEBUG_MODE')
    print()

    # Export to different formats
    print("7. Exporting to different formats...")
    manager.export('json', 'output/config.json')
    manager.export('env', 'output/config.env')
    manager.export('sh', 'output/export.sh')
    print()

    # Load from file
    print("8. Loading from .env file...")
    manager.load('examples/example.env')
    print()

    # List all variables again
    print("9. Updated variable list...")
    manager.list()
    print()

    # Backup
    print("10. Creating backup...")
    manager.backup('output/backup.json')
    print()

    # Search in values
    print("11. Searching in values...")
    manager.search('localhost', search_value=True)
    print()

    # Clear all variables
    print("12. Clearing all variables...")
    manager.clear()
    print()

    print("=== Demo Complete ===")

if __name__ == '__main__':
    import os
    # Create output directory
    os.makedirs('output', exist_ok=True)
    main()
