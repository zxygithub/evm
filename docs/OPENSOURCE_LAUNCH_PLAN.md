# EVM 开源项目推广计划

**日期**: 2026-05-30 | **仓库**: github.com/zxygithub/evm

---

## 一、现状评估

| 维度 | 当前 | 开源标准 | 差距 |
|------|------|----------|------|
| 代码质量 | 98% 覆盖, ruff+mypy 双零 | ✅ 达标 | — |
| README | 708 行, 含 API/示例 | ✅ 达标 | — |
| API 文档 | API_REFERENCE.md (875行) | ✅ 达标 | — |
| 变更日志 | CHANGELOG.md | ✅ 达标 | — |
| 用户指南 | USER_GUIDE_CN.md (2,340行) | ⚠️ 仅中文 | 需英文版 |
| CI/CD | **无** | ❌ 缺失 | GitHub Actions |
| PyPI | **未发布** | ❌ 缺失 | 发布流水线 |
| 社区文件 | **0 个** | ❌ 缺失 | 见下方清单 |
| 官网 | 无 | ⚠️ 可选 | GitHub Pages |

---

## 二、必须完成的（发布前）

### 2.1 GitHub 社区健康文件

```
.github/
├── workflows/
│   ├── test.yml               # CI: py39-313 × ubuntu/macos
│   ├── lint.yml               # ruff + mypy
│   └── publish.yml            # CD: git tag → PyPI
├── ISSUE_TEMPLATE/
│   ├── bug_report.md
│   └── feature_request.md
└── pull_request_template.md

根目录文件:
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md          # 复用 Contributor Covenant
└── SECURITY.md
```

### 2.2 CI/CD 流水线

**test.yml** — 质量门禁矩阵：
- Python 3.9/3.10/3.11/3.12/3.13 × ubuntu-latest/macos-latest
- 运行: pytest + coverage + ruff + mypy

**publish.yml** — 自动发布：
- 触发: `git push --tags`
- 步骤: build → twine check → PyPI publish (Trusted Publisher OIDC)

### 2.3 PyPI 发布

1. 注册 [pypi.org](https://pypi.org) 账号
2. 配置 Trusted Publisher (GitHub → PyPI OIDC)
3. 首次手动发布验证：`python -m build && twine upload dist/*`

### 2.4 pyproject.toml 更新

```diff
- Development Status :: 4 - Beta
+ Development Status :: 5 - Production/Stable

+ Operating System :: MacOS
+ Operating System :: POSIX :: Linux
+ Programming Language :: Python :: 3 :: Only
+ Topic :: System :: Systems Administration
+ Topic :: Software Development :: Build Tools
```

### 2.5 LICENSE 年份

`2024` → `2024-2026`

---

## 三、发布前代码改动

| 改动 | 工作量 |
|------|--------|
| 英文 User Guide (`USER_GUIDE.md`) | 2h |
| 英文代码 docstring | 可选 1-2h |
| `--version` 输出确认简洁 | 已就绪 |

---

## 四、README 增强 — Badges

```markdown
[![PyPI](https://img.shields.io/pypi/v/evm-cli)](https://pypi.org/project/evm-cli/)
[![Tests](https://github.com/zxygithub/evm/actions/workflows/test.yml/badge.svg)](https://github.com/zxygithub/evm/actions)
[![Coverage](https://codecov.io/gh/zxygithub/evm/branch/main/graph/badge.svg)](https://codecov.io/gh/zxygithub/evm)
[![Python](https://img.shields.io/pypi/pyversions/evm-cli)](https://pypi.org/project/evm-cli/)
[![License](https://img.shields.io/github/license/zxygithub/evm)](LICENSE)
```

---

## 五、推广渠道（发布后）

| 阶段 | 渠道 | 说明 |
|------|------|------|
| 发布当天 | **GitHub Release** | Release Notes + 安装指令 |
| 第 1 周 | **Hacker News** Show HN | 侧重 Agent-friendly 差异化 |
| 第 1 周 | **Reddit** r/Python, r/devops | 交叉发布 |
| 第 1 周 | **Python Weekly** newsletter | 提交推荐 |
| 第 2 周 | **Dev.to / Medium** | 技术深度文章 |
| 持续 | **Twitter/X** | 版本发布通知 |

---

## 六、项目治理

| 项 | 建议 |
|---|------|
| 版本策略 | SemVer, `git tag vX.Y.Z` → 自动发布 |
| 贡献流程 | CONTRIBUTING.md 定义 fork → PR → review → merge |
| 行为准则 | Contributor Covenant (复用模板) |
| 安全报告 | SECURITY.md → 私密邮件报告 → 90天修复窗口 |
| 版本支持 | 仅支持最新版本 (明确声明) |
| 路线图 | GitHub Milestones + Roadmap issue |

---

## 七、发布检查清单

### 发布前

- [ ] GitHub Actions CI 全矩阵通过
- [ ] `.github/` 目录就绪
- [ ] `CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` / `SECURITY.md` 就绪
- [ ] PyPI 账号 + Trusted Publisher 配置
- [ ] `pyproject.toml` classifiers 更新
- [ ] `pip install evm-cli` 验证通过
- [ ] README badges 添加
- [ ] 英文 User Guide 完成
- [ ] GitHub Release Notes 撰写

### 发布当日

- [ ] `git tag v3.0.0 && git push --tags`
- [ ] 确认 PyPI 发布成功
- [ ] GitHub Release 发布
- [ ] HN / Reddit 发帖

### 发布后持续

- [ ] 48h 内首次回复 GitHub Issues
- [ ] 首个外部 PR 合并
- [ ] 收集反馈规划 v3.1

---

## 八、时间线

| 阶段 | 时间 | 关键产出 |
|------|------|----------|
| 基建搭建 | 第 1 周 | CI 通过 + 社区文件 + PyPI 可发布 |
| 文档完善 | 第 2 周 | 英文 Guide + badges + Release Notes |
| **正式发布** | **第 3 周** | **v3.0.0 + PyPI + GitHub Release + 推广** |
| 社区建设 | 第 4-8 周 | 响应 issue、接受 PR、收集反馈 |
