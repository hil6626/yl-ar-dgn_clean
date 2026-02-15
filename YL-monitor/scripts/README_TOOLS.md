# 运维工具脚本 (Tools)

> 项目维护、部署与验证工具

## 脚本列表

| ID | 名称 | 文件 | 使用方式 |
|----|------|------|---------|
| TOOL-001 | 项目启动脚本 | `project_run.sh` | `bash scripts/project_run.sh` |
| TOOL-002 | Docker镜像构建 | `docker_build.sh` | `bash scripts/docker_build.sh` |
| TOOL-003 | Docker容器启动 | `docker_start.sh` | `bash scripts/docker_start.sh` |
| TOOL-004 | Docker容器停止 | `docker_stop.sh` | `bash scripts/docker_stop.sh` |
| TOOL-005 | 清理旧文件 | `cleanup_old_files.py` | `python3 scripts/cleanup_old_files.py` |
| TOOL-006 | 前端优化验证 | `verify_frontend_optimization.py` | `python3 scripts/verify_frontend_optimization.py` |
| TOOL-007 | 静态资源验证 | `verify_static_resources.sh` | `bash scripts/verify_static_resources.sh` |
| TOOL-008 | 部署验证 | `verify_deployment.py` | `python3 scripts/verify_deployment.py` |
| TOOL-009 | API功能测试 | `test_api_functionality.py` | `python3 scripts/test_api_functionality.py` |

## 快速使用

### Docker 运维

```bash
# 构建镜像
bash scripts/docker_build.sh

# 启动容器
bash scripts/docker_start.sh

# 停止容器
bash scripts/docker_stop.sh
```

### 项目启动

```bash
# 启动项目（自动检测环境）
bash scripts/project_run.sh
```

### 验证与测试

```bash
# 验证前端优化
python3 scripts/verify_frontend_optimization.py

# 验证静态资源
bash scripts/verify_static_resources.sh

# 验证部署
python3 scripts/verify_deployment.py

# API功能测试
python3 scripts/test_api_functionality.py
```

### 清理工具

```bash
# 清理旧文件
python3 scripts/cleanup_old_files.py
```

## 返回顶部

[返回 scripts 目录](../README.md)

