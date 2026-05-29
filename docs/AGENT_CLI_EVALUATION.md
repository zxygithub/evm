# EVM 项目 Agent CLI 调用场景评估

**评估日期**：2026-05-30
**评估版本**：v1.7.0
**评估范围**：EVM 是否满足智能体（Agent）通过 CLI 调用的场景需求

---

## 总体评分：68/100（基本可用，但有若干阻碍）

| 维度 | 得分 | 说明 |
|------|------|------|
| 功能完备性 | 85 | CRUD/分组/导入导出/备份/加密/模板，覆盖全面 |
| **输出可解析性** | **45** | 核心弱点 — 输出是人类友好的表格，不是 JSON |
| 错误处理 | 75 | 异常体系完善，退出码 0/1，但无法区分错误类型 |
| 幂等性 | 80 | set/get/delete 行为合理，load 支持 replace/merge |
| 非交互性 | 85 | 无 prompt 确认，但 clear 也没有 --force |
| JSON 输出支持 | **20** | 无 --json 标志，无结构化输出模式 |

---

## 逐项分析

### 1. 输出可解析性 — 主要阻塞点

当前所有输出都是人类可读的文本格式：

```
# 当前 set 输出：
Set: API_KEY=abc123

# 当前 list 输出：
Environment Variables:
------------------------------------------------------
API_KEY             = abc123
DATABASE_URL        = postgresql://localhost/mydb
------------------------------------------------------
Total: 2 variables
```

Agent 解析这些输出需要复杂的正则或字符串匹配，极不稳定。标准做法是提供 `--json` / `--format json` 输出：

```json
{"status": "ok", "data": {"API_KEY": "abc123", "DATABASE_URL": "postgresql://..."}}
```

**建议**：所有命令添加 `--output json` 选项，输出 JSON 到 stdout。

### 2. 错误码不够细化

当前 `main()` 返回 `0` 或 `1`，agent 无法区分"变量不存在"和"文件权限错误"：

```python
# cli.py:313-323 - 所有错误都返回 1
except EVMError as e:
    print(f"Error: {e}", file=sys.stderr)
    return 1
```

**建议**：定义差异化退出码：
- `2` — 变量不存在（KeyNotFoundError）
- `3` — 文件/存储错误（StorageError）
- `4` — 输入格式错误（ImportError）
- `5` — 解密失败（DecryptionError）

### 3. 缺少 `--json` 输出标志

没有任何命令支持机器可读的结构化输出。Agent 需要能够：

```bash
evm get API_KEY --json          # → {"API_KEY": "abc123"}
evm list --json                 # → {"API_KEY": "abc123", ...}
evm info --json                 # → {"version": "1.7.0", ...}
evm search api --json           # → {"API_KEY": "abc123", "API_URL": "..."}
```

`info` 命令已经返回了一个结构化 dict，但输出却是人类格式的文本（`formatters.py:96-113`）。这是最容易添加 JSON 支持的命令 — 只需在 cli.py 的 info 分支加一个条件。

### 4. `clear` 缺少 `--force` / `--yes` 标志

虽然 `manager.clear()` 有 `force` 参数，但 CLI 层没有暴露。如果 agent 调用 `evm clear`，当前行为是直接清空（没有确认），这在无人值守场景下既是优点也是风险。应该：
- 默认要求 `--force` 或 `--yes`，防止误操作
- 或者保持当前行为但通过 `--json` 输出确认

### 5. `exec` 使用 `os.execvpe` — 替换当前进程

```python
# manager.py:334
os.execvpe(command[0], command, env_copy)
```

`os.execvpe` 替换当前进程，这意味着 `evm exec -- python script.py` 的执行流程是：evm 进程被 python 进程完全替换。从 agent 角度看，这导致返回值不可控（agent 无法捕获 evm 的退出码，因为 evm 进程已不存在）。这是设计选择而非 bug，但对 agent 调用是一个潜在问题。通常情况下 agent 期望 `evm exec` 返回被调用命令的退出码。

`os.execvpe` vs `subprocess.run` 的选择反映了两种哲学：exec 系列是"先污染后治理"模式（先加载环境变量再替换自身），优点是环境变量对子进程完全透明，缺点是无法在命令执行后做清理或日志。对 agent 场景，`subprocess.run` + 显式 env 传递更可控。

### 6. `loadmemory` 的作用域限制

`load_to_memory()` 将变量写入 `os.environ`，但这只影响当前进程及其子进程。对于 agent 的 CLI 调用场景，每次 `evm loadmemory` 都是一个独立进程，退出后环境变量就丢失了。这意味着 agent 无法真正"跨调用共享"环境变量 — 必须每次都用 `evm exec -- <cmd>` 包装，或使用 `eval $(evm export --format sh)` 模式。

这与工具设计目标一致（环境变量管理器，不是 shell session 管理器），但 agent 开发者需要了解这个限制。

---

## 亮点（做得好的地方）

1. **无外部依赖** — 纯 Python 标准库，安装极简，对 agent 部署友好
2. **异常体系完善** — `exceptions.py` 有 16 个异常类，层次清晰，便于调用方精确捕获
3. **dry-run 全覆盖** — 几乎所有写操作都支持，agent 可以先预览再执行
4. **原子写入 + 文件锁** — 并发安全性好，agent 并发调用不会损坏数据
5. **`--env-file` 隔离** — 允许 agent 使用独立存储文件，不影响用户本地配置
6. **`main(argv)` 返回 int** — 函数签名正确，可以被程序化调用（不需要 sys.argv）

---

## 改进优先级建议

| 优先级 | 改进项 | 工作量 |
|--------|--------|--------|
| **P0** | 所有命令添加 `--json` / `--format json` 输出 | 2-3天 |
| **P0** | 细化退出码（按异常类型映射） | 0.5天 |
| **P1** | `list` 和 `search` 的 JSON 输出模式 | 含在 P0 中 |
| **P1** | `exec` 改用 `subprocess.run` 并透传退出码 | 0.5天 |
| **P2** | `clear` 添加 `--force` 参数 | 0.5天 |
| **P2** | 添加 `--quiet` 模式（只输出值，无装饰文本） | 0.5天 |
| **P3** | `export --format sh` 的 eval 友好输出 | 已支持 |

---

## 设计原则

Agent CLI 工具设计的黄金法则：**stdout 是数据，stderr 是日志**。当前 EVM 将所有输出写入 stdout，agent 解析器必须从装饰性文本中提取数据。`--json` + stdout=JSON / stderr=人类可读的分离输出模式，是让 CLI 工具同时服务人类和 agent 的最小代价方案。

---

## 总结

EVM 作为人类使用的 CLI 工具设计质量不错 — 功能全面、安全措施到位、代码结构清晰。但作为 agent 可调用的 CLI 工具，缺少结构化输出（JSON 模式）和细化退出码是两个核心阻塞点。好消息是这两个改进点都很局部（主要在 `formatters.py` 和 `cli.py`），不需要架构变更。加入 `--json` 和差异化退出码后，这个项目对 agent 场景的适配度可以从 68 分提升到 85+ 分。
