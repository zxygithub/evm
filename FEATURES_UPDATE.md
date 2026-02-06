# EVM 功能更新总结

## 更新日期
2024-01-06

## 版本
1.0.0 -> 1.1.0

---

## 功能1：改进的命令行行为

### 问题描述
之前当用户输入 `evm` 命令（不带任何子命令）时，会显示错误信息并退出。

### 解决方案
现在输入 `evm` 命令会显示完整的帮助信息，包括所有可用命令和使用示例。

### 使用示例

**之前：**
```bash
$ evm
# 输出: error: the following arguments are required: command
# 退出码: 1
```

**现在：**
```bash
$ evm
# 输出: 完整的帮助信息（包括所有命令、参数和示例）
# 退出码: 0
```

### 实现细节
- 修改了 `main()` 函数中的参数处理逻辑
- 当 `args.command` 为空时，调用 `parser.print_help()` 而不是报错退出

---

## 功能2：环境变量分组/命名空间管理

### 功能概述
添加了完整的分组/命名空间功能，允许用户使用 `group:key` 格式组织环境变量。

### 核心概念
使用冒号分隔的格式 `group:key` 来标识属于特定分组的变量：
- `dev:DATABASE_URL` - 开发环境的数据库配置
- `prod:DATABASE_URL` - 生产环境的数据库配置
- `test:API_KEY` - 测试环境的API密钥

### 新增命令

#### 1. groups - 列出所有分组
```bash
evm groups
```

#### 2. setg - 在分组中设置变量
```bash
evm setg dev DATABASE_URL "postgresql://localhost/dev"
```

#### 3. getg - 从分组获取变量
```bash
evm getg dev DATABASE_URL
```

#### 4. deleteg - 从分组删除变量
```bash
evm deleteg dev DEBUG
```

#### 5. listg - 列出分组的变量
```bash
evm listg dev
```

#### 6. delete-group - 删除整个分组
```bash
evm delete-group test
```

#### 7. move-group - 移动变量到分组
```bash
evm move-group API_KEY prod
```

### 增强的 list 命令

#### --group 参数
列出指定分组的变量：
```bash
evm list --group dev
```

#### --show-groups 参数
按分组显示所有变量：
```bash
evm list --show-groups
```

### 实际应用场景

#### 场景1：多环境管理
```bash
# 开发环境
evm setg dev NODE_ENV development
evm setg dev DATABASE_URL postgresql://localhost/dev
evm setg dev DEBUG true

# 测试环境
evm setg test NODE_ENV testing
evm setg test DATABASE_URL postgresql://test-server/app
evm setg test DEBUG true

# 生产环境
evm setg prod NODE_ENV production
evm setg prod DATABASE_URL postgresql://prod-server/app
evm setg prod DEBUG false

# 查看所有环境
evm list --show-groups

# 切换环境查看
evm listg dev
evm listg prod
```

#### 场景2：微服务配置
```bash
# 用户服务
evm setg user-service DB_URL postgresql://localhost/users
evm setg user-service CACHE_URL redis://localhost/0

# 订单服务
evm setg order-service DB_URL postgresql://localhost/orders
evm setg order-service CACHE_URL redis://localhost/1

# 支付服务
evm setg payment-service DB_URL postgresql://localhost/payments
evm setg payment-service API_KEY payment_key

# 查看所有服务配置
evm list --show-groups
```

### 技术实现

#### 数据结构
- 继续使用 JSON 格式存储所有环境变量
- 分组变量使用 `group:key` 作为完整键名
- 例如：`{"dev:DATABASE_URL": "postgresql://localhost/dev"}`

#### 向后兼容
- 不带 `:` 的变量属于默认命名空间
- 所有现有命令继续正常工作
- `getg` 命令会先查找 `group:key`，如果不存在则尝试查找 `key`

#### 导入导出
- 导出的 JSON 文件包含完整的 `group:key` 格式
- 可以通过编辑导出文件来筛选特定分组的变量
- 支持所有现有的导出格式（JSON、.env、shell脚本）

### 测试覆盖

新增了 10 个测试用例：
1. `test_set_grouped_variable` - 测试设置分组变量
2. `test_get_grouped_variable` - 测试获取分组变量
3. `test_delete_grouped_variable` - 测试删除分组变量
4. `test_list_groups` - 测试列出所有分组
5. `test_list_group_variables` - 测试列出分组变量
6. `test_list_with_show_groups` - 测试按分组显示
7. `test_delete_group` - 测试删除整个分组
8. `test_delete_default_group` - 测试删除默认分组（应该失败）
9. `test_move_to_group` - 测试移动变量到分组
10. `test_mixed_variables` - 测试混合分组和非分组变量

**总计：31 个测试用例，全部通过 ✅**

### 文档更新

#### 新增文档
1. **GROUPS.md** - 分组功能详细指南
   - 功能概述
   - 所有命令的详细说明
   - 使用示例
   - 实际应用场景
   - 注意事项

2. **examples/groups_demo.sh** - 分组功能演示脚本
   - 完整的使用示例
   - 可以直接运行的演示

#### 更新文档
1. **README.md**
   - 功能列表添加分组相关功能
   - 命令参考添加分组命令
   - 使用示例添加多环境管理示例
   - 快速参考

2. **CHANGELOG.md**
   - 添加版本 1.1.0 的变更记录
   - 详细列出所有新增和修改的内容

3. **tests/test_main.py**
   - 添加 10 个新的测试用例

### 使用限制

1. **默认命名空间保护**
   - 不能删除 `default` 命名空间
   - 使用 `evm clear` 来清除所有变量

2. **变量名冲突**
   - 同一分组内变量名必须唯一
   - 不同分组可以有相同的变量名

3. **分组名称**
   - 不支持包含 `:` 的分组名称
   - 不支持空分组名称

### 性能影响

- 内存使用：略微增加（需要维护分组索引）
- 查询性能：无显著影响（使用字典查找）
- 导出性能：无影响（直接输出键值对）

### 兼容性

- ✅ 向后兼容：所有现有功能继续工作
- ✅ 数据格式：使用现有 JSON 格式，无需迁移
- ✅ Python 版本：继续支持 Python 3.6+
- ✅ 操作系统：继续支持 macOS 和 Linux

---

## 总结

### 功能1：命令行行为改进
- ✅ 提升用户体验
- ✅ 符合 Unix 命令行工具的最佳实践
- ✅ 代码改动小，风险低

### 功能2：分组/命名空间管理
- ✅ 强大的环境变量组织能力
- ✅ 适合多环境、多服务配置
- ✅ 完整的命令支持
- ✅ 完善的测试覆盖
- ✅ 详细的文档和示例

### 测试状态
- ✅ 所有 31 个测试用例通过
- ✅ 手动测试验证所有新功能
- ✅ 向后兼容性测试通过

### 文档状态
- ✅ 主文档更新（README.md）
- ✅ 新功能详细指南（GROUPS.md）
- ✅ 版本历史更新（CHANGELOG.md）
- ✅ 演示脚本（examples/groups_demo.sh）
- ✅ 更新日志（FEATURES_UPDATE.md）

### 可以立即使用
所有新功能已经完全实现、测试并文档化，可以立即投入使用！
