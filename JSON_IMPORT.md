# EVM JSON 格式导入功能

EVM 的 JSON 导入功能已全面增强，支持多种导入场景和灵活配置。

## 功能概述

### 支持的文件格式

1. **标准 JSON 配置文件**
   - 简单的键值对映射
   - 最常用的配置格式

2. **EVM 备份文件**
   - 包含时间戳和变量的完整备份
   - 使用 `evm backup` 命令创建

3. **标准 .env 文件**
   - 经典的环境变量格式
   - 兼容大多数应用

## 命令选项

```bash
evm load <file> [OPTIONS]
```

### 选项

- `--format`, `-f`: 强制指定文件格式
  - `json`: JSON 格式
  - `env`: .env 格式
  - `backup`: 备份文件格式

- `--replace`, `-r`: 替换模式（默认是合并模式）
  - 替换所有现有变量
  - 不与现有变量合并

- `--group`, `-g`: 将导入的变量添加到指定分组
  - 自动添加分组前缀 `group:key`

### 自动检测

如果不指定 `--format`，EVM 会自动检测文件格式：

1. 根据文件扩展名（.json, .env, .backup）
2. 根据文件内容（JSON 以 `{` 开头）

## 使用示例

### 基本用法

#### 导入 JSON 配置文件

**config.json:**
```json
{
  "APP_NAME": "My Application",
  "APP_VERSION": "1.0.0",
  "DATABASE_URL": "postgresql://localhost/app",
  "API_KEY": "your_api_key"
}
```

**命令：**
```bash
evm load config.json
```

**输出：**
```
Loaded 4 environment variables from config.json
```

#### 导入 .env 文件

**config.env:**
```env
APP_NAME="My Application"
APP_VERSION="1.0.0"
DATABASE_URL="postgresql://localhost/app"
API_KEY="your_api_key"
```

**命令：**
```bash
evm load config.env
# 或
evm load config --format env
```

### 高级用法

#### 导入到特定分组

将变量添加到 `dev` 分组：

```bash
evm load config.json --group dev
```

**结果：**
```
Loaded 4 environment variables from config.json
Variables added to group 'dev'
```

变量会被添加为：
```
dev:APP_NAME
dev:APP_VERSION
dev:DATABASE_URL
dev:API_KEY
```

#### 使用替换模式

替换所有现有变量而不是合并：

```bash
evm load config.json --replace
```

**输出：**
```
Replaced environment variables (4 total)
```

#### 强制指定格式

如果文件没有标准扩展名：

```bash
evm load config --format json
evm load settings --format env
evm load backup --format backup
```

### 导入备份文件

导入使用 `evm backup` 创建的备份：

**backup.json:**
```json
{
  "timestamp": "2024-01-06T12:00:00.000000",
  "variables": {
    "APP_NAME": "My Application",
    "API_KEY": "backup_key",
    "DEBUG": "false"
  }
}
```

**命令：**
```bash
evm load backup.json --format backup
# 或简单使用（自动检测）
evm load backup.json
```

**输出：**
```
Detected backup file (timestamp: 2024-01-06T12:00:00.000000)
Loaded 3 environment variables from backup.json
```

## 实际应用场景

### 场景1：多环境配置管理

**dev.json:**
```json
{
  "DATABASE_URL": "postgresql://localhost/dev",
  "DEBUG": "true",
  "LOG_LEVEL": "debug"
}
```

**prod.json:**
```json
{
  "DATABASE_URL": "postgresql://prod-server/app",
  "DEBUG": "false",
  "LOG_LEVEL": "error"
}
```

**使用：**
```bash
# 导入开发配置
evm load dev.json --group dev

# 导入生产配置
evm load prod.json --group prod

# 查看所有环境
evm list --show-groups
```

### 场景2：从备份恢复

```bash
# 1. 创建备份
evm backup --file before_change.json

# 2. 做一些修改
evm set NEW_VAR "new_value"

# 3. 如果需要恢复
evm load before_change.json --format backup
```

### 场景3：团队共享配置

**team-config.json:**
```json
{
  "API_URL": "https://api.team-project.com",
  "API_TIMEOUT": "30000",
  "RETRY_COUNT": "3"
}
```

团队成员导入：
```bash
evm load team-config.json
```

### 场景4：不同格式的导入

**混合使用多种配置源：**

```bash
# 从 JSON 导入
evm load config.json

# 从 .env 导入
evm load .env

# 从备份导入
evm load backup.json --format backup
```

