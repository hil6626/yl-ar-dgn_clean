# 前端测试

## 概述
本目录包含AR Live Studio前端界面和监控页面的测试。

## 测试结构
```
test_frontend/
├── __init__.py              # 测试包初始化
├── test_monitor_page.py    # 监控页面测试
├── test_websocket.py       # WebSocket通信测试
├── test_api_client.py      # API客户端测试
└── test_ui_components.py   # UI组件测试
```

## 运行测试

### 前提条件
确保监控服务正在运行：
```bash
cd /workspaces/AR
source env/bin/activate
python src/backend/monitor_app.py &
```

### 运行前端测试
```bash
cd /workspaces/AR
source env/bin/activate
python -m pytest test/test_frontend/ -v
```

### 端到端测试
```bash
# 使用Selenium进行E2E测试
python -m pytest test/test_frontend/test_e2e.py -v
```

## 测试工具
- **pytest**: 测试框架
- **selenium**: 浏览器自动化测试
- **requests**: HTTP请求测试
- **websocket-client**: WebSocket测试

## 安装测试依赖
```bash
pip install selenium webdriver-manager pytest-html
```

## 浏览器兼容性测试
测试在以下浏览器中进行：
- Chrome/Chromium
- Firefox
- Safari (macOS)

## 性能测试
- 页面加载时间测试
- WebSocket通信延迟测试
- 内存使用监控

## 注意事项
- 测试需要浏览器驱动程序
- 某些测试需要网络连接
- 监控服务必须先启动
