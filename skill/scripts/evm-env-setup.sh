#!/usr/bin/env bash
# EVM Environment Setup Script
# Evaluates EVM variables into the current shell session.
#
# Usage:
#   eval "$(evm-env-setup.sh [env-file] [group])"
#
# This script generates shell export statements that can be eval'd
# to load EVM variables into the current shell environment.

set -euo pipefail

EVM_FILE="${1:-}"
GROUP="${2:-}"
EVM_BASE="evm"
if [ -n "$EVM_FILE" ]; then
    EVM_BASE="evm --env-file $EVM_FILE"
fi

# Generate export statements
if [ -n "$GROUP" ]; then
    $EVM_BASE export --format sh --group "$GROUP" 2>/dev/null | grep '^export '
else
    $EVM_BASE export --format sh 2>/dev/null | grep '^export '
fi
