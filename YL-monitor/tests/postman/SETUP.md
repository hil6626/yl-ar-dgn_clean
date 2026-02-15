# YL-Monitor Postman 配置指南

本文档详细说明如何在 VSCode 中配置和使用 Postman 扩展来测试 YL-Monitor API。

## 📋 目录

1. [快速开始](#快速开始)
2. [配置文件说明](#配置文件说明)
3. [环境配置](#环境配置)
4. [使用步骤](#使用步骤)
5. [VSCode 集成](#vscode-集成)
6. [故障排除](#故障排除)

## 🚀 快速开始

### 1. 安装 Postman 扩展

在 VSCode 中安装 Postman 扩展：

```bash
# 方式 1: 通过 VSCode 扩展市场
Ctrl+Shift+P → Extensions: Install Extensions → 搜索 "Postman"

# 方式 2: 命令行
code --install-extension Postman.postman-for-vscode
```

### 2. 验证配置

运行验证脚本确保配置正确：

```bash
# 使用 VSCode 任务
Ctrl+Shift+P → Tasks: Run Task → YL-Monitor: 验证 Postman 配置

# 或手动运行
bash scripts/tools/verify_mcp_and_postman.sh
```

### 3. 导入集合

```bash
# 方式 1: 使用 VSCode 命令
Ctrl+Shift+P → YL-Monitor: 在 Postman 中打开集合

# 方式 2: 手动导入
1. 打开 Postman 扩展
2. 点击 Import → File
3. 选择 tests/postman/yl-monitor-collection.json
```

## 📁 配置文件说明

### 主要配置文件

| 文件 | 说明 | 用途 |
|------|------|------|
| `.vscode/postman.json` | Postman 扩展主配置 | 定义集合路径、环境、端点映射 |
| `.vscode/settings.json` | VSCode 工作区设置 | Postman 扩展的行为配置 |
| `.vscode/tasks.json` | VSCode 任务配置 | 自动化测试任务定义 |
| `tests/postman/yl-monitor-collection.json` | API 测试集合 | 所有 API 端点和测试脚本 |
| `tests/postman/environments/*.json` | 环境配置 | 不同环境的变量配置 |

### 配置结构

```
.vscode/
├── postman.json          # Postman 扩展配置
├── settings.json         # VSCode 设置
└── tasks.json            # 自动化任务

tests/postman/
├── yl-monitor-collection.json    # API 测试集合
├── environments/
│   ├── local.json              # 本地环境
│   ├── development.json        # 开发环境
│   └── production.json       # 生产环境
└── SETUP.md                    # 本说明文档
```

## 🌍 环境配置

### 环境变量说明

| 变量名 | 说明 | 默认值 | 用途 |
|--------|------|--------|------|
| `base_url` | 服务基础 URL | `http://localhost:5500` | API 请求地址 |
| `api_version` | API 版本 | `v1` | 版本控制 |
| `timeout` | 请求超时 | `30000` | 毫秒 |
| `auth_token` | 认证令牌 | `` | 身份验证 |
| `cpu_threshold` | CPU 阈值 | `80` | 监控告警 |
| `memory_threshold` | 内存阈值 | `90` | 监控告警 |
| `disk_threshold` | 磁盘阈值 | `85` | 监控告警 |
| `script_category` | 脚本类别 | `monitor` | 脚本分类 |
| `test_dag_id` | 测试 DAG ID | `example_dag` | DAG 测试 |
| `test_script_name` | 测试脚本名 | `01_cpu_usage_monitor.py` | 脚本测试 |
| `ar_scene` | AR 场景 | `test_scene` | AR 渲染 |
| `ar_resolution` | AR 分辨率 | `1920x1080` | AR 渲染 |

### 切换环境

```bash
# 在 Postman 扩展中
1. 打开 Postman 侧边栏
2. 点击环境下拉框
3. 选择目标环境（Local/Development/Production）
```

## 📝 使用步骤

### 1. 启动 YL-Monitor 服务

```bash
# 方式 1: 使用脚本
bash scripts/docker_start.sh

# 方式 2: 直接启动
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 5500
```

### 2. 运行 API 测试

```bash
# 方式 1: VSCode 任务
Ctrl+Shift+P → Tasks: Run Task → YL-Monitor: 运行 API 测试

# 方式 2: 使用 Newman（命令行）
newman run tests/postman/yl-monitor-collection.json \
  -e tests/postman/environments/local.json \
  --reporters cli,html \
  --reporter-html-export tests/postman/reports/report.html

# 方式 3: Postman 扩展 GUI
1. 打开 Postman 扩展
2. 选择 YL-Monitor API Collection
3. 点击 Run 按钮
```

### 3. 查看测试结果

- **控制台输出**: 实时显示在 VSCode 输出面板
- **HTML 报告**: `tests/postman/reports/report.html`
- **JSON 报告**: 在 `logs/verification-reports/` 目录

## 🔧 VSCode 集成

### 可用命令

| 命令 | 快捷键 | 说明 |
|------|--------|------|
| `YL-Monitor: 运行 API 测试` | - | 运行完整 API 测试集合 |
| `YL-Monitor: 在 Postman 中打开集合` | - | 在 Postman 扩展中打开集合 |
| `YL-Monitor: 启动服务并测试` | - | 启动服务并运行测试 |
| `YL-Monitor: 验证 Postman 配置` | - | 验证配置完整性 |

### 任务配置

在 `.vscode/tasks.json` 中定义了以下任务：

1. **运行 API 测试**: 使用 Newman 运行测试集合并生成 HTML 报告
2. **启动服务并测试**: 自动启动服务，等待 3 秒后运行测试
3. **验证 Postman 配置**: 验证所有配置文件的正确性
4. **生成 API 文档**: 从 FastAPI 应用生成 OpenAPI 规范

### 快捷键绑定（可选）

在 `.vscode/keybindings.json` 中添加：

```json
[
  {
    "key": "ctrl+shift+t",
    "command": "workbench.action.tasks.runTask",
    "args": "YL-Monitor: 运行 API 测试"
  },
  {
    "key": "ctrl+shift+p",
    "command": "ylMonitor.openPostman"
  }
]
```

## 🔍 API 端点列表

### 系统健康检查
- `GET /api/v1/dashboard/health` - 健康检查
- `GET /api/v1/dashboard/summary` - 系统摘要
- `GET /api/dashboard/summary` - 系统摘要 (Legacy)

### AR 模块
- `GET /api/v1/ar/status` - AR 状态
- `POST /api/v1/ar/trigger` - 触发 AR 任务
- `GET /api/v1/ar/nodes` - AR 节点列表

### DAG 模块
- `GET /api/v1/dag/status` - DAG 状态
- `POST /api/v1/dag/execute` - 执行 DAG
- `GET /api/v1/dag/list` - DAG 列表

### 脚本管理
- `GET /api/v1/scripts/status` - 脚本状态
- `POST /api/v1/scripts/execute` - 执行脚本
- `GET /api/v1/scripts/list` - 脚本列表

### API 元数据
- `GET /api/meta` - API 元数据
- `POST /api/functions/{func_id}/bubble_check` - 功能冒泡检测

### WebSocket
- `/ws/dag` - DAG 状态推送
- `/ws/ar` - AR 状态推送
- `/ws/scripts` - 脚本状态推送

## 🐛 故障排除

### 常见问题

#### 1. Postman 扩展无法加载集合

**症状**: 导入集合时出错或集合不显示

**解决方案**:
```bash
# 检查 JSON 格式
python3 -c "import json; json.load(open('tests/postman/yl-monitor-collection.json'))"

# 验证文件路径
ls -la tests/postman/yl-monitor-collection.json

# 重新导入集合
# 1. 删除 Postman 扩展中的旧集合
# 2. 重新导入 tests/postman/yl-monitor-collection.json
```

#### 2. API 请求返回 404

**症状**: 所有 API 请求返回 404 Not Found

**解决方案**:
```bash
# 检查服务是否运行
curl http://localhost:5500/api/v1/dashboard/health

# 检查端口配置
# 确认环境变量 base_url 正确设置

# 查看服务日志
docker logs yl-monitor  # 如果使用 Docker
# 或查看 logs/ 目录下的日志文件
```

#### 3. 环境变量未生效

**症状**: 请求使用错误的 URL 或参数

**解决方案**:
```bash
# 检查环境配置
cat tests/postman/environments/local.json

# 在 Postman 中确认环境已激活
# 查看 Postman 扩展右下角的环境指示器

# 重新加载环境
# 1. 切换环境到 "No Environment"
# 2. 再切换回目标环境
```

#### 4. Newman 测试失败

**症状**: 命令行运行 Newman 时出错

**解决方案**:
```bash
# 安装 Newman
npm install -g newman

# 验证安装
newman --version

# 运行测试时添加详细输出
newman run tests/postman/yl-monitor-collection.json \
  -e tests/postman/environments/local.json \
  --verbose

# 检查报告目录是否存在
mkdir -p tests/postman/reports
```

#### 5. VSCode 任务无法运行

**症状**: 运行任务时提示命令未找到

**解决方案**:
```bash
# 检查 Newman 是否安装
which newman

# 检查 Python 环境
which python3
python3 --version

# 验证脚本权限
chmod +x scripts/tools/verify_mcp_and_postman.sh

# 手动运行验证脚本
bash scripts/tools/verify_mcp_and_postman.sh
```

### 调试技巧

1. **查看详细日志**:
   ```bash
   # 在 VSCode 输出面板查看 Postman 扩展日志
   # 或查看 logs/ 目录下的日志文件
   tail -f logs/verification-reports/*.log
   ```

2. **测试单个端点**:
   ```bash
   curl -v http://localhost:5500/api/v1/dashboard/health
   ```

3. **验证 JSON 格式**:
   ```bash
   python3 -m json.tool tests/postman/yl-monitor-collection.json > /dev/null && echo "Valid JSON"
   ```

4. **检查端口占用**:
   ```bash
   netstat -tlnp | grep 5500
   ```

## 📚 相关文档

- [MCP 快速入门](../../MCP-QUICKSTART.md)
- [项目 README](../../README.md)
- [Postman 官方文档](https://learning.postman.com/docs/)
- [Newman 文档](https://learning.postman.com/docs/collections/using-newman-cli/)

## 🔄 更新和维护

### 添加新端点

1. 编辑 `tests/postman/yl-monitor-collection.json`
2. 在相应模块下添加新请求
3. 更新 `.vscode/postman.json` 中的端点映射
4. 运行验证脚本确保配置正确

### 更新环境变量

1. 编辑对应的环境文件（`local.json`, `development.json`, `production.json`）
2. 确保所有环境文件同步更新
3. 在 Postman 扩展中重新加载环境

### 版本控制

所有配置文件已纳入版本控制，提交时请包含：
- `.vscode/postman.json`
- `.vscode/settings.json`
- `.vscode/tasks.json`
- `tests/postman/yl-monitor-collection.json`
- `tests/postman/environments/*.json`

---

**最后更新**: 2024-01-01  
**版本**: v1.0.0  
**维护者**: YL-Monitor Team
