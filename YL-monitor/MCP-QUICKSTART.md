# YL-Monitor MCP Server 快速入门

## 🚀 5 分钟快速开始

### 1. 验证安装 (30 秒)

```bash
bash scripts/tools/verify_mcp_server.sh
```

预期输出：
```
✓ Node.js 版本: v18.x.x
✓ MCP Server 脚本存在
✓ MCP 配置 JSON 格式正确
✓ list_files 成功
✓ read_file 成功
✓ search 成功
✓ YL-Monitor 服务运行中
```

### 2. 在 VS Code 中使用 (1 分钟)

打开命令面板 (`Ctrl+Shift+P`)，输入：

| 命令 | 功能 |
|------|------|
| `YL-Monitor: 启动` | 启动 YL-Monitor 服务 |
| `YL-Monitor: 停止` | 停止服务 |
| `YL-Monitor: 运行 API 测试` | 执行 Postman 集合测试 |
| `YL-Monitor: 在 Postman 中打开集合` | 打开 Postman 并导入集合 |
| `MCP: 列出文件` | 列出项目文件 |
| `MCP: 搜索代码` | 在项目中搜索代码 |

### 3. 手动测试 MCP (2 分钟)

```bash
# 进入项目目录
cd /home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean/YL-monitor

# 测试列出文件
echo '{"command": "list_files", "args": {"path": "app"}, "id": 1}' | \
  node .vscode/mcp-server.js $(pwd)

# 测试读取文件
echo '{"command": "read_file", "args": {"path": "app/main.py"}, "id": 2}' | \
  node .vscode/mcp-server.js $(pwd)

# 测试搜索代码
echo '{"command": "search", "args": {"pattern": "def.*health", "path": "app"}, "id": 3}' | \
  node .vscode/mcp-server.js $(pwd)

# 测试 API 请求
echo '{"command": "api_request", "args": {"method": "GET", "endpoint": "/api/health"}, "id": 4}' | \
  node .vscode/mcp-server.js $(pwd)
```

### 4. 导入 Postman 集合 (1 分钟)

**方式一：VS Code 命令**
```
Ctrl+Shift+P → YL-Monitor: 在 Postman 中打开集合
```

**方式二：手动导入**
1. 打开 Postman
2. 点击 `Import` → `File`
3. 选择 `tests/postman/yl-monitor-collection.json`

## 📁 文件结构

```
.vscode/
├── mcp.json              # MCP 配置文件
├── mcp-server.js         # MCP Server 实现
└── README.md             # 详细文档

tests/postman/
├── yl-monitor-collection.json    # API 测试集合
├── environments/
│   └── local.json                # 本地环境配置
└── README.md                     # Postman 使用指南

scripts/tools/
└── verify_mcp_server.sh  # 验证脚本

部署/Tasks/
└── TASK-082-MCP-POSTMAN-INTEGRATION.md  # 部署文档
```

## 🔧 核心功能

### MCP 工具 (9 个)

| 工具 | 用途 | 示例 |
|------|------|------|
| `list_files` | 列出目录 | `{"path": "app", "recursive": true}` |
| `read_file` | 读取文件 | `{"path": "app/main.py"}` |
| `search` | 搜索代码 | `{"pattern": "def.*health", "path": "app"}` |
| `get_file_stats` | 文件信息 | `{"path": "app/main.py"}` |
| `api_request` | API 调用 | `{"method": "GET", "endpoint": "/api/health"}` |
| `run_monitor_script` | 执行脚本 | `{"script": "01_cpu_usage_monitor.py"}` |
| `get_api_collection` | 获取集合 | `{"collection": "yl-monitor-collection"}` |
| `watch_file_changes` | 监控文件 | `{"path": "app"}` |
| `run_shell_command` | 执行命令 | `{"command": "ls -la"}` |

### API 端点 (14+)

- `GET /api/health` - 健康检查
- `GET /api/v1/ar/status` - AR 状态
- `POST /api/v1/ar/trigger` - 触发 AR 任务
- `GET /api/v1/dag/status` - DAG 状态
- `POST /api/v1/dag/execute` - 执行 DAG
- `GET /api/v1/scripts/list` - 脚本列表
- `POST /api/v1/scripts/execute` - 执行脚本
- `GET /api/v1/dashboard/metrics` - 仪表板指标

## 🔒 安全特性

- ✅ 路径白名单（仅项目目录）
- ✅ 命令白名单（禁止危险命令）
- ✅ 文件大小限制（10MB）
- ✅ 路径遍历防护
- ✅ 自动批准安全操作

## 🐛 故障排除

### MCP Server 无法启动

```bash
# 检查 Node.js
node --version  # 需要 v14+

# 手动启动查看错误
node .vscode/mcp-server.js $(pwd)
```

### 文件访问被拒绝

- 确保路径在项目目录内
- 使用相对路径（如 `app/main.py`）
- 检查 `.vscode/mcp.json` 中的 `security.allowedPaths`

### API 请求失败

```bash
# 检查服务状态
curl http://localhost:5500/api/health

# 检查端口配置
cat .vscode/mcp.json | grep YL_MONITOR_PORT
```

## 📚 相关文档

- [MCP 详细文档](.vscode/README.md) - 完整使用指南
- [Postman 使用指南](tests/postman/README.md) - API 测试文档
- [部署总结](部署/Tasks/TASK-082-MCP-POSTMAN-INTEGRATION.md) - 技术细节

## 🎯 下一步

1. **探索 MCP 功能**: 尝试不同的命令和参数
2. **运行 API 测试**: 使用 Postman 集合测试所有端点
3. **自定义配置**: 根据需要修改 `.vscode/mcp.json`
4. **集成到工作流**: 将 MCP 工具融入日常开发

---

**部署状态**: ✅ 生产就绪  
**版本**: 1.0.6  
**最后更新**: 2025-02-08
