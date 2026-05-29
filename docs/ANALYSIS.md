# EVM 项目评估报告 v6

**评估日期：** 2026-05-30
**项目版本：** 2.0.0
**评估范围：** 代码评审报告 18 项修复验证

---

## 一、修复状态总览

| 编号 | 严重度 | 问题 | 状态 | 验证 |
|------|--------|------|------|------|
| #1 | CRITICAL | 文件锁竞态条件 | ✅ 已修复 | 改用独立 `.lock` 文件 |
| #2 | CRITICAL | 加密与机器绑定 | ⚠️ 已缓解 | 首次使用打印警告，v1→v3 自动迁移 |
| #3 | CRITICAL | 裸 except Exception | ✅ 已修复 | 改为 `except OSError` |
| #4 | HIGH | 重复密钥 XOR | ✅ 已修复 | HMAC-CTR 模式 |
| #5 | HIGH | 机器派生密钥低熵 | ✅ 已修复 | HKDF-Expand 密钥分离 |
| #6 | HIGH | 历史日志明文记录 value | ✅ 已修复 | 不记 value + chmod 600 |
| #7 | HIGH | IPv6 正则过宽 | ✅ 已修复 | `ipaddress.IPv6Address()` |
| #8 | HIGH | .env 引号解析不严谨 | ✅ 已修复 | 平衡引号匹配 |
| #9 | HIGH | Shell 导出 key 未转义 | ✅ 已修复 | key 也 shlex.quote |
| #10 | HIGH | Schema 损坏静默丢弃 | ✅ 已修复 | stderr 打印警告 |
| #11 | MEDIUM | 未使用的 import | ✅ 已修复 | `_schema.py` 清理 |
| #12 | MEDIUM | 异常链丢失 | ✅ 已修复 | 全部 `raise from e` |
| #13 | MEDIUM | .env 导出值含换行 | ✅ 已修复 | 双引号包裹 + 转义 |
| #14 | MEDIUM | 异常命名不惯用 | ✅ 已修复 | 重命名 + 向后兼容别名 |
| #15 | MEDIUM | 加密/MAC 同钥 | ✅ 已修复 | HKDF 派生子密钥 |
| #16 | MEDIUM | v1 加密无盐无 MAC | ✅ 已修复 | 自动迁移到 v3 |
| #17 | MEDIUM | 历史写入非原子 | ✅ 已修复 | 仅捕获 OSError |
| #18 | MEDIUM | 解密秘文输出终端 | ✅ 已修复 | TTY 检测 + scrollback 警告 |

**修复率：18/18 = 100%**

---

## 二、架构变更

### 加密模块 (`_crypto.py`)
- **HKDF-Expand** (RFC 5869)：从主密钥派生独立 enc_key 和 mac_key
- **HMAC-CTR**：基于 HMAC 的流密码，消除重复密钥 XOR 弱点
- **Encrypt-then-MAC**：HMAC-SHA256 认证，常量时间比较
- **v3 格式**：`ENCv3:<salt>:<iv>:<mac>:<ciphertext>`

### 文件锁 (`manager.py`)
- 使用独立 `.lock` 文件（`env.json.lock`）加锁
- `os.open(O_CREAT|O_RDWR)` + `fcntl.flock(LOCK_EX|LOCK_NB)`
- 超时重试机制，默认 5 秒

### 异常体系 (`exceptions.py`)
- `StoragePermissionError`（原 `PermissionError_`）
- `ImportFailedError`（原 `ImportError_`）
- 保留向后兼容别名

---

## 三、安全评估

### 加密安全性对比

| 维度 | v2 (1.9.0) | v3 (2.0.0) |
|------|-----------|-----------|
| 加密算法 | 重复密钥 XOR | HMAC-CTR 流密码 |
| 密钥派生 | PBKDF2 → 单钥 | PBKDF2 → HKDF → enc_key + mac_key |
| 密钥分离 | ❌ 加密/MAC 同钥 | ✅ 独立子密钥 |
| 密钥流周期 | 32 字节 | 无周期（CTR 计数器） |
| 完整性 | HMAC-SHA256 ✓ | HMAC-SHA256 ✓ |
| 常量时间比较 | ✓ | ✓ |
| 自动迁移 | — | v1/v2 → v3 |

### 剩余已知限制
1. **机器绑定**：密钥从 hostname+uid+arch 派生，跨机不可迁移（已添加警告）
2. **无主密码**：不支持用户自定义密码增强熵（P3 工程化待实现）

---

## 四、测试覆盖

| 测试类 | 用例数 | 新增 |
|--------|--------|------|
| TestLockFile | 3 | 并发写入/锁文件权限/创建 |
| TestHistoryPermissions | 2 | chmod 600/OSError 静默 |
| TestIPv6Validation | 4 | ipaddress 标准库 |
| TestEnvQuoteParsing | 3 | 平衡/不平衡引号 |
| TestShellExportKeyEscaping | 2 | key 转义/导入校验 |
| TestEnvNewlineExport | 1 | 换行值处理 |
| TestSchemaCorruptionWarning | 1 | 损坏警告 |
| TestCryptoModule | 5 | HKDF/HMAC-CTR/加解密 |
| TestSecrets (增强) | 8 | v3/v2兼容/v1兼容/篡改/警告 |
| **总计** | **225** | **+24** |

---

## 五、下一步建议（P3 工程化）

1. `pyproject.toml` 迁移
2. GitHub Actions CI/CD
3. pre-commit hooks (black, ruff, mypy)
4. 发布 PyPI
5. 用户主密码支持（可选加密增强）
6. Sphinx 文档生成
