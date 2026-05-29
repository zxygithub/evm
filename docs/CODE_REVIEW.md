# EVM 代码评审报告

**评审日期**：2026-05-30
**评审版本**：v1.7.0
**评审范围**：evm/ 包全部源码 + tests/test_main.py

---

## CRITICAL（阻塞项，共 3 个）

### 1. 并发写入竞态条件 — 可能导致数据丢失

**文件**：`evm/manager.py`，行 117-143

`_save_env_vars` 对 `mkstemp` 生成的唯一临时文件加锁，而非对目标文件 `env.json` 加锁。两个并发进程各自创建不同临时文件，各自成功获取互不冲突的锁，然后 `shutil.move` 后一个覆盖前一个的写入。

```python
# manager.py:117 — tmp_path 每个进程唯一，锁永远不冲突
tmp_fd, tmp_path = tempfile.mkstemp(dir=..., suffix='.tmp', prefix='.env_')
# ...
self._acquire_lock(f.fileno())   # <--- 锁的是临时文件，非 env.json
# ...
shutil.move(tmp_path, str(self.env_file))   # <--- 竞态窗口
```

**修复建议**：对目标文件 `self.env_file` 加锁（使用独立 `.lock` 文件或在打开目标文件后加锁），确保两个进程争夺同一资源。

---

### 2. 加密与机器绑定 — 换机 / 改 hostname 后秘文永久不可恢复

**文件**：`evm/manager.py`，行 452-459

加密密钥完全从 `platform.node() + getuid() + platform.machine()` 派生，无用户主密码、无恢复密钥、无警告提示。

后果：
- 修改 hostname → 所有秘文不可解密
- Docker/容器环境 hostname 变化频繁 → 加密不可用
- `env.json` 迁移到其他机器 → 所有 `ENCv2:` 值变垃圾
- 无法跨机迁移秘文

**修复建议**：支持可选用户主密码作为密钥派生输入；最低限度在首次使用 `--secret` 时打印明确警告。

---

### 3. 裸 `except Exception: pass` 静默吞没所有异常

**文件**：`evm/_history.py`，行 46 和行 100

```python
# Line 46 — log_operation()
except Exception:
    pass  # 日志记录不应影响主操作

# Line 100 — _trim_history()
except Exception:
    pass
```

`pass` 会吞没 `AttributeError`、`TypeError` 等编程错误，运维阶段完全无法调试。

**修复建议**：捕获具体异常类型 `except OSError`，而非裸 `Exception`。

---

## HIGH（强烈建议，共 7 个）

### 4. 重复密钥 XOR 加密（密码学弱密钥）

**文件**：`evm/manager.py`，行 476-478

```python
ciphertext = bytes(
    d ^ key[i % len(key)] for i, d in enumerate(data_bytes)
)
```

32 字节密钥以 `key[i % len(key)]` 循环复用。明文超过 32 字节时，同一密钥字节加密多个明文位置，产生经典的重复密钥 XOR 弱点。可被已知明文攻击恢复密钥流。

**修复建议**：用 AES-256-GCM 替换 XOR 加密，移除 HMAC 层（GCM 内置认证）。

---

### 5. 机器派生密钥熵极低

**文件**：`evm/manager.py`，行 452-465

```python
def _get_machine_salt(self) -> bytes:
    machine_id = (
        platform.node()      # hostname — 可猜解
        + str(os.getuid())   # 通常是 501
        + platform.machine() # "arm64" / "x86_64"
    )
    return machine_id.encode('utf-8')
```

攻击者知道 hostname 即可计算相同密钥。共享系统上读取 `/etc/hostname` + 知道 uid 即可解密所有秘文。

**修复建议**：使用用户提供的主密码作为 PBKDF2 输入，或利用系统 keychain（macOS Keychain / Linux Secret Service）存储高熵随机密钥。

---

### 6. 操作历史日志明文记录 value

**文件**：`evm/manager.py`，行 178 + `evm/_history.py`，行 41

```python
# manager.py:178
self.log_operation('set', key, f'value={value}')
```

`evm set API_KEY sk-abc123...`（忘记 `--secret`）→ 明文 value 写入 `~/.evm/history.jsonl`。且该文件无 `chmod 600` 保护（仅 `env.json` 和 `schema.json` 有权限限制）。

**修复建议**：
1. history 文件创建时加 `os.chmod(history_file, 0o600)`
2. `set` 操作只记录 key 名称，不记录 value
3. 或检测 key 名称含 `KEY/SECRET/TOKEN/PASS` 时自动红值

---

### 7. IPv6 校验正则过于宽松

**文件**：`evm/_schema.py`，行 34

```python
'ipv6': re.compile(r'^[0-9a-fA-F:]+$'),
```

匹配 `:::`, `abcdef`, 单个字符和非法 IPv6 地址，基本无校验效果。

**修复建议**：使用标准库 `ipaddress.IPv6Address()` 校验，或至少使用完整 IPv6 正则。

---

### 8. `.env` 导入引号解析不严谨

**文件**：`evm/_io.py`，行 78

```python
value = value.strip().strip("'").strip('"')
```

对不平衡引号（如 `KEY="value'`）处理错误 — 开头 `"` 和结尾 `'` 都被剥离，内容错误地变为无引号。

**修复建议**：显式匹配平衡引号对 `"..."` 或 `'...'`，而非盲剥。

---

### 9. Shell 导出 key 未转义 — 可构造武器化导出脚本

**文件**：`evm/_io.py`，行 160

```python
f.write(f'export {key}={shlex.quote(value)}\n')
```

