# --nest 参数功能说明

## 功能概述

`--nest` 或 `-n` 参数允许导入包含嵌套对象的JSON文件，将第一层键作为分组名，第二层键值对作为该分组的环境变量。

## 使用场景

### 场景1：多环境配置

假设有一个配置文件包含多个环境的配置：

**config.json（嵌套格式）：**
```json
{
  "development": {
    "DATABASE_URL": "postgresql://localhost/dev",
    "DEBUG": "true",
    "API_URL": "http://localhost:3000"
  },
  "production": {
    "DATABASE_URL": "postgresql://prod-server/app",
    "DEBUG": "false",
    "API_URL": "https://api.example.com"
  },
  "staging": {
    "DATABASE_URL": "postgresql://staging-server/app",
    "DEBUG": "true",
    "API_URL": "https://staging-api.example.com"
  }
}
```

**使用 --nest 导入：**
```bash
evm load config.json --nest
```

**结果：**
```bash
Detected and imported 3 groups from nested structure
Loaded 9 environment variables from config.json
```

**导入后的变量：**
```
development:DATABASE_URL = postgresql://localhost/dev
development:DEBUG = true
development:API_URL = http://localhost:3000

production:DATABASE_URL = postgresql://prod-server/app
production:DEBUG = false
production:API_URL = https://api.example.com

staging:DATABASE_URL = postgresql://staging-server/app
staging:DEBUG = true
staging:API_URL = https://staging-api.example.com
```

### 场景2：微信小程序配置

**test_group_config.json：**
```json
{
  "会员小程序": {
    "username": "skin_aoyi",
    "password": "...",
    "host": "...",
    "database": "skinhat",
    "port": 3306
  },
  "会员小程序测试": {
    "username": "ap",
    "password": "...",
    "host": "47.103..73",
    "database": "testwechat",
    "port": 3306
  }
}
```

**使用 --nest 导入：**
```bash
evm load tests/test_case/test_group_config.json --nest
```

**结果：**
```bash
Detected and imported 2 groups from nested structure
Loaded 11 environment variables from test_group_config.json
```

**导入后的变量：**
```
会员小程序:database = skinhat
会员小程序:password = ...
会员小程序:port = 3306
会员小程序:ssh_username = ...
会员小程序:ssh_host = ...
会员小程序:ssh_password = ...
会员小程序:ssh_port = 22
会员小程序:local_bind_address = 120.0.1
会员小程序:local_bind_port = 13307

会员小程序测试:database = testwechat
会员小程序测试:password = ...
会员小程序测试:port = 3306
会员小程序测试:username = ap
```

### 场景3：混合格式

如果文件同时包含嵌套对象和简单键值对：

**mixed.json：**
```json
{
  "GLOBAL_KEY": "value",
  "dev": {
    "DB_URL": "localhost"
  },
  "prod": {
    "DB_URL": "prod-server"
  }
}
```

**使用 --nest 导入：**
```bash
evm load mixed.json --nest
```

**结果：**
```
GLOBAL_KEY = value
dev:DB_URL = localhost
prod:DB_URL = prod-server
```

## 参数规则

### --nest 的行为

1. **检测嵌套结构**
   - 检查JSON是否包含第一层嵌套对象
   - 如果第一层键的值是字典对象，则作为分组处理

2. **处理嵌套对象**
   - 第一层键名成为分组名
   - 第二层键值对成为该分组的环境变量
   - 格式：`group_name:key=value`

3. **处理简单键值对**
   - 如果第一层键的值不是字典，则按原样处理
   - 除非同时指定了`--group`参数

### 与 --group 的交互

| --nest | --group | 结果 |
|--------|--------|------|
| No | No | 正常导入 |
| No | Yes | 正常导入（添加指定分组前缀）|
| Yes | No | 嵌套导入（第一层作为分组）|
| Yes | Yes | 错误：两个参数冲突 |

**注意：** 不能同时使用 `--nest` 和 `--group`，会优先使用 `--nest`

## 格式要求

### 支持的嵌套格式

```json
{
  "group_name": {
    "KEY1": "value1",
    "KEY2": "value2",
    "KEY3": "value3"
  }
}
```

### 不支持的嵌套格式

```json
{
  "nested": {
    "deeper": {
      "KEY": "value"
    }
  }
}
```

**注意：** 只支持两层嵌套（第一层作为分组）

## 使用示例

### 示例1：多环境配置文件

