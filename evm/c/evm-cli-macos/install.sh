#!/bin/bash
# EVM macOS Installation Script
set -e

echo "Installing EVM..."
INSTALL_DIR="/usr/local/bin"

if [[ ! -w "$INSTALL_DIR" ]]; then
    echo "需要管理员权限来安装到 $INSTALL_DIR"
    sudo cp evm "$INSTALL_DIR/"
    sudo chmod +x "$INSTALL_DIR/evm"
else
    cp evm "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/evm"
fi

echo "✓ EVM 安装成功!"
echo ""
echo "运行 evm --help 开始使用"
