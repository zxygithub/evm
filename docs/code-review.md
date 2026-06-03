># Code Review: EVM CLI (v2.4.0)

## 架构评价

整体设计不错。Mixin 组合模式 + Protocol 类型约束，模块拆分清晰（`_io.py`、`_groups.py`、`_history.py`、`_schema.py`、`_crypto.py`）。CLI 层用命令注册表模式调度，`--json` / `--quiet` 输出模式考虑了 Agent 调用场景。

## 严重问题

### 1. `info()` 和 `--version` 硬编码了过时版本号

**文件:** `manager.py:226`、`cli.py:137`

```python
'version': '2.3.0',  # 应该用 evm.__version__
```

`__init__.py` 里版本是 `2.4.0`，但这两处都写死了 `2.3.0`。应统一引用 `evm.__version__`。

### 2. `copy()` 静默覆盖目标变量

**文件:** `manager.py:195`

`rename()` 在目标已存在时会抛 `KeyAlreadyExistsError`，但 `copy()` 直接覆盖，没有检查也没有警告。如果这是有意设计应加文档说明，否则应加覆盖保护。

### 3. `set_schema` 参数名 `format` 遮蔽 Python 内建函数

**文件:** `_schema.py:87`

项目其他地方（如 `_io.py`、`cli.py`）都用 `format_type`，这里应保持一致。

## 中等问题

### 4. Windows 下加密盐值退化

**文件:** `manager.py:326`

`os.getuid()` 在 Windows 上不存在，`hasattr` 守卫后返回空字符串，导致盐值变短。应加 Windows 回退（如 `%USERNAME%` 或环境变量）。

### 5. `.env` 解析器不处理 `export KEY=value` 格式

**文件:** `_io.py:95`

常见 `.env` 文件会带 `export` 前缀。当前解析器会把 `export KEY` 整体当作 key 名，然后被 `_validate_key_name` 拒绝并跳过。应先 strip 掉 `export ` 前缀。

### 6. 历史裁切策略过于激进

**文件:** `_history.py:131`

超过 1500 条阈值时直接丢弃最老的一半（750+ 条）。建议改为保留最新 1000 条，行为更可预测。

### 7. Shell 补全脚本耦合 JSON 信封格式

**文件:** `_completion.py:26`

三个 shell 的补全都靠 `python3 -c` 解析 `evm list --json` 的 `data` 字段。如果 JSON 输出格式变更，补全会静默失败。建议提供专用的 `evm --keys-only` 命令。

### 8. `expand` 和 `_expand_value` 逻辑重复

**文件:** `manager.py:248-280`

两个几乎相同的递归展开函数。`expand` 应直接调用 `_expand_value`，消除重复。

## 轻微问题

### 9. `print_vars_by_group` 格式错误

**文件:** `formatters.py:71`

```python
print("\n+" * width)  # 输出一串 "+"，应该是 "=" * width
```

### 10. 全部 14 个源文件未通过 `ruff format`

发布前应执行 `ruff format evm/`。

### 11. `chmod 600` 散落多处

历史文件、schema 文件、env 文件各自硬编码 `0o600`，应提取为类常量。

### 12. `ImportError_` 兼容别名遮蔽内建

**文件:** `exceptions.py:117`

建议改名或在无外部消费者时移除。

### 13. 测试文件 `test_main.py` 有 2152 行

按功能拆分为多个文件会更易维护。

## 总结

核心逻辑扎实——原子写入、文件锁、Encrypt-then-MAC、完整异常体系、Agent 友好 JSON 模式。

**优先修复：**
- 版本号硬编码（快修）
- `copy()` 覆盖保护
- `.env` 解析器的 `export` 前缀处理
- `ruff format`

**其余为优化项。**