**environments.json：**
```json
{
  "dev": {
    "NODE_ENV": "development",
    "DEBUG": "true",
    "API_URL": "http://localhost:3000"
  },
  "prod": {
    "NODE_ENV": "production",
    "DEBUG": "false",
    "API_URL": "https://api.example.com"
  }
}
```

**命令：**
```bash
# 导入为多个分组
evm load environments.json --nest

# 查看所有分组
evm list --show-groups

# 查看特定分组
evm listg dev
evm listg prod

# 获取分组中的变量
evm getg dev NODE_ENV
```

### 示例2：配置与服务对应

**services.json：**
```json
{
  "database": {
    "HOST": "localhost",
    "PORT": "5432",
    "USER": "dbuser",
    "PASSWORD": "dbpass"
  },
  "cache": {
    "HOST": "localhost",
    "PORT": "6379",
    "TTL": "3600"
  },
  "api": {
    "HOST": "localhost",
    "PORT": "3000",
    "TIMEOUT": "30000"
  }
}
```

**命令：**
```bash
# 导入为服务分组
evm load services.json --nest

# 查看database分组
evm list --group database

# 导出database配置
evm export --format json -o database-config.json --group database
```

### 示例3：微服务配置

**microservices.json：**
```json
{
  "user-service": {
    "DB_URL": "postgresql://localhost/users",
    "CACHE_URL": "redis://localhost/0"
    "DEBUG": "false"
  },
  "order-service": {
    "DB_URL": "postgresql://localhost/orders",
    "CACHE_URL": "redis://localhost/1",
    "DEBUG": "true"
  },
  "payment-service": {
    "DB_URL": "postgresql://localhost/payments",
    "API_KEY": "pay_api_key",
    "TIMEOUT": "30000"
  }
}
```

**命令：**
```bash
# 导入所有微服务配置
evm load microservices.json --nest

# 查看所有微服务
evm list --show-groups

# 切换到生产环境（批量）
evm deleteg user-service DEBUG
evm setg user-service DEBUG "false"
evm setg user-service CACHE_ENABLED "false"
```

## 与其他参数配合

### 配合 --replace

```bash
# 清空并替换为嵌套结构
evm clear
evm load environments.json --nest --replace

# 结果：只保留导入的环境
```

### 配合 --format

```bash
# 强制指定格式并导入嵌套结构
evm load config.json --format json --nest

# 即使文件扩展名不是.json，也会按JSON处理
```

## 最佳实践

### 1. 文件命名

- 使用有意义的文件名：`environments.json`, `services.json`, `config.json`
- 在文件名中描述内容类型：`dev-env.json`, `prod-env.json`

### 2. 分组命名

- 使用清晰的分组名：`development`, `production`, `staging`
- 避免中文字符作为键名（除非必要）
- 使用短划线分隔单词：`api_service`, `user_db`

### 3. 配置结构

- 保持两层嵌套：分组 → 键值对
- 每个分组包含相关的配置项
- 避免过深的嵌套（超过2层）

### 4. 环境变量命名

- 在组内使用描述性名称
- 避免与分组名重复
- 遵循环境变量命名约定（大写、下划线）

### 5. 文件组织

建议的结构：
```
project/
├── config/
│   ├── dev.json
│   ├── prod.json
│   ├── test.json
│   └── staging.json
├── services/
│   ├── database.json
│   ├── cache.json
│   └── api.json
└── app.json
```

## 优势

1. **批量管理**：一次导入多个环境的配置
2. **逻辑分组**：按环境或服务自动分组
3. **配置复用**：不同的配置使用相同的JSON文件
4. **灵活切换**：轻松在环境之间切换
5. **版本控制**：嵌套配置文件易于追踪变更

## 限制

1. 只支持两层嵌套（分组 + 键值对）
2. 嵌套对象的值必须是字典（key-value对）
3. 不能同时使用 `--nest` 和 `--group`
4. 嵌套键名不能包含特殊字符（建议使用英文字母和数字）

## 实现细节

### 嵌套检测逻辑

```python
if nest and isinstance(data, dict):
    for group_name, group_data in data.items():
        if isinstance(group_data, dict):
            # 这是一个分组，添加所有键值对
            for key, value in group_data.items():
                loaded_vars[f"{group_name}:{key}"] = value
        else:
            # 这是简单键值对，直接使用
            loaded_vars[group_name] = group_data
```

### 检测和计数

```python
groups_detected = sum(1 for v in data.values() if isinstance(v, dict))
print(f"Detected and imported {groups_detected} groups from nested structure")
```

## 总结

`--nest` 参数为EVM添加了强大的嵌套配置支持，使得处理多环境、多服务的配置文件变得更加方便和直观。
