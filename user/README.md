# user

**版本:** 2.2.0  
**最后更新:** 2026-02-16  
**部署状态:** 阶段1&2已完成 - 监控服务运行中 (端口5502)

本地桌面 GUI 应用，提供系统交互与控制面板。

---

## 🚀 快速启动

```bash
# 进入目录
cd user

# 安装依赖（首次）
pip install -r requirements.txt  # 如果存在

# 启动应用
python3 main.py

# 启动监控服务（供YL-monitor监控）
python3 start_monitor_service.py
```

---

## 🎯 功能定位

`user` 提供本地桌面 GUI，与 `YL-monitor` 互补：

| 特性 | user（桌面） | YL-monitor（浏览器） |
|------|--------------|---------------------|
| 启动方式 | 双击执行 | 打开 HTML |
| 界面框架 | PyQt/Tkinter | HTML/JavaScript |
| 交互方式 | 原生 GUI 控件 | 网页界面 |
| 离线使用 | 支持 | 需要浏览器 |
| 监控服务 | 端口5502 | 端口5500 |

---

## 🔗 与其他模块的关系

### 直接调用
- **AR-backend** - 通过本地接口（HTTP 或 IPC）
- **api-map** - 加载接口定义 (`registry.json`)
- **scripts** - 执行脚本或获取状态

### 监控集成
- **YL-monitor** - 通过HTTP端点上报状态 (端口5502)
- 健康检查: `GET /health`
- 状态查询: `GET /status`
- 统计信息: `GET /stats`

### 兼容集成
- 可嵌入 `YL-monitor` 页面
- 可通过 WebSocket 与后端实时交互

---

## 📂 目录结构

```
user/
├── main.py                    # 应用入口
├── start_monitor_service.py   # 监控服务启动脚本
├── start.py                   # 启动脚本
├── start.sh                   # Shell启动脚本
├── test_backend_api.py        # 后端API测试
├── test_gui_audio.py          # GUI音频测试
├── test_gui_video.py          # GUI视频测试
├── controllers/               # 业务逻辑
├── gui/                       # UI 组件
│   └── gui.py                 # 主GUI界面
├── services/                  # 服务层
│   ├── status_reporter.py     # 状态上报
│   └── local_http_server.py   # 本地HTTP服务
├── config/                    # 配置文件
├── assets/                    # 资源文件
├── manuals/                   # 用户手册
├── utils/                     # 工具函数
└── logs/                      # 日志目录
```

---

## 📖 相关文档

- [项目总览](../README.md) - 系统架构
- [监控前端](../YL-monitor/README.md) - 浏览器版本
- [后端服务](../AR-backend/README.md) - API 接口
- [部署任务跟踪](../部署/TODO_DEPLOY.md) - 部署进度
- [阶段1完成报告](../部署/阶段1-监控整合-完成报告.md) - 监控整合详情

---

## 🔍 部署状态

### 当前状态
- **阶段1 (监控整合)**: ✅ 已完成 (2026-02-16)
  - 监控服务运行中: 端口5502
  - 健康检查端点: `/health`
  - 状态查询端点: `/status`
  - 统计信息端点: `/stats`
- **阶段2 (User GUI优化)**: ✅ 已完成 (2026-02-16)
  - main.py入口已创建
  - 路径管理器已创建 (user/core/path_manager.py)
  - 服务客户端已创建 (user/services/ar_backend_client.py)
  - 配置管理器已创建 (user/config/settings.py)
  - 所有功能可用

### 下一阶段
- **阶段3 (规则架构部署)**: 🟡 进行中 (60%)
  - 完善L1-L5规则文件
  - 规则引擎增强

---

## 📝 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 2.2.0 | 2026-02-16 | 更新阶段2完成状态，添加核心模块文档 |
| 2.1.0 | 2026-02-16 | 添加监控服务文档，更新部署状态 |
| 2.0.0 | 2026-02-09 | 初始版本 |

---

**文档版本:** 2.2.0  
**最后更新:** 2026-02-16  
**维护者:** AI 编程代理  
**部署状态:** 阶段1&2已完成，监控服务运行中
