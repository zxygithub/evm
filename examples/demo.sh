#!/bin/bash
# Demo script for EVM (Environment Variable Manager)
# This script demonstrates how to use EVM to manage environment variables

echo "=== EVM Demo Script ==="
echo ""

# Check if EVM is installed
if ! command -v evm &> /dev/null
then
    echo "EVM is not installed. Installing..."
    pip install -e .
fi

echo "1. Setting up development environment..."
evm set APP_NAME "My Application"
evm set APP_VERSION "1.0.0"
evm set ENVIRONMENT "development"
evm set DEBUG "true"
evm set DATABASE_URL "postgresql://user:password@localhost:5432/mydb"
echo ""

echo "2. Listing all environment variables:"
evm list
echo ""

echo "3. Getting a specific variable:"
echo "APP_NAME: $(evm get APP_NAME)"
echo ""

echo "4. Searching for variables containing 'APP':"
evm search APP
echo ""

echo "5. Exporting to .env format:"
evm export --format env -o demo.env
echo "Exported to demo.env"
echo ""

echo "6. Creating a backup:"
evm backup --file demo-backup.json
echo ""

echo "7. Renaming a variable:"
evm rename ENVIRONMENT ENV
echo ""

echo "8. Copying a variable:"
evm copy APP_NAME APP
echo ""

echo "9. Final list of variables:"
evm list
echo ""

echo "10. Cleaning up demo variables:"
evm delete APP
evm delete ENV
evm clear
echo ""

echo "=== Demo Complete ==="
echo ""
echo "Check the generated files:"
echo "  - demo.env (exported .env file)"
echo "  - demo-backup.json (backup file)"
