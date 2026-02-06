# EVM 分组/命名空间功能

EVM 现在支持环境变量的分组/命名空间管理，使用 `group:key` 的格式来组织变量。

## 功能概述

分组功能允许您将环境变量按命名空间组织，例如：
- `dev:DATABASE_URL` - 开发环境的数据库URL
- `prod:DATABASE_URL` - 生产环境的数据库URL
- `test:API_KEY` - 测试环境的API密钥

## 新增命令

### 分组管理命令

```bash
# 列出所有分组
evm groups

# 在指定分组中设置变量
evm setg <group> <key> <value>

# 从指定分组获取变量
evm getg <group> <key>

# 从指定分组删除变量
evm deleteg <group> <key>

# 列出指定分组的所有变量
evm listg <group>

# 删除整个分组
evm delete-group <group>

# 将变量移动到另一个分组
evm move-group <key> <group>
```

### 增强的 list 命令

```bash
# 列出指定分组的变量
evm list --group <group>

# 按分组显示所有变量
evm list --show-groups
```

## 使用示例

### 创建开发环境配置

```bash
# 设置开发环境的变量
evm setg dev NODE_ENV development
evm setg dev DATABASE_URL "postgresql://localhost/dev"
evm setg dev API_KEY "dev_api_key"
evm setg dev DEBUG "true"

# 设置生产环境的变量
evm setg prod NODE_ENV production
evm setg prod DATABASE_URL "postgresql://prod-server/app"
evm setg prod API_KEY "prod_api_key"
evm setg prod DEBUG "false"
```

### 查看分组

```bash
# 列出所有分组
evm groups
# 输出:
# Available Groups:
# --------------------------------------------------
#   dev                            (4 variables)
#   prod                           (4 variables)
# --------------------------------------------------
# Total: 2 groups
```

### 查看特定分组的变量

```bash
# 查看开发环境的变量
evm listg dev

# 或者使用 --group 参数
evm list --group dev

# 输出:
# Environment Variables:
# ------------------------------------------------------------------
# dev:API_KEY      = dev_api_key
# dev:DATABASE_URL = postgresql://localhost/dev
# dev:DEBUG        = true
# dev:NODE_ENV     = development
# ------------------------------------------------------------------
# Total: 4 variables
```

### 按分组显示所有变量

```bash
evm list --show-groups

# 输出:
# Environment Variables (by group):
# ======================================================================
#
# [dev]
# ----------------------------------------------------------------------
# API_KEY      = dev_api_key
# DATABASE_URL = postgresql://localhost/dev
# DEBUG        = true
# NODE_ENV     = development
# ----------------------------------------------------------------------
#   4 variables
#
# [prod]
# ----------------------------------------------------------------------
# API_KEY      = prod_api_key
# DATABASE_URL = postgresql://prod-server/app
# DEBUG        = false
# NODE_ENV     = production
# ----------------------------------------------------------------------
#   4 variables
#
# ======================================================================
# Total: 2 groups, 8 variables
```

### 获取分组中的变量

```bash
evm getg dev DATABASE_URL
# 输出: postgresql://localhost/dev
```

### 删除分组中的变量

```bash
evm deleteg dev DEBUG
# 输出: Deleted: [dev] DEBUG
```

### 删除整个分组

```bash
evm delete-group test
# 输出: Deleted group 'test' and all its variables (5 total)
```

### 移动变量到分组

```bash
# 先创建一个非分组的变量
evm set API_KEY "my_key"

# 移动到开发分组
evm move-group API_KEY dev
# 输出: Moved: API_KEY -> dev:API_KEY
```

## 实际应用场景

### 场景1：多环境管理

```bash
# 开发环境
evm setg dev DB_HOST localhost
evm setg dev DB_PORT 5432

# 测试环境
evm setg test DB_HOST test-server
evm setg test DB_PORT 5432

# 生产环境
evm setg prod DB_HOST prod-server
evm setg prod DB_PORT 5432

# 快速切换环境
evm list --group dev
evm list --group prod
```

### 场景2：微服务配置

```bash
# 用户服务配置
evm setg user-service DB_URL "postgresql://localhost/users"
evm setg user-service CACHE_URL "redis://localhost/0"

# 订单服务配置
evm setg order-service DB_URL "postgresql://localhost/orders"
evm setg order-service CACHE_URL "redis://localhost/1"

# 支付服务配置
evm setg payment-service DB_URL "postgresql://localhost/payments"
evm setg payment-service API_KEY "payment_key"

# 查看所有服务配置
evm list --show-groups
```

### 场景3：项目配置

```bash
# 项目A配置
evm setg project-a API_KEY "key_a"
evm setg project-a API_URL "https://api-a.example.com"

# 项目B配置
evm setg project-b API_KEY "key_b"
evm setg project-b API_URL "https://api-b.example.com"

# 导出特定项目的配置
evm export --format json -o project-a.json
# 然后手动编辑，只保留 project-a:* 的变量
```

## 导出和导入

导出的文件包含完整的 `group:key` 格式：

```bash
# 导出所有变量（包括分组）
evm export --format json -o config.json

# config.json 内容示例:
{
  "dev:DATABASE_URL": "postgresql://localhost/dev",
  "dev:DEBUG": "true",
  "prod:DATABASE_URL": "postgresql://prod-server/app",
  "prod:DEBUG": "false"
}
```

## 注意事项

1. **默认命名空间**：不带 `:` 的变量属于默认命名空间
2. **删除默认分组**：不能删除 `default` 分组，使用 `evm clear` 来清除所有变量
3. **变量名冲突**：同一分组内变量名必须唯一
4. **导出格式**：导出时会保留完整的 `group:key` 格式

## 命令速查

| 命令 | 说明 |
|------|------|
| `evm groups` | 列出所有分组 |
| `evm setg group key value` | 在分组中设置变量 |
| `evm getg group key` | 获取分组中的变量 |
| `evm deleteg group key` | 删除分组中的变量 |
| `evm listg group` | 列出分组的变量 |
| `evm delete-group group` | 删除整个分组 |
| `evm move-group key group` | 移动变量到分组 |
| `evm list --group group` | 列出指定分组的变量 |
| `evm list --show-groups` | 按分组显示所有变量 |
