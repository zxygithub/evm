#!/bin/bash
# =============================================================================
# EVM macOS 构建脚本
# 将 Python 代码打包成独立的 macOS 可执行文件
# =============================================================================

set -e

echo "======================================"
echo "EVM macOS 构建脚本"
echo "======================================"
echo ""

# 检查是否在 macOS 上运行
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "错误: 此脚本只能在 macOS 上运行"
    exit 1
fi

# 检查是否安装了 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python"
    exit 1
fi

echo "步骤 1: 安装依赖..."
python3 -m pip install pyinstaller -q
echo "✓ PyInstaller 安装完成"
echo ""

echo "步骤 2: 清理旧的构建文件..."
rm -rf build dist evm.spec
rm -rf EVM.app
rm -rf evm-cli-macos
rm -f evm-cli-macos.tar.gz
echo "✓ 清理完成"
echo ""

echo "步骤 3: 构建独立可执行文件..."
python3 -m PyInstaller \
    --name=evm \
    --onefile \
    --clean \
    --noconfirm \
    evm/main.py
echo "✓ 构建完成"
echo ""

echo "步骤 4: 创建发布包..."
mkdir -p evm-cli-macos
cp dist/evm evm-cli-macos/
cp README.md evm-cli-macos/
cp LICENSE evm-cli-macos/
cp QUICKSTART.md evm-cli-macos/

# 创建安装脚本
cat > evm-cli-macos/install.sh << 'EOF'
#!/bin/bash
# EVM macOS 安装脚本

set -e

echo "正在安装 EVM..."

# 创建安装目录
INSTALL_DIR="/usr/local/bin"

# 检查是否有写入权限
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
echo "运行 'evm --help' 开始使用"
EOF

chmod +x evm-cli-macos/install.sh
chmod +x evm-cli-macos/evm

# 打包
tar -czf evm-cli-macos.tar.gz evm-cli-macos

echo "✓ 发布包创建完成"
echo ""

echo "======================================"
echo "构建成功!"
echo "======================================"
echo ""
echo "生成的文件:"
echo "  - dist/evm              (独立可执行文件)"
echo "  - evm-cli-macos.tar.gz  (发布包)"
echo ""
echo "安装方法:"
echo "  1. 解压: tar -xzf evm-cli-macos.tar.gz"
echo "  2. 安装: cd evm-cli-macos && ./install.sh"
echo ""
echo "或者直接运行:"
echo "  ./dist/evm --help"
echo ""
