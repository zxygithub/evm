#!/bin/bash
# Demo script for EVM Group/Namespace Management features

echo "=== EVM Group Management Demo ==="
echo ""

# Check if EVM is installed
if ! command -v evm &> /dev/null
then
    echo "EVM is not installed. Please run: pip install -e ."
    exit 1
fi

echo "1. Setting up multiple environments..."
evm setg dev NODE_ENV development
evm setg dev DATABASE_URL "postgresql://localhost/dev"
evm setg dev API_KEY "dev_key_123"
evm setg dev DEBUG "true"

evm setg test NODE_ENV testing
evm setg test DATABASE_URL "postgresql://test-server/app"
evm setg test API_KEY "test_key_456"
evm setg test DEBUG "true"

evm setg prod NODE_ENV production
evm setg prod DATABASE_URL "postgresql://prod-server/app"
evm setg prod API_KEY "prod_key_789"
evm setg prod DEBUG "false"

echo ""
echo "2. Listing all groups:"
evm groups
echo ""

echo "3. Viewing variables grouped by namespace:"
evm list --show-groups
echo ""

echo "4. Viewing development environment variables:"
evm listg dev
echo ""

echo "5. Getting specific variable from test environment:"
echo "Test DATABASE_URL:"
evm getg test DATABASE_URL
echo ""

echo "6. Moving a variable to a different group:"
evm set GLOBAL_VAR "global_value"
echo "Moving GLOBAL_VAR to dev group..."
evm move-group GLOBAL_VAR dev
echo ""

echo "7. Updated dev environment:"
evm listg dev
echo ""

echo "8. Deleting a variable from test environment:"
evm deleteg test DEBUG
echo ""

echo "9. Updated test environment:"
evm listg test
echo ""

echo "10. Exporting dev environment to JSON:"
evm export --format json -o dev-environment.json
echo "Exported to dev-environment.json"
echo ""

echo "11. Deleting entire test group:"
evm delete-group test
echo ""

echo "12. Final group list:"
evm groups
echo ""

echo "=== Demo Complete ==="
echo ""
echo "Generated files:"
echo "  - dev-environment.json (exported dev environment)"
echo ""
echo "Clean up with: evm clear"
