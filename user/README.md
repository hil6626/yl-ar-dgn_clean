# user

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

---

## 🔗 与其他模块的关系

### 直接调用
- **AR-backend** - 通过本地接口（HTTP 或 IPC）
- **api-map** - 加载接口定义 (`registry.json`)
- **scripts** - 执行脚本或获取状态

### 兼容集成
- 可嵌入 `YL-monitor` 页面
- 可通过 WebSocket 与后端实时交互

---

## 📂 目录结构

（待补充 - 根据实际目录结构更新）

```
user/
├── main.py          # 应用入口
├── controllers/     # 业务逻辑
├── gui/             # UI 组件
├── assets/          # 资源文件
└── manuals/         # 用户手册
```

---

## 📖 相关文档

- [项目总览](../README.md) - 系统架构
- [监控前端](../YL-monitor/README.md) - 浏览器版本
- [后端服务](../AR-backend/README.md) - API 接口

