#!/usr/bin/env bash
# EVM Agent Wrapper
# Simplifies common EVM operations for agent usage.
# All output is JSON. All errors go to stderr.
#
# Usage:
#   source evm-wrapper.sh [env-file]
#
# Functions:
#   evm_set KEY VALUE          - Set a variable
#   evm_get KEY                - Get a variable (prints value only)
#   evm_exists KEY             - Check existence (exit 0/2)
#   evm_delete KEY             - Delete a variable
#   evm_list [PATTERN]         - List variables as JSON
#   evm_export FORMAT [FILE]   - Export variables
#   evm_load FILE              - Import variables
#   evm_run COMMAND [ARGS...]   - Run command with EVM env

set -euo pipefail

EVM_FILE="${1:-${EVM_CONFIG:-}}"
EVM_BASE="evm"
if [ -n "$EVM_FILE" ]; then
    EVM_BASE="evm --env-file $EVM_FILE"
fi

evm_set() {
    local key="$1" value="$2"
    $EVM_BASE --json set "$key" "$value" 2>/dev/null
}

evm_get() {
    local key="$1"
    local output
    output=$($EVM_BASE --json get "$key" 2>/dev/null) || return $?
    echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['value'])"
}

evm_exists() {
    local key="$1"
    $EVM_BASE --quiet get "$key" >/dev/null 2>&1
}

evm_delete() {
    local key="$1"
    $EVM_BASE --json delete "$key" 2>/dev/null
}

evm_list() {
    local pattern="${1:-}"
    if [ -n "$pattern" ]; then
        $EVM_BASE --json list "$pattern" 2>/dev/null
    else
        $EVM_BASE --json list 2>/dev/null
    fi
}

evm_export() {
    local format="${1:-json}" file="${2:-}"
    if [ -n "$file" ]; then
        $EVM_BASE --json export --format "$format" --output "$file" 2>/dev/null
    else
        $EVM_BASE --json export --format "$format" 2>/dev/null
    fi
}

evm_load() {
    local file="$1"
    $EVM_BASE --json load "$file" 2>/dev/null
}

evm_run() {
    $EVM_BASE exec -- "$@"
}

# Print usage if sourced without arguments and no functions called
if [ "${1:-}" = "--help" ]; then
    echo "EVM Agent Wrapper"
    echo ""
    echo "Usage: source evm-wrapper.sh [env-file]"
    echo ""
    echo "Functions:"
    echo "  evm_set KEY VALUE     Set a variable"
    echo "  evm_get KEY           Get value (prints value only)"
    echo "  evm_exists KEY        Check existence (exit 0=found, 2=missing)"
    echo "  evm_delete KEY        Delete a variable"
    echo "  evm_list [PATTERN]    List as JSON"
    echo "  evm_export FMT [FILE] Export (json/env/sh)"
    echo "  evm_load FILE         Import from file"
    echo "  evm_run CMD [ARGS]    Run with EVM environment"
fi
