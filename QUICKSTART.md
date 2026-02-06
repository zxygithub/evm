# EVM 快速开始指南

## 5分钟快速上手

### 1. 安装

```bash
cd /Users/zhuangxiaoyi/Desktop/evm
pip install -e .
```

### 2. 基本使用

```bash
# 设置环境变量
evm set APP_NAME "我的应用"
evm set APP_VERSION "1.0.0"

# 查看所有环境变量
evm list

# 获取特定变量
evm get APP_NAME

# 搜索变量
evm search APP
```

### 3. 导出和导入

```bash
# 导出为.env文件
evm export --format env -o myenv.env

# 从.env文件导入
evm load myenv.env
```

### 4. 备份和恢复

```bash
# 创建备份
evm backup

# 恢复备份
evm restore ~/.evm/backup_20240106_120000.json
```

### 5. 执行命令

```bash
# 使用自定义环境变量执行命令
evm exec -- python script.py
evm exec -- npm start
```

## 常用命令速查

| 命令 | 说明 | 示例 |
|------|------|------|
| `set KEY value` | 设置变量 | `evm set API_KEY abc123` |
| `get KEY` | 获取变量 | `evm get API_KEY` |
| `delete KEY` | 删除变量 | `evm delete API_KEY` |
| `list [pattern]` | 列出变量 | `evm list API` |
| `clear` | 清空所有 | `evm clear` |
| `search pattern` | 搜索变量 | `evm search api` |
| `rename old new` | 重命名 | `evm rename OLD_KEY NEW` |
| `copy src dst` | 复制 | `evm copy SRC_KEY DST_KEY` |
| `export -f format` | 导出 | `evm export -f env` |
| `load file [opts]` | 导入 | `evm load config.env --group dev` |
| `backup` | 备份 | `evm backup` |
| `restore file` | 恢复 | `evm restore backup.json --merge` |
| `exec -- command` | 执行命令 | `evm exec -- python app.py` |
| **分组命令** | | |
| `groups` | 列出所有分组 | `evm groups` |
| `setg group key value` | 在分组中设置 | `evm setg dev DB_URL localhost` |
| `getg group key` | 从分组获取 | `evm getg dev DB_URL` |
| `deleteg group key` | 从分组删除 | `evm deleteg dev DEBUG` |
| `listg group` | 列出分组变量 | `evm listg dev` |
| `delete-group group` | 删除整个分组 | `evm delete-group dev` |
| `move-group key group` | 移动到分组 | `evm move-group API_KEY prod` |
| **list 选项** | | |
| `--group name` | 列出指定分组 | `evm list --group dev` |
| `--show-groups` | 按分组显示 | `evm list --show-groups` |
| **load 选项** | | |
| `--format type` | 强制格式 | `evm load file --format json` |
| `--replace` | 替换模式 | `evm load file --replace` |
| `--group name` | 导入到分组 | `evm load file --group dev` |

## 使用场景

### 场景1：开发环境配置
```bash
# 设置开发环境
evm set NODE_ENV development
evm set DATABASE_URL "postgresql://localhost/dev"
evm set DEBUG true

# 运行应用
evm exec -- npm start
```

### 场景2：团队协作
```bash
# 导出配置
evm export --format env -o team-env.env

# 分享给团队成员
# 团队成员导入配置
evm load team-env.env
```

### 场景3：生产部署
```bash
# 创建备份
evm backup

# 切换到生产配置
evm set NODE_ENV production
evm set API_URL https://api.example.com
evm set DEBUG false

# 导出为shell脚本
evm export --format sh -o production.sh

# 在服务器上加载
source production.sh
```

### 场景4：多项目切换
```bash
# 项目A配置
evm set PROJECT project_a
evm set API_URL http://project-a.local
evm backup --file project-a.json

# 切换到项目B
evm clear
evm set PROJECT project_b
evm set API_URL http://project-b.local

# 切换回项目A
evm restore project-a.json
```

## 使用Makefile快捷命令

```bash
# 查看所有可用命令
make help

# 安装
make install

# 运行测试
make test

# 运行演示
make demo

# 清理
make clean
```

## 获取帮助

```bash
# 查看主帮助
evm --help

# 查看特定命令的帮助
evm set --help
evm export --help
evm restore --help
```

## 存储位置

环境变量默认存储在：`~/.evm/env.json`

可以使用 `--env-file` 参数指定自定义位置：
```bash
evm --env-file /path/to/custom.json set KEY value
```

## 下一步

- 阅读 [README.md](README.md) 了解更多详细信息
- 查看 [examples/](examples/) 目录中的示例代码
- 运行 `make demo` 查看完整演示
- 运行 `make test` 了解测试用例

## 常见问题

**Q: 如何查看所有环境变量？**
```bash
evm list
```

**Q: 如何批量删除环境变量？**
```bash
evm clear  # 删除所有
# 或逐个删除
evm delete KEY1
evm delete KEY2
```

**Q: 如何在多个项目中使用不同的配置？**
```bash
# 使用不同的配置文件
evm --env-file ~/.evm/project1.json set KEY value
evm --env-file ~/.evm/project2.json set KEY value
```

**Q: 如何导出为shell脚本并在其他机器上使用？**
```bash
evm export --format sh -o export.sh
# 在其他机器上
source export.sh
```

**Q: 环境变量会持久化吗？**
是的，所有环境变量都存储在 `~/.evm/env.json` 文件中，重启后仍然有效。
