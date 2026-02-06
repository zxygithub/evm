# Test Case 目录总结

## 创建日期
2024-01-06

## 目录结构

```
tests/test_case/
├── __init__.py              # Python 包初始化文件
├── README.md                # 详细的测试文件说明
├── SUMMARY.md               # 本文件
├── test_config.json         # 标准JSON配置（15个变量）
├── test_config.env         # 标准.env配置（25个变量）
├── test_backup.json        # 备份文件格式（11个变量）
├── test_export.sh          # Shell脚本格式（12个变量）
├── dev_config.json         # 开发环境配置（8个变量）
├── prod_config.json        # 生产环境配置（10个变量）
└── test_env.json          # 测试环境配置（8个变量）
```

## 文件分类

### 1. 基础配置文件

| 文件 | 格式 | 变量数 | 用途 |
|------|------|---------|------|
| test_config.json | JSON | 15 | 标准配置导入测试 |
| test_config.env | .env | 25 | .env格式导入测试 |

### 2. 备份相关文件

| 文件 | 格式 | 变量数 | 用途 |
|------|------|---------|------|
| test_backup.json | JSON（备份） | 11 | 备份文件导入测试 |

### 3. 导出格式文件

| 文件 | 格式 | 变量数 | 用途 |
|------|------|---------|------|
| test_export.sh | Shell脚本 | 12 | Shell脚本格式测试 |

### 4. 环境配置文件

| 文件 | 格式 | 变量数 | 用途 |
|------|------|---------|------|
| dev_config.json | JSON | 8 | 开发环境分组测试 |
| prod_config.json | JSON | 10 | 生产环境分组测试 |
| test_env.json | JSON | 8 | 测试环境分组测试 |

## 使用方法

### 快速测试

```bash
# 1. 进入tests目录
cd tests

# 2. 运行测试脚本
python run_tests.py
```

### 手动测试

```bash
# 测试JSON导入
evm load tests/test_case/test_config.json

# 测试.env导入
evm load tests/test_case/test_config.env

# 测试备份导入
evm load tests/test_case/test_backup.json --format backup

# 测试分组导入
evm load tests/test_case/dev_config.json --group dev
evm load tests/test_case/prod_config.json --group prod

# 查看结果
evm list
evm list --show-groups
evm groups
```

## 测试场景

### 场景1：基本导入功能

```bash
# 清空环境
evm clear

# 导入标准JSON
evm load tests/test_case/test_config.json

# 验证导入
evm list | grep "APP_NAME"
```

### 场景2：多环境管理

```bash
# 清空并导入多环境
evm clear
evm load tests/test_case/dev_config.json --group dev
evm load tests/test_case/prod_config.json --group prod
evm load tests/test_case/test_env.json --group test

# 查看分组
evm list --show-groups
```

### 场景3：备份和恢复

```bash
# 导入备份
evm load tests/test_case/test_backup.json --format backup

# 检查时间戳显示
# 应该看到: "Detected backup file (timestamp: ...)"
```

### 场景4：替换模式

```bash
# 先导入开发配置
evm load tests/test_case/dev_config.json

# 用生产配置替换
evm load tests/test_case/prod_config.json --replace

# 只有生产配置的变量保留
evm list
```

### 场景5：混合格式导入

```bash
# 清空
evm clear

# 导入JSON
evm load tests/test_case/test_config.json

# 导入.env（会合并）
evm load tests/test_case/test_config.env

# 查看合并结果
evm list
```

## 测试验证点

### JSON导入测试
- ✅ 正确解析JSON对象
- ✅ 处理字符串值
- ✅ 处理数字值
- ✅ 处理布尔值
- ✅ 正确的变量数量

### .env导入测试
- ✅ 正确解析键值对
- ✅ 处理引号
- ✅ 忽略注释行
- ✅ 忽略空行
- ✅ 去除引号

### 备份导入测试
- ✅ 识别备份格式
- ✅ 显示时间戳
- ✅ 提取variables字段
- ✅ 正确的变量数量

### 分组导入测试
- ✅ 添加分组前缀
- ✅ 多个分组共存
- ✅ 按分组查看
- ✅ 分组列表正确

### Shell脚本导入测试
- ✅ 识别export语句
- ✅ 提取键值对
- ✅ 忽略shebang行
- ✅ 处理注释

## 清理测试数据

测试完成后，可以清理生成的文件：

```bash
# 清空EVM环境
evm clear

# 清理测试生成的导出文件
rm tests/test_case/exported.*
```

## 扩展测试文件

### 添加新的测试文件

1. **确定测试目的**
   - 要测试哪个功能？
   - 需要什么样的测试数据？

2. **选择合适的格式**
   - JSON：结构化数据
   - .env：键值对
   - Shell：导出脚本
   - 备份：带时间戳

3. **创建测试文件**
   - 使用清晰的文件名
   - 包含代表性数据
   - 添加必要的注释

4. **更新文档**
   - 在 README.md 中添加说明
   - 在本文件中记录

### 测试文件命名规范

- 格式：`[environment]_[type].[ext]`
- 示例：
  - `dev_config.json` - 开发环境的JSON配置
  - `prod_config.env` - 生产环境的.env配置
  - `test_backup.json` - 测试用的备份文件

## 与测试用例的集成

这些测试文件可以与 `tests/test_main.py` 中的测试用例配合使用：

```python
# 在测试中使用测试文件
def test_load_test_config(self):
    """Test loading from test config file."""
    test_file = os.path.join(
        os.path.dirname(__file__),
        'test_case',
        'test_config.json'
    )
    self.manager.load(test_file)
    # 断言验证
```

## 质量检查

在添加新测试文件前，请检查：

1. ✅ JSON文件格式正确
2. ✅ .env文件语法正确
3. ✅ 文件编码为UTF-8
4. ✅ 变量名有意义
5. ✅ 值具有代表性
6. ✅ 包含必要的注释
7. ✅ 文档已更新
8. ✅ 文件名清晰明确

## 贡献指南

如果你想为测试用例添加新的文件：

1. Fork 项目仓库
2. 创建新分支
3. 添加测试文件到 `tests/test_case/`
4. 更新相关文档（README.md、SUMMARY.md）
5. 运行测试验证
6. 提交Pull Request

## 联系方式

如有问题或建议，请在GitHub上提Issue。
