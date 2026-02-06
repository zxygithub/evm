# Test Case Files

这个目录包含用于测试 EVM 功能的示例配置文件。

## 文件列表

### 标准配置文件

#### test_config.json
标准的 JSON 配置文件示例，包含：
- 应用基本信息
- 数据库配置
- 缓存配置
- API 配置
- 功能开关
- 日志配置
- 安全设置
- 外部服务配置

**用途：** 测试基本的 JSON 导入功能
**变量数量：** 15个

#### test_config.env
标准的 .env 配置文件示例，包含：
- 应用设置
- 数据库配置
- 缓存配置
- API 配置
- 功能开关
- 日志设置
- 安全配置
- 外部服务

**用途：** 测试 .env 格式导入功能
**变量数量：** 25个

### 备份文件

#### test_backup.json
EVM 备份文件格式示例，包含：
- 时间戳（timestamp）
- 环境变量字典（variables）

**用途：** 测试备份文件导入和恢复功能
**变量数量：** 11个
**特殊字段：** timestamp

### 导出文件

#### test_export.sh
Shell 脚本导出格式示例，包含：
- shebang 行（#!/bin/bash）
- export 语句
- 注释说明

**用途：** 测试 shell 脚本格式导入和导出
**变量数量：** 12个

### 环境配置文件

#### dev_config.json
开发环境配置文件示例，包含：
- 开发环境的典型设置
- DEBUG = true
- 本地服务器地址
- 开发工具相关配置

**用途：** 测试分组导入到 'dev' 环境
**变量数量：** 8个

#### prod_config.json
生产环境配置文件示例，包含：
- 生产环境的典型设置
- DEBUG = false
- 生产服务器地址
- 安全相关配置

**用途：** 测试分组导入到 'prod' 环境
**变量数量：** 10个

#### test_config.json
测试环境配置文件示例，包含：
- 测试环境的典型设置
- DEBUG = true
- 测试服务器地址
- Mock 服务配置

**用途：** 测试分组导入到 'test' 环境
**变量数量：** 8个

## 使用示例

### 1. 测试基本导入

```bash
# 导入 JSON 配置
evm load tests/test_case/test_config.json

# 导入 .env 配置
evm load tests/test_case/test_config.env

# 验证导入
evm list
```

### 2. 测试备份导入

```bash
# 导入备份文件
evm load tests/test_case/test_backup.json --format backup

# 应该显示时间戳
# 输出: Detected backup file (timestamp: 2024-01-06T12:30:45)
```

### 3. 测试分组导入

```bash
# 清空现有变量
evm clear

# 导入不同环境
evm load tests/test_case/dev_config.json --group dev
evm load tests/test_case/prod_config.json --group prod
evm load tests/test_case/test_config.json --group test

# 查看所有分组
evm list --show-groups
```

### 4. 测试导出并重新导入

```bash
# 设置一些变量
evm set TEST_VAR "test_value"
evm set ANOTHER_VAR "another_value"

# 导出为 JSON
evm export --format json -o tests/test_case/exported.json

# 清空
evm clear

# 重新导入
evm load tests/test_case/exported.json

# 验证
evm list
```

### 5. 测试替换模式

```bash
# 先导入一个配置
evm load tests/test_case/test_config.json

# 使用替换模式导入另一个
evm load tests/test_case/prod_config.json --replace

# 只有 prod_config 的变量会保留
evm list
```

### 6. 测试 shell 脚本导入

```bash
# 导入 shell 脚本
evm load tests/test_case/test_export.sh

# 导出的变量应该被正确识别
evm list
```

## 文件格式说明

### JSON 格式
- 必须是有效的 JSON 对象
- 所有键必须是字符串
- 值可以是字符串、数字或布尔值
- 不支持嵌套对象

### .env 格式
- 使用 `=` 分隔键和值
- 值可以用单引号或双引号包围
- 空行会被忽略
- 以 `#` 开头的行（注释）会被忽略

### 备份格式
- 必须包含 `timestamp` 字段（可选）
- 必须包含 `variables` 字段（必需）
- `variables` 必须是字典对象

### Shell 脚本格式
- 必须以 `#!/bin/bash` 开头
- 使用 `export KEY="value"` 格式
- 允许注释行

## 清理

测试完成后，可以清理生成的临时文件：

```bash
rm tests/test_case/exported.json
rm tests/test_case/imported.env
```

## 添加新的测试文件

当添加新的测试文件时，请：
1. 使用清晰的命名（如：`feature_name_type.json`）
2. 添加适当的注释
3. 在此 README 中记录文件的用途
4. 确保文件格式正确
5. 包含有代表性的测试数据

## 变量命名规范

- 使用大写字母和下划线
- 描述性名称（如：`DATABASE_URL` 而非 `DB_URL`）
- 避免特殊字符（除了下划线）
- 遵循常见的环境变量命名约定

## 格式问题说明

### test_group_config.json 格式问题

**注意：** `test_group_config.json` 文件包含嵌套的JSON对象，EVM无法正确处理。

**问题：**
- 文件包含微信小程序的完整配置（嵌套对象）
- 包含敏感的生产数据库信息
- 格式不符合EVM要求的简单键值对

**推荐方案：**
1. 使用 `test_group_config_correct.json` - 正确格式的示例
2. 参考 `FORMAT_ISSUE.md` 了解详细说明

**正确格式示例：**
```bash
evm load tests/test_case/test_group_config_correct.json --group dev
```

## 重要提示

### EVM支持的文件格式

EVM只支持以下格式：

1. **标准JSON（推荐）**
   ```json
   {
     "KEY1": "value1",
     "KEY2": "value2"
   }
   ```

2. **.env文件**
   ```
   KEY1="value1"
   KEY2="value2"
   ```

3. **不支持嵌套对象**
   ```
   {
     "nested": {
       "key": "value"
     }
   }
   ```

### 使用正确的测试文件

**推荐使用：**
- `test_config.json` - 标准JSON配置
- `test_config.env` - 标准.env配置
- `test_env.json` - 测试环境配置（已修正）
- `dev_config.json` - 开发环境配置
- `prod_config.json` - 生产环境配置
- `test_group_config_correct.json` - 分组配置（正确格式）

**避免使用：**
- `test_group_config.json` - 包含嵌套对象，格式不正确
