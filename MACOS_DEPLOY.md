# EVM macOS 独立版本部署指南

本文档介绍如何构建和部署 EVM 的 macOS 独立可执行版本，无需安装 Python 即可运行。

## 目录

- [系统要求](#系统要求)
- [快速安装](#快速安装)
- [从源码构建](#从源码构建)
- [安装方法](#安装方法)
- [卸载](#卸载)
- [故障排除](#故障排除)

## 系统要求

- macOS 10.14 (Mojave) 或更高版本
- 约 20MB 磁盘空间
- 可选：管理员权限（用于安装到系统目录）

## 快速安装

### 方法一：使用一键安装脚本

```bash
curl -fsSL https://raw.githubusercontent.com/zxygithub/evm/main/install_macos.sh | bash
```

或者使用 `wget`：

```bash
wget -qO- https://raw.githubusercontent.com/zxygithub/evm/main/install_macos.sh | bash
```

### 方法二：手动下载安装

1. 从 [Releases](https://github.com/zxygithub/evm/releases) 页面下载 `evm-cli-macos.tar.gz`

2. 解压并安装：

```bash
# 解压
tar -xzf evm-cli-macos.tar.gz

# 进入目录
cd evm-cli-macos

# 安装
./install.sh
```

## 从源码构建

如果你想从源码构建 macOS 版本：

### 前置条件

- macOS 10.14+
- Python 3.8+
- pip

### 构建步骤

1. 克隆仓库：

```bash
git clone https://github.com/zxygithub/evm.git
cd evm
```

2. 使用 Makefile 构建：

```bash
make build-macos
```

或者手动运行构建脚本：

```bash
bash build_macos.sh
```

3. 构建完成后，可执行文件位于：
   - `dist/evm` - 独立可执行文件
   - `evm-cli-macos.tar.gz` - 发布包

### Makefile 目标

```bash
make build-macos    # 构建 macOS 独立可执行文件
make install-macos  # 从源码安装到 macOS
make clean          # 清理构建文件
```

## 安装方法

### 系统范围安装（推荐）

```bash
# 使用安装脚本
cd evm-cli-macos
./install.sh

# 或手动安装
sudo cp evm /usr/local/bin/
sudo chmod +x /usr/local/bin/evm
```

### 用户级安装

```bash
# 安装到用户目录
mkdir -p ~/.local/bin
cp evm ~/.local/bin/
chmod +x ~/.local/bin/evm

# 添加到 PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 验证安装

```bash
evm --version
evm --help
```

## 卸载

```bash
# 删除可执行文件
sudo rm /usr/local/bin/evm

# 删除配置和数据（可选）
rm -rf ~/.evm
```

## 故障排除

### 1. "无法验证开发者" 安全提示

如果在运行 `evm` 时看到安全警告：

```bash
# 方法1：在系统偏好设置中允许
cd 系统偏好设置 > 安全性与隐私 > 通用 > 允许

# 方法2：使用命令行移除隔离属性
xattr -d com.apple.quarantine /usr/local/bin/evm
```

### 2. 权限被拒绝

```bash
# 确保有执行权限
chmod +x /usr/local/bin/evm
```

### 3. 命令未找到

```bash
# 检查安装位置
echo $PATH
which evm

# 如果安装到 /usr/local/bin，确保它在 PATH 中
# 对于 Apple Silicon Mac，可能需要：
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
```

### 4. 构建失败

```bash
# 确保安装了 PyInstaller
pip3 install pyinstaller

# 清理并重新构建
make clean
make build-macos
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `build_macos.sh` | macOS 构建脚本 |
| `install_macos.sh` | 在线安装脚本 |
| `evm.spec` | PyInstaller 配置文件 |
| `evm-cli-macos/` | 构建输出目录 |
| `evm-cli-macos.tar.gz` | 发布包 |

## 与 Python 版本的区别

| 特性 | macOS 独立版 | Python 版 |
|------|-------------|----------|
| Python 依赖 | 不需要 | 需要 |
| 文件大小 | ~15MB | ~50KB |
| 启动速度 | 稍慢 | 快 |
| 功能 | 完全相同 | 完全相同 |
| 更新 | 重新下载 | pip upgrade |

## 自动化发布

在 GitHub Actions 中自动构建：

```yaml
# .github/workflows/macos-build.yml
name: macOS Build

on:
  release:
    types: [created]

jobs:
  build:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Build
        run: make build-macos
      - name: Upload
        uses: actions/upload-release-asset@v1
        with:
          upload_url: ${{ github.event.release.upload_url }}
          asset_path: ./evm-cli-macos.tar.gz
          asset_name: evm-cli-macos.tar.gz
```

## 许可证

MIT License - 与主项目相同。