### 场景5：带分组的批量导入

创建不同服务的配置：

**user-service.json:**
```json
{
  "DB_URL": "postgresql://localhost/users",
  "CACHE_URL": "redis://localhost/0"
}
```

**order-service.json:**
```json
{
  "DB_URL": "postgresql://localhost/orders",
  "CACHE_URL": "redis://localhost/1"
}
```

导入到不同分组：
```bash
evm load user-service.json --group user-service
evm load order-service.json --group order-service
```

查看所有服务：
```bash
evm list --show-groups
```

## 格式说明

### JSON 格式要求

1. **标准 JSON 对象**
   ```json
   {
     "KEY1": "value1",
     "KEY2": "value2"
   }
   ```

2. **字符串值**
   - 所有值应该被引号包围
   - 支持特殊字符和 Unicode

3. **键名规则**
   - 必须是有效的 JSON 字符串
   - 不支持嵌套对象
   - 键名区分大小写

### 备份文件格式

```json
{
  "timestamp": "ISO 8601 格式的时间戳",
  "variables": {
    "KEY1": "value1",
    "KEY2": "value2"
  }
}
```

- `timestamp`: 可选字段，备份创建时间
- `variables`: 必需字段，环境变量字典

### .env 格式要求

```env
KEY1="value1"
KEY2="value2"

# 注释行会被忽略
KEY3="value3"
```

- 使用 `=` 分隔键和值
- 值可以用单引号或双引号包围
- 空行和以 `#` 开头的行会被忽略

## 错误处理

### 文件不存在
```bash
$ evm load nonexistent.json
File not found: nonexistent.json
```

### 无效的 JSON 格式
```bash
$ evm load invalid.json
Error loading environment variables: Expecting value: line 2 column 1 (char 1)
```

### 不支持的格式
```bash
$ evm load config.xml --format xml
Unsupported format: xml
```

## 合并与替换模式

### 合并模式（默认）

```bash
evm load config.json
```

- 保留现有变量
- 添加或覆盖同名变量
- 不会删除任何现有变量

**示例：**

**现有变量：**
```
KEY1 = old_value1
KEY2 = old_value2
```

**导入文件：**
```json
{
  "KEY1": "new_value1",
  "KEY3": "new_value3"
}
```

**结果：**
```
KEY1 = new_value1  # 被覆盖
KEY2 = old_value2  # 保留
KEY3 = new_value3  # 新增
```

### 替换模式

```bash
evm load config.json --replace
```

- 删除所有现有变量
- 只保留导入的变量

**示例：**

**现有变量：**
```
KEY1 = old_value1
KEY2 = old_value2
```

**导入文件：**
```json
{
  "KEY3": "new_value3"
}
```

**结果：**
```
KEY3 = new_value3  # 只有导入的变量
```

## 最佳实践

1. **使用明确的文件扩展名**
   - 使用 `.json` 表示 JSON 文件
   - 使用 `.env` 表示环境变量文件

2. **创建备份**
   - 在批量导入前创建备份
   - 便于快速回滚

3. **使用分组**
   - 为不同环境/服务使用不同分组
   - 便于管理和切换

4. **验证导入**
   - 导入后使用 `evm list` 验证
   - 确认变量数量和内容正确

5. **使用 --replace 谨慎**
   - 确认要替换所有变量时才使用
   - 默认的合并模式更安全

## 与其他命令的配合

### 导入后导出

```bash
# 导入 JSON
evm load config.json

# 导出为 .env
evm export --format env -o output.env
```

### 导入后搜索

```bash
# 导入
evm load config.json

# 搜索特定变量
evm search API
```

### 导入到分组后查看

```bash
# 导入到 dev 分组
evm load config.json --group dev

# 查看分组
evm listg dev
# 或
evm list --group dev
```

## 性能考虑

- **小文件（<100KB）**: 瞬间加载
- **大文件（>100KB）**: 几秒钟内完成
- **数千个变量**: 仍然可以快速处理

## 安全建议

1. **不要提交敏感文件**
   - 不要将包含密码的 JSON 文件提交到 Git
   - 使用 `.gitignore` 排除这些文件

2. **验证来源**
   - 只从可信来源导入配置
   - 检查导入文件的权限

3. **使用加密存储**
   - 对于包含敏感信息的文件考虑加密
   - 或使用密钥管理服务
