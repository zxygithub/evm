# test_group_config.json 格式问题说明

## 问题描述

`test_group_config.json` 文件包含不符合EVM导入要求的格式，导致导入结果与预期不一致。

## 问题详情

### 当前文件内容（test_group_config.json）

```json
{
  "会员小程序": {
    "username": "skin_aoyi",
    "password": "bvINb*3%@Ou6O!eH",
    "host": "rm-uf6s8tkgwedl.rds.aliyuncs.com",
    "database": "skinhat",
    "port": 3306,
    "ssh_username": "juuser",
    "ssh_password": "NRYC5^kPf@yhV5",
    "ssh_host": "106.116.108",
    "ssh_port": 22,
    "local_bind_port": 13307,
    "local_bind_address": "120.0.1"
  },
  "会员小程序测试": {
    "username": "ap",
    "password": "SkinbTUP",
    "host": "47.103..73",
    "database": "testwechat",
    "port": 3306
  }
}
```

### 问题分析

1. **格式问题**
   - 文件包含**嵌套的JSON对象**
   - EVM期望的是**简单的键值对**格式
   - 不支持嵌套的配置结构

2. **命名问题**
   - 键名包含中文字符（"会员小程序"）
   - 虽然EVM可以处理中文字符，但不符合最佳实践

3. **内容问题**
   - 包含**微信小程序的完整配置信息**
   - 包含**敏感的生产数据库信息**
   - 不符合"开发环境测试配置"的描述

4. **预期不符**
   - 文档说明应为8个环境变量
   - 实际内容包含两个嵌套对象，共16个字段
   - EVM导入时会忽略或报错

## 解决方案

### 方案1：使用正确的示例文件

我们已经创建了 `test_group_config_correct.json` 文件，包含正确格式：

```json
{
  "NODE_ENV": "development",
  "DATABASE_URL": "postgresql://localhost:5432/devdb",
  "REDIS_URL": "redis://localhost:6379/0",
  "API_URL": "http://localhost:3000/api",
  "DEBUG": "true",
  "LOG_LEVEL": "debug",
  "CACHE_ENABLED": "true",
  "PROFILING_ENABLED": "true"
}
```

**使用方法：**
```bash
evm load tests/test_case/test_group_config_correct.json --group dev
```

**预期结果：**
```
Loaded 8 environment variables from test_group_config_correct.json
Variables added to group 'dev'
```

### 方案2：如果需要使用原文件

如果确实需要使用包含嵌套对象的JSON文件，有几种处理方式：

1. **扁平化配置**：将嵌套对象转换为简单的键值对
   ```json
   {
     "APP_NAME": "My App",
     "APP_DB_HOST": "localhost",
     "APP_DB_PORT": "5432"
   }
   ```
   转换为：
   ```json
   {
     "APP_NAME": "My App",
     "APP_DB_HOST": "localhost",
     "APP_DB_PORT": "5432"
   }
   ```

2. **使用特定工具处理嵌套配置**
   - 使用专门的配置管理工具
   - 编写自定义脚本提取需要的变量

3. **分文件管理**
   - 将不同的配置拆分为多个简单文件
   - 每个文件只包含一组的变量

## 为什么EVM不支持嵌套对象

1. **设计原则**
   - EVM用于管理环境变量（KEY=VALUE）
   - 环境变量是扁平的键值对
   - 不支持复杂的嵌套配置结构

2. **实现考虑**
   - 简单性：易于理解和使用
   - 可靠性：减少解析错误
   - 兼容性：符合标准环境变量格式

3. **使用场景**
   - 环境变量通常用于简单的配置
   - 复杂配置应使用专门的配置文件格式
   - 或使用配置管理工具（如Consul、Etcd）

## 测试验证

### 正确的文件测试

```bash
# 导入正确格式的文件
evm load tests/test_case/test_group_config_correct.json --group dev

# 应该显示：
# Loaded 8 environment variables from test_group_config_correct.json
# Variables added to group 'dev'

# 查看导入的变量
evm listg dev

# 应该显示8个变量
```

### 原文件的问题

如果尝试导入 `test_group_config.json`：

```bash
evm load tests/test_case/test_group_config.json --group dev
```

**可能的问题：**
- JSON解析可能成功（因为是有效的JSON）
- 但导入的变量数不符合预期
- 某些嵌套字段可能被忽略
- 或者整个文件被忽略

## 建议

1. **使用 test_group_config_correct.json**
   这是正确的示例文件，符合所有要求

2. **遵循命名规范**
   - 使用英文字符作为键名
   - 使用下划线分隔单词（如：DATABASE_URL）
   - 使用大写字母（环境变量标准）

3. **保持简单结构**
   - 避免嵌套对象
   - 使用扁平的键值对
   - 每个键对应一个环境变量

4. **参考其他测试文件**
   - `dev_config.json` - 开发环境示例
   - `prod_config.json` - 生产环境示例
   - `test_env.json` - 测试环境示例

## 总结

- **问题：** test_group_config.json 包含不符合EVM要求的嵌套JSON对象
- **影响：** 导入结果与预期不一致
- **解决方案：** 使用 test_group_config_correct.json 或遵循正确的格式
- **原因：** EVM设计为管理简单的键值对环境变量

## 正确格式示例

### 好的格式

```json
{
  "APP_NAME": "My Application",
  "APP_VERSION": "1.0.0",
  "DEBUG": "true"
}
```

### 需要避免的格式

```json
{
  "nested": {
    "key": "value"
  },
  "多级嵌套": {
    "level1": {
      "level2": {
        "key": "value"
      }
    }
  }
}
```

**注意：** 虽然这些格式在技术上是有效的JSON，但EVM不会按预期方式处理它们。
