# EVM 系统功能说明书

**版本：** 2.0.1  
**最后更新：** 2026-05-30  
**适用平台：** macOS / Linux

---

## 目录

- [1. 系统概述](#1-系统概述)
- [2. 安装与配置](#2-安装与配置)
- [3. 基本操作](#3-基本操作)
- [4. 分组管理](#4-分组管理)
- [5. 导入导出](#5-导入导出)
- [6. 备份与恢复](#6-备份与恢复)
- [7. 加密存储](#7-加密存储)
- [8. 模板展开](#8-模板展开)
- [9. Schema 验证](#9-schema-验证)
- [10. 操作历史](#10-操作历史)
- [11. 命令执行](#11-命令执行)
- [12. Shell 补全](#12-shell-补全)
- [13. AI Agent Skill](#13-ai-agent-skill)
- [14. 高级功能](#14-高级功能)
- [15. 全局选项](#15-全局选项)
- [16. 退出码说明](#16-退出码说明)
- [17. 最佳实践](#17-最佳实践)
- [18. 故障排除](#18-故障排除)

---

## 1. 系统概述

### 1.1 什么是 EVM

EVM（Environment Variable Manager）是一个强大的命令行工具，用于管理环境变量。它提供了安全、灵活、高效的环境变量管理解决方案，特别适用于以下场景：

- **多环境配置管理**：开发、测试、生产环境的配置隔离
- **敏感信息保护**：API 密钥、数据库密码等敏感信息的加密存储
- **配置验证**：确保配置值的格式正确性
- **配置导入导出**：与 `.env` 文件、JSON 配置的互操作
- **自动化脚本**：为 CI/CD 管道提供结构化的环境变量管理

### 1.2 核心特性

- ✅ **安全的加密存储**：使用 HKDF + HMAC-CTR v3 加密算法
- ✅ **灵活的分组管理**：支持命名空间隔离（如 dev、prod）
- ✅ **强大的导入导出**：支持 JSON、ENV、SH 三种格式
- ✅ **配置验证**：内置 Schema 验证机制
- ✅ **操作审计**：完整的操作历史记录
- ✅ **Agent 友好**：原生 JSON 输出支持
- ✅ **零依赖**：纯 Python 实现，无需外部依赖
- ✅ **原子操作**：文件锁保护，支持并发安全

### 1.3 系统架构

```
evm/
├── cli.py              # 命令行接口（参数解析、调度）
├── manager.py          # 核心业务逻辑
├── _io.py              # IOMixin（导入导出/备份恢复）
├── _groups.py          # GroupMixin（分组管理）
├── _history.py         # HistoryMixin（操作历史）
├── _schema.py          # SchemaMixin（Schema 验证）
├── _crypto.py          # 加密模块（HKDF + HMAC-CTR）
├── _completion.py      # Shell 补全生成器
├── _json.py            # JSON 输出辅助函数
├── formatters.py       # 输出格式化
└── exceptions.py       # 异常定义
```

---

## 2. 安装与配置

### 2.1 安装方式

#### 方式一：从源码安装（开发模式）

```bash
# 克隆仓库
git clone https://github.com/zxygithub/evm.git
cd evm

# 开发模式安装
pip install -e .

# 验证安装
evm --version
```

#### 方式二：用户级安装

```bash
# 安装到用户目录
pip install --user -e .

# 添加到 PATH（如果需要）
export PATH="$HOME/.local/bin:$PATH"
```

### 2.2 配置文件

EVM 默认使用以下文件存储配置：

| 文件 | 路径 | 权限 | 说明 |
|------|------|------|------|
| 环境变量存储 | `~/.evm/env.json` | 600 | 主要配置文件 |
| 操作历史 | `~/.evm/history.jsonl` | 600 | 操作日志 |
| Schema 定义 | `~/.evm/schema.json` | 600 | Schema 定义 |
| 文件锁 | `~/.evm/env.json.lock` | 600 | 并发控制锁 |

**注意**：所有敏感文件都会自动设置为 `600` 权限（仅所有者可读写）。

### 2.3 首次使用

```bash
# 查看帮助
evm --help

# 查看版本
evm --version

# 设置第一个变量
evm set MY_VAR "hello world"

# 获取变量
evm get MY_VAR
```

---

## 3. 基本操作

### 3.1 设置变量 (`set`)

**语法：**
```bash
evm set KEY VALUE
```

**参数：**
- `KEY`：变量名（支持字母、数字、下划线，可选分组前缀如 `dev:KEY`）
- `VALUE`：变量值

**示例：**
```bash
# 设置简单变量
evm set API_KEY "abc123"
evm set DATABASE_URL "postgresql://localhost/mydb"

# 设置带分组的变量（见分组管理章节）
evm setg dev API_KEY "dev-key-123"
```

**注意事项：**
- 如果变量已存在，将覆盖旧值
- 变量名只能包含字母、数字、下划线和冒号（用于分组）
- 操作会自动记录到历史日志

### 3.2 获取变量 (`get`)

**语法：**
```bash
evm get KEY
```

**示例：**
```bash
# 获取变量值
evm get API_KEY
# 输出: abc123

# 获取不存在的变量
evm get MISSING_KEY
# 输出: Error: Variable 'MISSING_KEY' not found
# 退出码: 2
```

**JSON 输出：**
```bash
evm --json get API_KEY
# 输出: {"status": "ok", "data": {"key": "API_KEY", "value": "abc123"}}
```

### 3.3 删除变量 (`delete`)

**语法：**
```bash
evm delete KEY
```

**示例：**
```bash
# 删除变量
evm delete API_KEY
# 输出: Deleted 'API_KEY'

# 删除不存在的变量
evm delete MISSING_KEY
# 退出码: 2
```

### 3.4 列出变量 (`list`)

**语法：**
```bash
evm list [--group GROUP] [--pattern PATTERN]
```

**参数：**
- `--group GROUP`：只显示指定分组
- `--pattern PATTERN`：按模式过滤（支持通配符）

**示例：**
```bash
# 列出所有变量
evm list

# 列出 dev 分组
evm list --group dev

# 按模式过滤
evm list --pattern "API_*"

# JSON 输出
evm --json list
# 输出: {"status": "ok", "data": {"API_KEY": "abc123", "DB_URL": "..."}}
```

### 3.5 清空所有变量 (`clear`)

**语法：**
```bash
evm clear [--force]
```

**参数：**
- `--force`：跳过确认提示

**示例：**
```bash
# 清空所有变量（会提示确认）
evm clear
# 输出: This will delete ALL variables. Continue? [y/N]

# 强制清空（不提示）
evm --force clear
# 或
evm clear --force
```

**⚠️ 警告**：此操作不可逆，建议先执行 `backup`。

### 3.6 搜索变量 (`search`)

**语法：**
```bash
evm search PATTERN [--case-sensitive]
```

**参数：**
- `PATTERN`：搜索模式
- `--case-sensitive`：区分大小写

**示例：**
```bash
# 搜索包含 "api" 的变量
evm search api
# 输出:
# API_KEY = abc123
# API_URL = https://api.example.com

# 区分大小写
evm search API --case-sensitive
```

### 3.7 重命名变量 (`rename`)

**语法：**
```bash
evm rename OLD_KEY NEW_KEY
```

**示例：**
```bash
# 重命名变量
evm rename API_KEY MY_API_KEY
# 输出: Renamed 'API_KEY' to 'MY_API_KEY'
```

### 3.8 复制变量 (`copy`)

**语法：**
```bash
evm copy SOURCE_KEY DEST_KEY
```

**示例：**
```bash
# 复制变量
evm copy API_KEY API_KEY_BACKUP
# 输出: Copied 'API_KEY' to 'API_KEY_BACKUP'
```

---

## 4. 分组管理

分组功能允许您使用命名空间（如 `dev:`、`prod:`）来组织变量，实现环境隔离。

### 4.1 设置分组变量 (`setg`)

**语法：**
```bash
evm setg GROUP KEY VALUE
```

**示例：**
```bash
# 设置开发环境变量
evm setg dev DATABASE_URL "postgresql://localhost/dev_db"
evm setg dev API_KEY "dev-key-123"

# 设置生产环境变量
evm setg prod DATABASE_URL "postgresql://prod-server/prod_db"
evm setg prod API_KEY "prod-key-456"
```

**存储格式：**
变量在内部存储为 `GROUP:KEY` 格式，例如：
```json
{
  "dev:DATABASE_URL": "postgresql://localhost/dev_db",
  "dev:API_KEY": "dev-key-123",
  "prod:DATABASE_URL": "postgresql://prod-server/prod_db",
  "prod:API_KEY": "prod-key-456"
}
```

### 4.2 获取分组变量 (`getg`)

**语法：**
```bash
evm getg GROUP KEY
```

**示例：**
```bash
# 获取开发环境的 API 密钥
evm getg dev API_KEY
# 输出: dev-key-123
```

### 4.3 列出分组变量 (`listg`)

**语法：**
```bash
evm listg GROUP
```

**示例：**
```bash
# 列出开发环境的所有变量
evm listg dev
# 输出:
# DATABASE_URL = postgresql://localhost/dev_db
# API_KEY = dev-key-123
```

### 4.4 删除分组变量 (`deleteg`)

**语法：**
```bash
evm deleteg GROUP KEY
```

**示例：**
```bash
# 删除开发环境的临时变量
evm deleteg dev TEMP_VAR
```

### 4.5 列出所有分组 (`groups`)

**语法：**
```bash
evm groups
```

**示例：**
```bash
# 查看所有分组
evm groups
# 输出:
# dev (2 variables)
# prod (2 variables)
# staging (1 variable)
```

### 4.6 删除整个分组 (`delete-group`)

**语法：**
```bash
evm delete-group GROUP [--force]
```

**示例：**
```bash
# 删除 staging 分组（会提示确认）
evm delete-group staging
# 输出: This will delete group 'staging' and all its variables. Continue? [y/N]

# 强制删除
evm delete-group staging --force
# 输出: Deleted group 'staging' and all its variables
```

**⚠️ 警告**：此操作会删除分组下的所有变量，且不可逆。

### 4.7 移动变量到分组 (`move-group`)

**语法：**
```bash
evm move-group KEY NEW_GROUP
```

**示例：**
```bash
# 将全局变量移动到 dev 分组
evm move-group API_KEY dev
# 输出: Moved 'API_KEY' to group 'dev'
# 变量名变为: dev:API_KEY
```

---

## 5. 导入导出

### 5.1 导入配置 (`load`)

**语法：**
```bash
evm load FILE [--format FORMAT] [--group GROUP] [--replace] [--nest]
```

**参数：**
- `FILE`：要导入的文件路径
- `--format FORMAT`：强制指定格式（`json`、`env`、`sh`），默认自动检测
- `--group GROUP`：将所有导入的变量放入指定分组
- `--replace`：替换模式（删除所有现有变量后再导入）
- `--nest`：嵌套导入（JSON 一级键作为分组名）

**示例：**

#### 导入 .env 文件
```bash
# 自动检测格式
evm load .env

# 强制指定格式
evm load config.txt --format env

# 导入到指定分组
evm load dev.env --group dev
```

**`.env` 文件格式：**
```env
# 注释行
API_KEY=abc123
DATABASE_URL="postgresql://localhost/mydb"
DEBUG='true'

# 支持多行值
MULTILINE="line1
line2
line3"
```

#### 导入 JSON 文件
```bash
# 简单 JSON
evm load config.json
```

**简单 JSON 格式：**
```json
{
  "API_KEY": "abc123",
  "DATABASE_URL": "postgresql://localhost/mydb"
}
```

#### 嵌套 JSON 导入
```bash
# 使用 --nest 参数
evm load multi-env.json --nest
```

**嵌套 JSON 格式：**
```json
{
  "dev": {
    "API_KEY": "dev-key-123",
    "DATABASE_URL": "postgresql://localhost/dev_db"
  },
  "prod": {
    "API_KEY": "prod-key-456",
    "DATABASE_URL": "postgresql://prod-server/prod_db"
  }
}
```

导入后变量名：
- `dev:API_KEY`
- `dev:DATABASE_URL`
- `prod:API_KEY`
- `prod:DATABASE_URL`

#### 替换模式导入
```bash
# 删除所有现有变量，然后导入
evm load new-config.json --replace
```

**⚠️ 警告**：`--replace` 会删除所有现有变量，建议先备份。

### 5.2 导出配置 (`export`)

**语法：**
```bash
evm export [--format FORMAT] [--output FILE] [--group GROUP]
```

**参数：**
- `--format FORMAT`：导出格式（`json`、`env`、`sh`），默认 `json`
- `--output FILE`：输出文件路径（默认输出到 stdout）
- `--group GROUP`：只导出指定分组

**示例：**

#### 导出为 JSON
```bash
# 导出到文件
evm export --format json --output backup.json

# 导出到 stdout
evm export --format json
```

#### 导出为 .env 文件
```bash
# 导出为 .env 格式
evm export --format env --output .env

# 只导出 dev 分组
evm export --format env --group dev --output dev.env
```

**`.env` 格式输出：**
```env
API_KEY=abc123
DATABASE_URL="postgresql://localhost/mydb"
MULTILINE="line1\nline2"
```

#### 导出为 Shell 脚本
```bash
# 导出为 shell 脚本
evm export --format sh --output env.sh

# 使用导出的脚本
source env.sh
```

**Shell 脚本格式：**
```bash
#!/bin/bash
export API_KEY='abc123'
export DATABASE_URL='postgresql://localhost/mydb'
```

**安全特性：**
- 键名和值都使用 `shlex.quote()` 转义，防止 shell 注入
- 导入时自动验证键名格式（只允许 `[A-Za-z_][A-Za-z0-9_]*`）

---

## 6. 备份与恢复

### 6.1 创建备份 (`backup`)

**语法：**
```bash
evm backup [--output FILE]
```

**参数：**
- `--output FILE`：备份文件路径（默认自动生成带时间戳的文件名）

**示例：**
```bash
# 自动命名备份
evm backup
# 输出: Backup created: ~/.evm/backup_20260530_143022.json

# 指定文件名
evm backup --output my-backup.json
# 输出: Backup created: my-backup.json
```

**备份文件格式：**
```json
{
  "timestamp": "2026-05-30T14:30:22.123456",
  "version": "2.0.1",
  "variables": {
    "API_KEY": "abc123",
    "dev:DATABASE_URL": "postgresql://localhost/dev_db"
  }
}
```

### 6.2 恢复备份 (`restore`)

**语法：**
```bash
evm restore FILE [--merge]
```

**参数：**
- `FILE`：备份文件路径
- `--merge`：合并模式（保留现有变量，只添加/更新备份中的变量）

**示例：**
```bash
# 完全恢复（替换所有变量）
evm restore backup_20260530_143022.json
# 输出: Restored from backup_20260530_143022.json

# 合并恢复
evm restore backup.json --merge
# 输出: Merged variables from backup.json
```

### 6.3 比较差异 (`diff`)

**语法：**
```bash
evm diff FILE
```

**示例：**
```bash
# 比较当前配置与备份的差异
evm diff backup.json
# 输出:
# Added (2):
#   NEW_VAR = new_value
#   ANOTHER = another_value
# 
# Removed (1):
#   OLD_VAR
# 
# Modified (1):
#   API_KEY: old_key -> new_key
# 
# Unchanged: 15 variables
```

**使用场景：**
- 在执行 `restore` 前查看将要发生的变更
- 审计配置变更
- 比较不同环境的配置差异

---

## 7. 加密存储

EVM 使用业界标准的加密算法保护敏感信息。

### 7.1 加密架构

**加密算法：** HKDF + HMAC-CTR v3

**密钥派生流程：**
```
机器标识 (hostname + uid + arch)
        │
        ▼
  PBKDF2-HMAC-SHA256 (100,000 次迭代, 16字节随机盐)
        │
        ▼
    主密钥 (32 字节)
        │
        ├─── HKDF-Expand (info="evm-encryption") ──→ enc_key (32 字节)
        │
        └─── HKDF-Expand (info="evm-authentication") ──→ mac_key (32 字节)
```

**加密格式：**
```
ENCv3:<salt_b64>:<iv_b64>:<mac_b64>:<ciphertext_b64>
```

**安全特性：**
- ✅ HKDF-Expand (RFC 5869) 密钥分离
- ✅ HMAC-CTR 流密码
- ✅ Encrypt-then-MAC (HMAC-SHA256)
- ✅ 常量时间 MAC 比较
- ✅ 自动从 v1/v2 迁移到 v3

### 7.2 设置加密变量

**语法：**
```bash
evm set KEY VALUE --secret
# 或
evm set --secret KEY VALUE
```

**示例：**
```bash
# 设置加密变量
evm set DB_PASSWORD "super_secret_password" --secret
# 输出:
# [WARNING] Encryption key is derived from machine identity (hostname + uid + arch).
# Changing hostname or migrating to another machine will make secrets unrecoverable.
# 
# Set 'DB_PASSWORD' = ENCv3:xxxxx:xxxxx:xxxxx:xxxxx

# 后续设置不再显示警告
evm set API_SECRET "api_secret_123" --secret
# 输出: Set 'API_SECRET' = ENCv3:xxxxx:xxxxx:xxxxx:xxxxx
```

### 7.3 获取加密变量

**语法：**
```bash
evm get KEY --secret
# 或
evm get --secret KEY
```

**示例：**
```bash
# 获取并解密
evm get DB_PASSWORD --secret
# 输出:
# [WARNING] Decrypted secret displayed on terminal (visible in scrollback).
# super_secret_password

# JSON 输出（不显示终端警告）
evm --json get --secret DB_PASSWORD
# 输出: {"status": "ok", "data": {"key": "DB_PASSWORD", "value": "super_secret_password"}}
```

**⚠️ 安全提示：**
- 终端输出的解密值可能被记录在 shell 历史中
- 建议使用 `--json` 输出并在脚本中处理
- 定期清理 shell 历史

### 7.4 自动迁移

如果您有 v1 或 v2 格式的加密变量，EVM 会在首次读取时自动迁移到 v3：

```bash
# 假设存在 v1 格式的加密变量
evm get OLD_SECRET --secret
# 输出:
# [INFO] Migrating 'OLD_SECRET' from v1 to v3...
# decrypted_value

# 查看存储，已更新为 v3 格式
evm get OLD_SECRET
# 输出: ENCv3:xxxxx:xxxxx:xxxxx:xxxxx
```

### 7.5 机器绑定限制

**重要提示：**

加密密钥从机器标识（hostname + uid + arch）派生，这意味着：

❌ **不能**：
- 在不同机器间共享加密变量
- 更改 hostname 后解密旧变量
- 在不同用户间共享加密变量

✅ **可以**：
- 同一机器、同一用户的不同会话间共享
- 备份加密变量并在同一机器上恢复
- 在同一机器上重新安装 EVM 后解密

**解决方案：**
- 使用外部密钥管理系统（如 HashiCorp Vault）
- 在迁移前导出明文配置
- 在新机器上重新设置加密变量

---

## 8. 模板展开

模板功能允许您在变量值中引用其他变量，实现配置的动态组合。

### 8.1 模板语法

**语法：** `{{VARIABLE_NAME}}`

**示例：**
```bash
# 定义基础变量
evm set API_HOST "api.example.com"
evm set API_PORT "443"

# 使用模板引用
evm set API_URL "https://{{API_HOST}}:{{API_PORT}}/v1"

# 展开模板
evm expand API_URL
# 输出: https://api.example.com:443/v1
```

### 8.2 展开模板 (`expand`)

**语法：**
```bash
evm expand KEY
```

**示例：**
```bash
# 简单展开
evm set DB_HOST "localhost"
evm set DB_PORT "5432"
evm set DB_NAME "mydb"
evm set DATABASE_URL "postgresql://{{DB_HOST}}:{{DB_PORT}}/{{DB_NAME}}"

evm expand DATABASE_URL
# 输出: postgresql://localhost:5432/mydb
```

**嵌套展开：**
```bash
# 支持多层嵌套
evm set BASE_URL "https://example.com"
evm set API_ENDPOINT "{{BASE_URL}}/api"
evm set FULL_URL "{{API_ENDPOINT}}/v1/users"

evm expand FULL_URL
# 输出: https://example.com/api/v1/users
```

**循环引用检测：**
```bash
# 防止无限循环
evm set A "{{B}}"
evm set B "{{A}}"

evm expand A
# 输出: Error: Circular reference detected: A -> B -> A
# 退出码: 6
```

### 8.3 获取展开后的值

```bash
# 方法一：使用 expand 命令
VALUE=$(evm expand DATABASE_URL)

# 方法二：使用 exec 注入环境变量
evm exec -- python -c "import os; print(os.environ['DATABASE_URL'])"
# 注意：exec 不会自动展开模板，需要在代码中处理
```

---

## 9. Schema 验证

Schema 功能允许您定义变量的格式规则，确保配置的正确性。

### 9.1 内置格式类型

| 格式 | 说明 | 示例 |
|------|------|------|
| `url` | URL 地址 | `https://example.com` |
| `email` | 邮箱地址 | `user@example.com` |
| `port` | 端口号（1-65535） | `8080` |
| `integer` | 整数 | `42`、`-10` |
| `boolean` | 布尔值 | `true`、`false`、`yes`、`no`、`1`、`0` |
| `path` | 文件路径 | `/usr/local/bin`、`./config` |
| `ipv4` | IPv4 地址 | `192.168.1.1` |
| `ipv6` | IPv6 地址 | `2001:0db8:85a3::8a2e:0370:7334` |

### 9.2 设置 Schema (`schema set`)

**语法：**
```bash
evm schema set KEY [--format FORMAT] [--pattern REGEX] [--required] [--description TEXT]
```

**参数：**
- `--format FORMAT`：内置格式类型
- `--pattern REGEX`：自定义正则表达式
- `--required`：标记为必需变量
- `--description TEXT`：添加描述

**示例：**

#### 使用内置格式
```bash
# URL 格式
evm schema set API_URL --format url --required

# 邮箱格式
evm schema set ADMIN_EMAIL --format email

# 端口号
evm schema set SERVER_PORT --format port

# 布尔值
evm schema set DEBUG_MODE --format boolean
```

#### 使用自定义正则
```bash
# API 密钥格式（32位十六进制）
evm schema set API_KEY --pattern "^[a-f0-9]{32}$"

# 版本号格式
evm schema set VERSION --pattern "^v[0-9]+\.[0-9]+\.[0-9]+$"

# AWS Region 格式
evm schema set AWS_REGION --pattern "^(us|eu|ap)-(north|south|east|west)-[1-9]$"
```

#### 添加描述
```bash
evm schema set DATABASE_URL --format url --required \
  --description "PostgreSQL connection string for main database"
```

### 9.3 查看 Schema (`schema get`)

**语法：**
```bash
evm schema get [KEY]
```

**示例：**
```bash
# 查看所有 Schema
evm schema get
# 输出:
# API_URL:
#   format: url
#   required: true
#   description: API endpoint URL
# 
# SERVER_PORT:
#   format: port

# 查看特定 Schema
evm schema get API_URL
# 输出:
# format: url
# required: true
# description: API endpoint URL
```

### 9.4 列出所有 Schema (`schema list`)

**语法：**
```bash
evm schema list
```

**示例：**
```bash
evm schema list
# 输出:
# API_URL (url, required)
# ADMIN_EMAIL (email)
# SERVER_PORT (port)
# DEBUG_MODE (boolean)
```

### 9.5 删除 Schema (`schema delete`)

**语法：**
```bash
evm schema delete KEY
```

**示例：**
```bash
evm schema delete TEMP_VAR
# 输出: Deleted schema for 'TEMP_VAR'
```

### 9.6 验证变量 (`validate`)

**语法：**
```bash
evm validate [KEY]
```

**参数：**
- `KEY`：要验证的变量名（可选，不指定则验证所有有 Schema 的变量）

**示例：**

#### 验证单个变量
```bash
# 验证通过的变量
evm validate API_URL
# 输出: ✓ API_URL is valid

# 验证失败的变量
evm validate SERVER_PORT
# 输出:
# ✗ SERVER_PORT is invalid:
#   - Value '99999' does not match format 'port'
# 退出码: 6
```

#### 验证所有变量
```bash
evm validate
# 输出:
# Validating 5 variables with schemas...
# 
# ✓ API_URL is valid
# ✓ ADMIN_EMAIL is valid
# ✗ SERVER_PORT is invalid:
#   - Value '99999' does not match format 'port'
# ✓ DEBUG_MODE is valid
# ⚠ TEMP_VAR has no value (required)
# 
# Summary: 3 valid, 1 invalid, 1 missing
# 退出码: 6（如果有错误或缺失的必需变量）
```

#### JSON 输出
```bash
evm --json validate
# 输出:
# {
#   "status": "error",
#   "data": {
#     "valid": 3,
#     "invalid": 1,
#     "missing": 1,
#     "details": {
#       "API_URL": {"valid": true},
#       "SERVER_PORT": {"valid": false, "errors": ["Value '99999' does not match format 'port'"]},
#       "TEMP_VAR": {"valid": false, "errors": ["Required variable has no value"]}
#     }
#   }
# }
```

### 9.7 Schema 文件存储

Schema 定义存储在 `~/.evm/schema.json`：

```json
{
  "API_URL": {
    "format": "url",
    "required": true,
    "description": "API endpoint URL"
  },
  "SERVER_PORT": {
    "format": "port"
  }
}
```

---

## 10. 操作历史

EVM 自动记录所有写操作（set、delete、clear 等）到历史日志。

### 10.1 查看历史 (`history`)

**语法：**
```bash
evm history [--limit N] [--format FORMAT]
```

**参数：**
- `--limit N`：显示最近 N 条记录（默认 20）
- `--format FORMAT`：输出格式（`table`、`json`）

**示例：**
```bash
# 查看最近 20 条记录
evm history
# 输出:
# 2026-05-30 14:30:22  set      API_KEY          success
# 2026-05-30 14:30:25  set      DATABASE_URL     success
# 2026-05-30 14:30:30  delete   TEMP_VAR         success
# 2026-05-30 14:31:00  setg     dev:API_KEY      success

# 查看最近 50 条
evm history --limit 50

# JSON 格式输出
evm history --format json
# 输出:
# [
#   {
#     "timestamp": "2026-05-30T14:30:22.123456",
#     "operation": "set",
#     "key": "API_KEY",
#     "status": "success"
#   },
#   ...
# ]
```

### 10.2 清空历史 (`history --clear`)

**语法：**
```bash
evm history --clear [--force]
```

**示例：**
```bash
# 清空历史（会提示确认）
evm history --clear
# 输出: This will delete all history. Continue? [y/N]

# 强制清空
evm history --clear --force
# 输出: Cleared 150 history entries
```

### 10.3 历史记录特性

**自动记录的操作：**
- ✅ `set` / `setg`
- ✅ `delete` / `deleteg`
- ✅ `clear`
- ✅ `rename`
- ✅ `copy`
- ✅ `move-group`
- ✅ `restore`

**不记录的操作：**
- ❌ `get` / `getg`（读取操作）
- ❌ `list` / `listg`（查询操作）
- ❌ `search`（查询操作）
- ❌ `expand`（查询操作）

**安全特性：**
- ❌ 不记录变量值（只记录键名）
- ✅ 历史文件权限为 600
- ✅ 超过 1000 条自动裁剪（保留最新 500 条）

### 10.4 历史文件位置

历史文件与 `env.json` 位于同一目录：

```
~/.evm/
├── env.json           # 环境变量存储
├── history.jsonl      # 操作历史
├── schema.json        # Schema 定义
└── env.json.lock      # 文件锁
```

如果使用 `--env-file` 指定自定义路径：

```bash
evm --env-file /tmp/my-project/env.json set KEY value
# 历史文件：/tmp/my-project/history.jsonl
```

---

## 11. 命令执行

### 11.1 执行命令 (`exec`)

**语法：**
```bash
evm exec -- COMMAND [ARGS...]
```

**功能：**
- 将所有 EVM 变量注入到子进程的环境变量中
- 透传子进程的退出码
- 支持模板展开（在子进程中）

**示例：**

#### 基本用法
```bash
# 运行 Python 脚本
evm exec -- python app.py
# Python 脚本可以通过 os.environ 访问所有 EVM 变量

# 运行 Node.js 应用
evm exec -- node server.js

# 运行 shell 命令
evm exec -- sh -c 'echo $API_KEY'
```

#### 退出码透传
```bash
# 子进程退出码会被透传
evm exec -- sh -c 'exit 42'
echo $?  # 输出: 42

# 用于 CI/CD 脚本
evm exec -- ./run-tests.sh
if [ $? -eq 0 ]; then
  echo "Tests passed"
else
  echo "Tests failed"
fi
```

#### 结合分组使用
```bash
# 只注入特定分组的变量（需要在代码中处理）
evm exec -- python -c "
import os
# 访问 dev 分组的变量
db_url = os.environ.get('dev:DATABASE_URL')
print(db_url)
"
```

### 11.2 加载到内存 (`loadmemory`)

**语法：**
```bash
evm loadmemory [--prefix PREFIX]
```

**参数：**
- `--prefix PREFIX`：只加载以指定前缀开头的变量

**功能：**
- 将 EVM 变量导出为 shell 的 `export` 语句
- 可以通过 `eval` 注入到当前 shell

**示例：**
```bash
# 加载所有变量到当前 shell
eval $(evm loadmemory)

# 验证
echo $API_KEY
# 输出: abc123

# 只加载特定前缀的变量
eval $(evm loadmemory --prefix "dev:")

# 验证
echo $dev:API_KEY
# 输出: dev-key-123
```

**注意事项：**
- `loadmemory` 不会自动展开模板
- 加载的变量只在当前 shell 会话中有效
- 建议使用 `exec` 来运行需要环境变量的命令

---

## 12. Shell 补全

EVM 支持为 Bash、Zsh 和 Fish 生成自动补全脚本。

### 12.1 生成补全脚本 (`completion`)

**语法：**
```bash
evm completion SHELL
```

**参数：**
- `SHELL`：Shell 类型（`bash`、`zsh`、`fish`）

### 12.2 Bash 补全

```bash
# 生成补全脚本
evm completion bash > ~/.evm-completion.bash

# 添加到 ~/.bashrc
echo 'source ~/.evm-completion.bash' >> ~/.bashrc

# 重新加载
source ~/.bashrc

# 测试补全
evm [TAB][TAB]
# 显示所有可用命令

evm get [TAB][TAB]
# 显示所有变量名
```

### 12.3 Zsh 补全

```bash
# 生成补全脚本
evm completion zsh > ~/.evm-completion.zsh

# 添加到 ~/.zshrc
echo 'source ~/.evm-completion.zsh' >> ~/.zshrc

# 重新加载
source ~/.zshrc

# 测试补全
evm [TAB]
```

### 12.4 Fish 补全

```bash
# 生成补全脚本到 Fish 配置目录
evm completion fish > ~/.config/fish/completions/evm.fish

# 测试补全
evm [TAB]
```

---

## 13. AI Agent Skill

EVM 提供了专门为 AI Agent 设计的 Skill，使 AI 助手能够智能地管理环境变量配置。

### 13.1 什么是 Agent Skill

Agent Skill 是一种结构化的能力描述文件，教会 AI 助手（如 Claude、Qwen 等）如何正确使用 EVM CLI 工具。它包含：

- **核心原则**：AI 使用 EVM 的最佳实践
- **常见工作流**：典型场景的操作指南
- **参考文档**：命令参考、API 文档、安全架构
- **辅助脚本**：Shell 包装函数
- **评估用例**：验证 Skill 效果的测试场景

### 13.2 Skill 目录结构

```
skill/
├── SKILL.md                  # 核心 Skill 文档（AI 阅读的主文件）
├── references/
│   ├── command-reference.md  # 完整命令参考
│   ├── exit-codes.md         # 退出码详细说明
│   ├── python-api.md         # Python API 文档
│   └── security.md           # 安全架构说明
├── scripts/
│   ├── evm-wrapper.sh        # Shell 辅助函数
│   └── evm-env-setup.sh      # 环境设置脚本
└── evals/
    └── evals.json            # 评估用例定义
```

### 13.3 安装 Skill

#### 方式一：使用 skill-creator 工具（推荐）

```bash
# 从 GitHub 安装
npx skills add zxygithub/evm/skill

# 验证安装
npx skills list
```

#### 方式二：手动安装

```bash
# 复制 skill 目录到 AI 的 skills 目录
cp -r /path/to/evm/skill ~/.claude/skills/evm-agent
# 或
cp -r /path/to/evm/skill ~/.qwen/skills/evm-agent
```

### 13.4 Skill 核心原则

Skill 教导 AI 遵循以下 5 个核心原则：

#### 原则 1：始终使用 `--json` 获取结构化输出

```bash
# ✅ 正确：JSON 输出可解析
evm get API_KEY --json
# stdout: {"status": "ok", "data": {"key": "API_KEY", "value": "abc123"}}

# ✅ 正确：错误也输出为 JSON
evm get MISSING_KEY --json
# stderr: {"status": "error", "error": "...", "error_code": 2}
```

#### 原则 2：使用 `--env-file` 实现配置隔离

```bash
# ✅ 正确：不触碰用户的全局配置
evm --env-file /tmp/project.json set API_KEY abc123
evm --env-file /tmp/project.json list --json
```

#### 原则 3：使用 `--force` 进行非交互执行

```bash
# ✅ 正确：AI 上下文中跳过确认
evm --force clear
evm --force delete-group staging
```

#### 原则 4：使用 `--dry-run` 预览变更

```bash
# ✅ 正确：先预览再执行
evm --dry-run set API_KEY new_value --json
# stdout: {"status": "ok", "data": {"message": "[DRY-RUN] Would set: API_KEY=new_value"}}
```

#### 原则 5：使用 `--quiet` 抑制人类输出

```bash
# ✅ 正确：只需要退出码或 JSON 数据
evm --quiet set KEY value
echo $?  # 0 = 成功
```

### 13.5 常见工作流示例

#### 工作流 1：多环境配置设置

```bash
# 创建开发环境配置
evm --env-file dev.json setg dev DATABASE_URL "postgresql://localhost/mydb"
evm --env-file dev.json setg dev API_KEY "dev-key-123"

# 创建生产环境配置
evm --env-file prod.json setg prod DATABASE_URL "postgresql://prod-server/mydb"
evm --env-file prod.json set --secret prod:API_KEY "prod-key-456"

# 验证配置
evm --env-file dev.json list --json
evm --env-file prod.json list --json
```

#### 工作流 2：导入、验证、导出

```bash
# 导入 .env 文件
evm --env-file config.json load .env

# 设置 Schema 验证规则
evm --env-file config.json schema set DATABASE_URL --format url --required
evm --env-file config.json schema set PORT --format port

# 验证所有变量
evm --env-file config.json validate --json

# 导出为 Shell 脚本
evm --env-file config.json export --format sh --output deploy.sh
```

#### 工作流 3：执行命令并透传退出码

```bash
# 使用 EVM 环境变量执行 Python 脚本
evm --env-file config.json exec -- python app.py
echo "退出码: $?"  # 透传 Python 脚本的退出码

# 使用 Python API 方式
cat > run_with_evm.py << 'EOF'
from evm.manager import EnvironmentManager

mgr = EnvironmentManager("config.json")
exit_code = mgr.execute(["python", "app.py"])
print(f"退出码: {exit_code}")
EOF

python run_with_evm.py
```

#### 工作流 4：备份、比较、恢复

```bash
# 创建备份
evm --env-file config.json backup --file backup.json

# 加载新配置（替换模式）
evm --env-file config.json load new-config.json --replace --json

# 比较差异
evm --env-file config.json diff backup.json --json
# stdout: {"status": "ok", "data": {"added": {...}, "removed": {...}, "changed": {...}}}

# 恢复备份
evm --env-file config.json restore backup.json --json
```

#### 工作流 5：CI/CD 集成工作流

```python
# cicd_workflow.py
from evm.manager import EnvironmentManager
from evm.exceptions import KeyNotFoundError, ImportFailedError, SchemaError

# 初始化隔离存储
mgr = EnvironmentManager("/tmp/ci_config.json")

# 导入配置
try:
    mgr.load("config.json")
except ImportFailedError as e:
    print(f"配置导入失败: {e}")
    exit(1)

# 设置 Schema 验证
mgr.set_schema("DATABASE_URL", format="url", required=True)
mgr.set_schema("API_URL", format="url", required=True)
mgr.set_schema("PORT", format="port")

# 验证所有配置
results = mgr.validate_all()
for key, result in results.items():
    if not result["valid"]:
        print(f"验证失败: {key}")
        for error in result["errors"]:
            print(f"  - {error}")
        exit(1)

# 导出为部署脚本
mgr.export("sh", "/tmp/deploy.sh")
print("配置验证通过，已生成部署脚本")
```

### 13.6 Skill 评估系统

EVM Skill 包含完整的评估系统，用于验证 Skill 的有效性。

#### 评估用例结构

```json
{
  "evals": [
    {
      "id": 1,
      "prompt": "我需要为开发环境和生产环境设置不同的配置...",
      "expected_output": "Agent 应该使用分组功能...",
      "files": []
    }
  ]
}
```

#### 运行评估

```bash
# 使用 skill-creator 运行评估
cd /path/to/evm
npx skills eval skill/

# 生成评估查看器
npx skills eval skill/ --viewer
# 输出：skill-workspace/iteration-1/review.html
```

#### 评估结果示例

```
Skill Benchmark: evm-agent
Date: 2026-05-30

配置对比：
- With Skill:    100% pass rate (40/40 assertions)
- Without Skill: 75% pass rate (30/40 assertions)

关键差异：
- With Skill 始终使用 --json 输出
- With Skill 正确使用 --force 跳过确认
- With Skill 使用 --dry-run 预览变更
- Without Skill 经常使用通用异常处理
```

### 13.7 Skill 辅助脚本

#### evm-wrapper.sh

提供便捷的 Shell 函数包装：

```bash
# 加载包装函数
source skill/scripts/evm-wrapper.sh /tmp/project.json

# 使用简化函数
evm_set API_KEY abc123
evm_get API_KEY
evm_exists API_KEY && echo "存在"
evm_delete API_KEY
evm_list --json
```

#### evm-env-setup.sh

快速设置环境变量到当前 Shell：

```bash
# 加载 EVM 配置到当前 Shell
eval $(skill/scripts/evm-env-setup.sh /tmp/project.json)

# 验证
echo $API_KEY
echo $DATABASE_URL
```

### 13.8 为 AI Agent 优化 CLI

EVM v2.0.1 针对 AI Agent 使用场景进行了多项优化：

#### 优化 1：`--json` 标志位置灵活

```bash
# 两种方式都有效
evm --json get API_KEY
evm get API_KEY --json
```

#### 优化 2：细化退出码

| 退出码 | 含义 | AI 处理建议 |
|--------|------|-------------|
| 0 | 成功 | 继续执行 |
| 2 | 变量不存在 | 创建或提示用户 |
| 3 | 存储错误 | 检查文件权限 |
| 5 | 解密失败 | 重新设置加密变量 |
| 6 | 验证失败 | 修正变量值 |

#### 优化 3：`exec` 透传退出码

```bash
# AI 可以捕获子进程的退出码
evm --env-file config.json exec -- python app.py
echo $?  # 透传 Python 脚本的退出码
```

### 13.9 Skill 最佳实践

#### ✅ 推荐做法

1. **始终使用 `--json`**：确保输出可解析
2. **使用隔离存储**：`--env-file` 避免污染全局配置
3. **预览再执行**：先 `--dry-run`，确认后再执行
4. **检查退出码**：根据退出码采取不同行动
5. **使用 Schema 验证**：确保配置正确性

#### ❌ 避免做法

1. **不要硬编码路径**：使用 `--env-file` 参数
2. **不要忽略错误**：检查退出码和 stderr
3. **不要跳过验证**：重要配置必须 validate
4. **不要明文存储敏感信息**：使用 `--secret` 加密

### 13.10 Skill 版本历史

- **v1.0.0** (2026-05-30)：初始版本
  - 5 个核心原则
  - 4 个参考文档
  - 2 个辅助脚本
  - 5 个评估用例
  - 评估通过率：100% (with skill) vs 75% (without skill)

---

## 14. 高级功能

### 14.1 编辑器编辑 (`edit`)

**语法：**
```bash
evm edit KEY
```

**功能：**
- 打开系统默认编辑器（`$EDITOR` 或 `$VISUAL`）
- 编辑完成后自动保存

**示例：**
```bash
# 编辑变量
evm edit LONG_CONFIG
# 打开 $EDITOR（如 vim、nano）

# 设置默认编辑器
export EDITOR=vim
evm edit CONFIG

# 或使用 VISUAL
export VISUAL=code  # VS Code
evm edit CONFIG
```

### 13.2 查看工具信息 (`info`)

**语法：**
```bash
evm info
```

**输出：**
```
EVM (Environment Variable Manager)
Version: 2.0.1
Author: EVM Tool
License: MIT
Python: 3.11.5
Platform: Darwin
Storage: /Users/username/.evm/env.json
Storage exists: True
Total variables: 25
Total groups: 3
Secret variables: 5
Groups:
  dev: 8 variables
  prod: 10 variables
  staging: 7 variables

Repository: https://github.com/zxygithub/evm
```

**JSON 输出：**
```bash
evm --json info
# 输出完整的 JSON 对象
```

### 13.3 编辑变量 (`edit`)

**语法：**
```bash
evm edit KEY
```

**功能：**
- 在系统编辑器中编辑变量值
- 保存并关闭编辑器后自动更新变量

**示例：**
```bash
# 编辑长文本配置
evm edit CONFIG_JSON
# 打开 $EDITOR（默认为 vim）

# 设置默认编辑器
export EDITOR=nano
evm edit CONFIG_JSON

# 使用 VS Code
export EDITOR="code --wait"
evm edit CONFIG_JSON
```

---

## 15. 全局选项

以下选项适用于所有命令：

### 15.1 `--json`

**功能：** 输出结构化 JSON 格式

**位置：** 可以在命令前或命令后

**示例：**
```bash
# 命令前
evm --json get API_KEY
# 输出: {"status": "ok", "data": {"key": "API_KEY", "value": "abc123"}}

# 命令后
evm get API_KEY --json
# 输出: {"status": "ok", "data": {"key": "API_KEY", "value": "abc123"}}

# 错误也输出为 JSON
evm --json get MISSING_KEY
# stderr: {"status": "error", "error": "Variable 'MISSING_KEY' not found", "error_code": 2}
# 退出码: 2
```

### 15.2 `--quiet`

**功能：** 静默模式，不输出任何文本（只返回退出码）

**示例：**
```bash
# 静默设置
evm --quiet set API_KEY "abc123"
echo $?  # 输出: 0

# 静默检查变量是否存在
evm --quiet get API_KEY
if [ $? -eq 0 ]; then
  echo "Variable exists"
fi
```

### 15.3 `--dry-run`

**功能：** 预览操作，不实际执行

**示例：**
```bash
# 预览设置
evm set API_KEY "new_value" --dry-run
# 输出: [DRY-RUN] Would set: API_KEY=new_value

# 预览删除
evm delete API_KEY --dry-run
# 输出: [DRY-RUN] Would delete: API_KEY

# 预览清空
evm clear --dry-run
# 输出: [DRY-RUN] Would clear 25 variables
```

### 15.4 `--force`

**功能：** 跳过确认提示，强制执行操作

**示例：**
```bash
# 强制清空（不提示）
evm clear --force

# 强制删除分组
evm delete-group dev --force

# 强制清空历史
evm history --clear --force
```

### 15.5 `--env-file`

**功能：** 指定自定义的存储文件路径

**示例：**
```bash
# 使用项目特定的配置
evm --env-file ./project.json set API_KEY "abc123"
evm --env-file ./project.json list

# 多项目隔离
evm --env-file ./project-a.json set KEY_A "value_a"
evm --env-file ./project-b.json set KEY_B "value_b"

# 每个项目有独立的文件
# ./project-a.json
# ./project-a.json.lock
# ./project-a.history.jsonl
# ./project-a.schema.json
```

---

## 16. 退出码说明

EVM 使用细化的退出码帮助脚本识别错误类型：

| 退出码 | 含义 | 异常类型 | 场景示例 |
|--------|------|----------|----------|
| 0 | 成功 | — | 操作成功完成 |
| 1 | 通用错误 | `OperationCancelledError` | 用户取消操作 |
| 2 | 变量不存在 | `KeyNotFoundError`、`KeyAlreadyExistsError` | `get MISSING_KEY` |
| 3 | 存储错误 | `StorageError`、`CorruptedStorageError`、`LockTimeoutError` | 文件损坏、权限错误、锁超时 |
| 4 | 导入导出错误 | `ImportFailedError`、`ExportError` | 文件格式错误、文件不存在 |
| 5 | 解密错误 | `DecryptionError` | 加密格式错误、MAC 验证失败 |
| 6 | 验证错误 | `ValidationError`、`SchemaError` | Schema 验证失败 |
| 7 | 分组错误 | `GroupNotFoundError`、`GroupOperationError` | 分组不存在、尝试删除 default 分组 |
| 8 | 备份错误 | `BackupError` | 备份文件损坏 |
| 9 | 编辑器错误 | `EditorError` | 编辑器不存在、编辑器返回非零退出码 |
| 10 | 命令未找到 | `CommandNotFoundError` | `exec` 的命令不存在 |

**脚本使用示例：**
```bash
#!/bin/bash

# 设置变量
evm set API_KEY "abc123"
case $? in
  0) echo "✓ Success" ;;
  3) echo "✗ Storage error" ;;
  *) echo "✗ Unknown error" ;;
esac

# 获取变量
VALUE=$(evm get API_KEY 2>/dev/null)
case $? in
  0) echo "Value: $VALUE" ;;
  2) echo "Variable not found" ;;
  3) echo "Storage error" ;;
  *) echo "Error: $?" ;;
esac
```

---

## 17. 最佳实践

### 17.1 项目隔离

**推荐：** 每个项目使用独立的 `--env-file`

```bash
# 项目 A
cd /path/to/project-a
evm --env-file ./evm.json set DATABASE_URL "postgresql://localhost/a_db"

# 项目 B
cd /path/to/project-b
evm --env-file ./evm.json set DATABASE_URL "postgresql://localhost/b_db"
```

**优点：**
- 项目配置互不干扰
- 可以提交到版本控制（如果使用加密）
- 便于团队协作

### 17.2 敏感信息处理

**推荐：** 所有敏感信息使用 `--secret` 加密

```bash
# ✅ 正确：加密存储
evm set DB_PASSWORD "super_secret" --secret
evm set API_KEY "api_key_123" --secret

# ❌ 错误：明文存储
evm set DB_PASSWORD "super_secret"
```

**注意：** 加密变量不能跨机器共享（见第 7.5 节）。

### 17.3 备份策略

**推荐：** 在进行重大变更前备份

```bash
# 变更前备份
evm backup --output backup-before-change.json

# 执行变更
evm set API_KEY "new_key"

# 验证变更
evm diff backup-before-change.json

# 如果有问题，恢复
evm restore backup-before-change.json
```

### 17.4 CI/CD 集成

**推荐：** 在 CI/CD 中使用 `--json` 和退出码

```yaml
# GitHub Actions 示例
- name: Validate configuration
  run: |
    evm validate
    if [ $? -ne 0 ]; then
      echo "Configuration validation failed"
      exit 1
    fi

- name: Run application
  run: |
    evm exec -- python app.py
```

### 17.5 分组命名规范

**推荐：** 使用一致的分组命名

```bash
# ✅ 推荐：小写、简洁
evm setg dev API_KEY "..."
evm setg prod API_KEY "..."
evm setg staging API_KEY "..."

# ❌ 不推荐：大小写混合、过长
evm setg Development API_KEY "..."
evm setg Production-Environment API_KEY "..."
```

### 17.6 变量命名规范

**推荐：** 使用大写字母和下划线

```bash
# ✅ 推荐
evm set DATABASE_URL "..."
evm set API_KEY "..."
evm set MAX_CONNECTIONS "..."

# ❌ 不推荐
evm set database_url "..."  # 小写
evm set ApiKey "..."        # 驼峰
evm set max-connections "..." # 连字符
```

### 17.7 Schema 验证

**推荐：** 为所有重要变量定义 Schema

```bash
# 定义 Schema
evm schema set DATABASE_URL --format url --required
evm schema set API_KEY --pattern "^[a-f0-9]{32}$" --required
evm schema set SERVER_PORT --format port
evm schema set DEBUG_MODE --format boolean

# 在部署前验证
evm validate
if [ $? -ne 0 ]; then
  echo "Configuration validation failed"
  exit 1
fi
```

### 17.8 模板使用

**推荐：** 使用模板减少重复配置

```bash
# 定义基础变量
evm set API_HOST "api.example.com"
evm set API_VERSION "v1"

# 使用模板组合
evm set API_URL "https://{{API_HOST}}/{{API_VERSION}}"
evm set WEBHOOK_URL "https://{{API_HOST}}/webhooks"
```

---

## 18. 故障排除

### 18.1 常见问题

#### Q1: 变量设置后无法获取

**症状：**
```bash
evm set API_KEY "abc123"
evm get API_KEY
# 输出: Error: Variable 'API_KEY' not found
```

**可能原因：**
1. 使用了不同的 `--env-file`
2. 存储文件权限问题
3. 存储文件损坏

**解决方案：**
```bash
# 检查存储文件
ls -la ~/.evm/env.json
cat ~/.evm/env.json

# 检查权限
chmod 600 ~/.evm/env.json

# 如果文件损坏，从备份恢复
evm restore backup.json
```

#### Q2: 加密变量无法解密

**症状：**
```bash
evm get DB_PASSWORD --secret
# 输出: Error: Decryption failed: MAC verification failed
```

**可能原因：**
1. 机器标识已更改（hostname、uid、arch）
2. 存储文件被手动修改
3. 加密格式不支持（v1/v2 未自动迁移）

**解决方案：**
```bash
# 检查机器标识
hostname
id -u
uname -m

# 如果标识已更改，需要重新设置加密变量
evm delete DB_PASSWORD
evm set DB_PASSWORD "new_password" --secret
```

#### Q3: 文件锁超时

**症状：**
```bash
evm set API_KEY "abc123"
# 输出: Error: Lock timeout after 5.0 seconds
```

**可能原因：**
1. 另一个 EVM 进程正在运行
2. 之前的进程异常退出，锁未释放

**解决方案：**
```bash
# 查找 EVM 进程
ps aux | grep evm

# 杀死进程
kill <PID>

# 或删除锁文件（谨慎操作）
rm ~/.evm/env.json.lock
```

#### Q4: Schema 验证失败

**症状：**
```bash
evm validate
# 输出:
# ✗ SERVER_PORT is invalid:
#   - Value '99999' does not match format 'port'
```

**解决方案：**
```bash
# 检查当前值
evm get SERVER_PORT
# 输出: 99999

# 修正为有效值
evm set SERVER_PORT "8080"

# 重新验证
evm validate
# 输出: ✓ SERVER_PORT is valid
```

#### Q5: 导入 .env 文件失败

**症状：**
```bash
evm load .env
# 输出: Error: Failed to import: Invalid key name 'API-KEY'
```

**原因：** 键名包含非法字符（连字符）

**解决方案：**
```bash
# 修正 .env 文件中的键名
# 将 API-KEY 改为 API_KEY
sed -i 's/API-KEY/API_KEY/g' .env

# 重新导入
evm load .env
```

### 18.2 调试技巧

#### 查看详细信息

```bash
# 使用 --json 查看详细错误
evm --json get MISSING_KEY
# 输出: {"status": "error", "error": "...", "error_code": 2}

# 检查存储文件内容
cat ~/.evm/env.json | python -m json.tool

# 查看操作历史
evm history --limit 50
```

#### 测试环境隔离

```bash
# 使用临时文件测试
evm --env-file /tmp/test.json set KEY value
evm --env-file /tmp/test.json list
rm /tmp/test.json
```

#### 检查文件权限

```bash
# 检查所有 EVM 文件权限
ls -la ~/.evm/

# 修正权限
chmod 600 ~/.evm/env.json
chmod 600 ~/.evm/history.jsonl
chmod 600 ~/.evm/schema.json
```

### 18.3 性能优化

#### 大量变量时的优化

```bash
# 如果变量数量超过 1000，建议分组管理
evm setg app1 KEY1 "..."
evm setg app2 KEY2 "..."

# 只加载需要的分组
eval $(evm loadmemory --prefix "app1:")
```

#### 减少文件 I/O

```bash
# 批量设置（减少文件写入次数）
evm load config.json --replace

# 而不是逐个设置
evm set KEY1 "..."
evm set KEY2 "..."
evm set KEY3 "..."
```

### 18.4 获取帮助

```bash
# 查看帮助
evm --help

# 查看特定命令帮助
evm set --help
evm schema set --help

# 查看版本
evm --version

# 查看完整信息
evm info

# 访问 GitHub
# https://github.com/zxygithub/evm
```

---

## 附录

### A. 命令速查表

| 命令 | 说明 | 示例 |
|------|------|------|
| `set KEY VALUE` | 设置变量 | `evm set API_KEY "abc"` |
| `get KEY` | 获取变量 | `evm get API_KEY` |
| `delete KEY` | 删除变量 | `evm delete API_KEY` |
| `list` | 列出所有变量 | `evm list` |
| `clear` | 清空所有变量 | `evm clear --force` |
| `search PATTERN` | 搜索变量 | `evm search "API_*"` |
| `rename OLD NEW` | 重命名变量 | `evm rename OLD NEW` |
| `copy SRC DST` | 复制变量 | `evm copy SRC DST` |
| `setg GROUP KEY VALUE` | 设置分组变量 | `evm setg dev KEY "val"` |
| `getg GROUP KEY` | 获取分组变量 | `evm getg dev KEY` |
| `listg GROUP` | 列出分组变量 | `evm listg dev` |
| `deleteg GROUP KEY` | 删除分组变量 | `evm deleteg dev KEY` |
| `groups` | 列出所有分组 | `evm groups` |
| `delete-group GROUP` | 删除整个分组 | `evm delete-group dev --force` |
| `move-group KEY GROUP` | 移动变量到分组 | `evm move-group KEY dev` |
| `load FILE` | 导入配置 | `evm load config.json` |
| `export` | 导出配置 | `evm export --format env` |
| `backup` | 创建备份 | `evm backup` |
| `restore FILE` | 恢复备份 | `evm restore backup.json` |
| `diff FILE` | 比较差异 | `evm diff backup.json` |
| `set --secret KEY VALUE` | 设置加密变量 | `evm set --secret KEY "val"` |
| `get --secret KEY` | 获取加密变量 | `evm get --secret KEY` |
| `expand KEY` | 展开模板 | `evm expand URL` |
| `schema set KEY` | 设置 Schema | `evm schema set KEY --format url` |
| `schema get [KEY]` | 查看 Schema | `evm schema get` |
| `schema list` | 列出所有 Schema | `evm schema list` |
| `schema delete KEY` | 删除 Schema | `evm schema delete KEY` |
| `validate [KEY]` | 验证变量 | `evm validate` |
| `history` | 查看操作历史 | `evm history` |
| `history --clear` | 清空历史 | `evm history --clear --force` |
| `exec -- COMMAND` | 执行命令 | `evm exec -- python app.py` |
| `loadmemory` | 加载到内存 | `eval $(evm loadmemory)` |
| `edit KEY` | 编辑器编辑 | `evm edit KEY` |
| `info` | 查看工具信息 | `evm info` |
| `completion SHELL` | 生成补全脚本 | `evm completion bash` |

### B. 全局选项速查

| 选项 | 说明 | 示例 |
|------|------|------|
| `--json` | JSON 输出 | `evm --json get KEY` |
| `--quiet` | 静默模式 | `evm --quiet set KEY "val"` |
| `--dry-run` | 预览操作 | `evm set KEY "val" --dry-run` |
| `--force` | 强制操作 | `evm clear --force` |
| `--env-file FILE` | 自定义存储文件 | `evm --env-file ./config.json list` |

### C. 退出码速查

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 通用错误 |
| 2 | 变量不存在 |
| 3 | 存储错误 |
| 4 | 导入导出错误 |
| 5 | 解密错误 |
| 6 | 验证错误 |
| 7 | 分组错误 |
| 8 | 备份错误 |
| 9 | 编辑器错误 |
| 10 | 命令未找到 |

---

**文档版本：** 1.0  
**最后更新：** 2026-05-30  
**适用版本：** EVM 2.0.1  
**作者：** EVM Tool  
**许可证：** MIT
