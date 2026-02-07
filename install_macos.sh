#!/bin/bash
# =============================================================================
# EVM macOS 快速安装脚本
# 从 GitHub 下载并安装 EVM
# =============================================================================

set -e

VERSION="1.4.0"
INSTALL_DIR="/usr/local/bin"

echo "======================================"
echo "EVM macOS 安装脚本"
echo "======================================"
echo ""

# 检查是否在 macOS 上运行
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "错误: 此脚本只能在 macOS 上运行"
    exit 1
fi

# 下载地址
DOWNLOAD_URL="https://github.com/zxygithub/evm/releases/download/v${VERSION}/evm-cli-macos.tar.gz"

echo "正在下载 EVM v${VERSION}..."
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

if command -v curl &> /dev/null; then
    curl -fsSL "$DOWNLOAD_URL" -o evm-cli-macos.tar.gz
elif command -v wget &> /dev/null; then
    wget -q "$DOWNLOAD_URL" -O evm-cli-macos.tar.gz
else
    echo "错误: 需要 curl 或 wget 来下载文件"
    exit 1
fi

echo "✓ 下载完成"
echo ""

echo "正在解压..."
tar -xzf evm-cli-macos.tar.gz
echo "✓ 解压完成"
echo ""

echo "正在安装..."

# 检查是否有写入权限
if [[ ! -w "$INSTALL_DIR" ]]; then
    echo "需要管理员权限来安装到 $INSTALL_DIR"
    sudo cp evm-cli-macos/evm "$INSTALL_DIR/"
    sudo chmod +x "$INSTALL_DIR/evm"
else
    cp evm-cli-macos/evm "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/evm"
fi

echo "✓ 安装完成"
echo ""

# 清理
rm -rf "$TEMP_DIR"

echo "======================================"
echo "EVM 安装成功!"
echo "======================================"
echo ""
echo "版本: v${VERSION}"
echo "安装位置: ${INSTALL_DIR}/evm"
echo ""
echo "快速开始:"
echo "  evm --help          显示帮助信息"
echo "  evm set KEY VALUE   设置环境变量"
echo "  evm get KEY         获取环境变量"
echo "  evm list            列出所有变量"
echo ""