value 已通过 `shlex.quote()` 正确转义，但 key 直接插值。若导入文件含恶意 key 名（如 `$(whoami)`），导出脚本被 source 时会执行命令。

**修复建议**：key 也用 `shlex.quote()` 包裹，或在导入时用 `^[A-Za-z_][A-Za-z0-9_:]*$` 校验 key 名。

---

### 10. Schema 文件损坏静默丢弃

**文件**：`evm/_schema.py`，行 50-54

```python
def _load_schema(self) -> Dict:
    except (json.JSONDecodeError, IOError):
        return {}   # <--- 所有 schema 定义静默丢失
```

Schema 文件损坏后所有定义被丢弃，用户完全无感知，认为校验仍在生效但实际什么都没做。

**修复建议**：至少打印 warning；考虑抛 `CorruptedStorageError` 让用户决定修复或重置。

---

## MEDIUM（改进建议，共 8 个）

| # | 文件 | 行 | 问题 |
|---|------|-----|------|
| 11 | `_schema.py` | 13,15 | 未使用的 import：`List`, `KeyNotFoundError`, `ValidationError` |
| 12 | `_io.py` | 257 | 异常重抛未用 `raise ... from e`，丢失原始 traceback |
| 13 | `_io.py` | 153-155 | `.env` 导出值含换行时格式破坏 |
| 14 | `exceptions.py` | 38,59 | `PermissionError_` / `ImportError_` 下划线命名不惯用，建议 `StoragePermissionError` / `ImportFailedError` |
| 15 | `manager.py` | 476-482 | 加密和 MAC 共用同一密钥，违反 NIST SP 800-108 |
| 16 | `manager.py` | 524-539 | 旧版 v1 加密无盐、无完整性校验（建议加自动迁移到 v2） |
| 17 | `_history.py` | 41,97 | 历史写入非原子操作（append 无锁、truncate 非 rename 模式） |
| 18 | `cli.py` | 318-319 | 解密秘文直接输出到 stdout，终端 scrollback 可见 |

---

## 加密模块专项评估

| 维度 | 现状 | 建议 |
|------|------|------|
| 加密算法 | 重复密钥 XOR | → AES-256-GCM |
| 密钥派生 | 机器信息 → PBKDF2（低熵） | → 用户主密码 + PBKDF2（高熵） |
| 密钥分离 | 加密/MAC 同钥 | → HKDF-Expand 派生独立子密钥 |
| 完整性 | HMAC-SHA256（✓） | → GCM 内置认证（可简化） |
| 常量时间比较 | `hmac.compare_digest`（✓） | 保持 |
| 旧版兼容 | v1 无盐无 MAC（弱） | → 首次读取自动迁移到 v2 |
| 恢复机制 | 无 | → 支持可选主密码 / 恢复码 |

---

## 测试覆盖缺口

1. **并发写入竞态** — 无测试（发现 #1）
2. **机器绑定加密跨机迁移** — 无测试
3. **`evm exec` 错误路径** — 命令不存在 / 权限拒绝未覆盖
4. **Schema 文件损坏恢复** — 静默 `return {}` 未验证用户是否被通知
5. **`.env` 导入多行 / 不平衡引号** — 仅简单用例
6. **History 文件损坏（部分 JSONL 行）** — `get_history` 跳过非法行的行为未测试
7. **URL 校验 IPv6 方括号表示法** — 未覆盖
8. **锁超时真实竞争** — 仅测试顺序写入，未测试实际竞争场景

---

## 积极发现

- `hmac.compare_digest` 常量时间 MAC 比较
- `os.execvpe` + list 参数防止 shell 注入
- `shlex.quote` 正确转义 shell value
- `tempfile + fsync + shutil.move` 原子写入模式
- `chmod 600` 应用于 `env.json` / `schema.json` / backup 文件
- Secret 值不记入操作日志（`set_secret` 不传 value）
- 模板展开 `max_depth=10` 防无限递归
- 自定义 regex 写入前先用 `re.compile` 校验

---

## 修复优先级

| 优先级 | 修复项 | 涉及文件 | 工作量 |
|--------|--------|----------|--------|
| **P0** | 修复文件锁竞态（对共享锁文件加锁） | `manager.py:117` | 0.5天 |
| **P0** | 消除 `except Exception: pass`（改 `OSError`） | `_history.py:46,100` | 0.5天 |
| **P1** | XOR → AES-256-GCM + 支持主密码 + 机器绑定警告 | `manager.py:450-565` | 2天 |
| **P1** | history 文件 chmod 600 + 不记 value | `manager.py:178`, `_history.py` | 0.5天 |
| **P1** | Schema 校验正则修复（IPv6, URL） | `_schema.py:20-35` | 0.5天 |
| **P2** | Shell export key 转义 + key 名校验 | `_io.py:160`, `_io.py:75-80` | 0.5天 |
| **P2** | Schema 损坏时显式警告 | `_schema.py:50-54` | 0.5天 |
| **P3** | 异常命名规范化、未使用 import 清理 | `exceptions.py`, `_schema.py` | 0.5天 |
| **P3** | v1 加密自动迁移到 v2 | `manager.py:524-539` | 0.5天 |

---

## 总结

| 严重度 | 数量 | 阻塞合并 |
|--------|------|----------|
| CRITICAL | 3 | 是 |
| HIGH | 7 | 建议 |
| MEDIUM | 8 | 否 |

**结论：不建议合并。** 并发写入竞态条件（#1）在正常多进程使用中可导致静默数据丢失；机器绑定加密（#2）是设计层面问题，需文档化警告；裸 `except Exception: pass`（#3）需立即修复。修复 #1 和 #3 后可达合并标准，#2 需至少加用户警告。
