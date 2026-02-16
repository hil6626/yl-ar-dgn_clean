# 测试指南

**版本:** 1.0.0  
**最后更新:** 2026-02-16  
**适用范围:** YL-AR-DGN 项目所有测试活动

---

## 📋 目录

1. [测试策略](#测试策略)
2. [测试类型](#测试类型)
3. [测试环境搭建](#测试环境搭建)
4. [单元测试](#单元测试)
5. [集成测试](#集成测试)
6. [端到端测试](#端到端测试)
7. [性能测试](#性能测试)
8. [测试自动化](#测试自动化)

---

## 测试策略

### 测试金字塔

```
        /\
       /  \     端到端测试 (E2E) - 10%
      /----\    集成测试 (Integration) - 30%
     /------\   单元测试 (Unit) - 60%
    /________\
```

### 测试原则

1. **自动化优先**: 所有测试应可自动运行
2. **快速反馈**: 单元测试应在秒级完成
3. **独立隔离**: 测试之间不应相互依赖
4. **可重复**: 任何环境、任何时间都应得到相同结果
5. **全面覆盖**: 核心功能覆盖率 > 80%

---

## 测试类型

| 类型 | 目的 | 工具 | 频率 |
|------|------|------|------|
| **单元测试** | 验证单个函数/类 | pytest | 每次提交 |
| **集成测试** | 验证组件间交互 | pytest + Docker | 每日构建 |
| **端到端测试** | 验证完整业务流程 | Selenium/Playwright | 每周 |
| **性能测试** | 验证性能指标 | locust | 每月 |
| **安全测试** | 发现安全漏洞 | bandit, safety | 每次发布 |

---

## 测试环境搭建

### 安装测试依赖

```bash
# 基础测试工具
pip install pytest pytest-cov pytest-asyncio pytest-mock

# 代码覆盖率
pip install coverage codecov

# 性能测试
pip install locust

# 安全测试
pip install bandit safety

# 类型检查
pip install mypy
```

### 测试配置

创建 `pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
markers =
    unit: 单元测试
    integration: 集成测试
    e2e: 端到端测试
    slow: 慢速测试
```

---

## 单元测试

### 测试文件结构

```
tests/
├── unit/
│   ├── __init__.py
│   ├── conftest.py          # 共享fixture
│   ├── test_path_manager.py
│   ├── test_ar_backend_client.py
│   ├── test_settings.py
│   └── test_face_processor.py
```

### 编写单元测试

**示例: 测试 PathManager**

```python
# tests/unit/test_path_manager.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from user.core.path_manager import PathManager


class TestPathManager:
    """PathManager 单元测试"""
    
    @pytest.fixture
    def path_manager(self):
        """创建 PathManager 实例"""
        return PathManager()
    
    def test_find_project_root_success(self, path_manager):
        """测试成功查找项目根目录"""
        # 执行
        root = path_manager._find_project_root()
        
        # 验证
        assert root is not None
        assert isinstance(root, Path)
        assert (root / "README.md").exists()
    
    def test_find_project_root_from_deep_path(self, path_manager):
        """测试从深层目录查找项目根"""
        # 准备
        deep_path = Path("/home/user/project/deep/nested/path")
        
        # 执行
        with patch('pathlib.Path.exists') as mock_exists:
            # 模拟在深层路径找不到，在根路径找到
            def side_effect(path):
                return str(path).endswith("README.md")
            mock_exists.side_effect = side_effect
            
            root = path_manager._find_project_root()
        
        # 验证
        assert root is not None
    
    def test_setup_python_path(self, path_manager):
        """测试设置 Python 路径"""
        # 准备
        original_path = sys.path.copy()
        
        # 执行
        with patch('sys.path', original_path):
            path_manager.setup_python_path()
            
            # 验证
            assert any("AR-backend" in p for p in sys.path)
            assert any("core" in p for p in sys.path)
    
    def test_setup_paths_idempotent(self, path_manager):
        """测试重复设置路径不会重复添加"""
        # 执行两次
        path_manager.setup_python_path()
        path_count = len(sys.path)
        
        path_manager.setup_python_path()
        new_count = len(sys.path)
        
        # 验证路径没有重复添加
        assert new_count == path_count
    
    def test_get_project_root_cached(self, path_manager):
        """测试项目根目录缓存"""
        # 第一次调用
        root1 = path_manager.get_project_root()
        
        # 第二次调用（应使用缓存）
        root2 = path_manager.get_project_root()
        
        # 验证是同一个对象
        assert root1 is root2
```

### 使用 Mock

```python
# 测试 ARBackendClient
import pytest
from unittest.mock import patch, Mock
import requests

from user.services.ar_backend_client import ARBackendClient


class TestARBackendClient:
    """ARBackendClient 单元测试"""
    
    @pytest.fixture
    def client(self):
        return ARBackendClient(host="0.0.0.0", port=5501)
    
    @patch('requests.get')
    def test_health_check_success(self, mock_get, client):
        """测试健康检查成功"""
        # 准备 Mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "healthy",
            "timestamp": "2026-02-16T10:00:00"
        }
        mock_get.return_value = mock_response
        
        # 执行
        result = client.health_check()
        
        # 验证
        assert result["status"] == "healthy"
        mock_get.assert_called_once_with(
            "http://0.0.0.0:5501/health",
            timeout=5
        )
    
    @patch('requests.get')
    def test_health_check_timeout(self, mock_get, client):
        """测试健康检查超时"""
        # 准备 Mock
        mock_get.side_effect = requests.Timeout("Connection timed out")
        
        # 执行
        result = client.health_check()
        
        # 验证
        assert result["status"] == "unhealthy"
        assert "timeout" in result["error"].lower()
    
    @patch('socket.socket')
    def test_discover_port_found(self, mock_socket_class, client):
        """测试端口发现成功"""
        # 准备 Mock
        mock_socket = Mock()
        mock_socket.connect_ex.return_value = 0  # 端口开放
        mock_socket_class.return_value = mock_socket
        
        # 执行
        port = client._discover_port()
        
        # 验证
        assert port == 5501  # 默认端口
    
    @patch('socket.socket')
    def test_discover_port_not_found(self, mock_socket_class, client):
        """测试端口发现失败"""
        # 准备 Mock - 所有端口都关闭
        mock_socket = Mock()
        mock_socket.connect_ex.return_value = 1  # 端口关闭
        mock_socket_class.return_value = mock_socket
        
        # 执行
        port = client._discover_port()
        
        # 验证返回默认端口
        assert port == 5501
```

### 测试异常

```python
def test_load_config_file_not_found():
    """测试配置文件不存在时的异常"""
    from user.config.settings import UserGUIConfig
    
    with pytest.raises(FileNotFoundError):
        UserGUIConfig.load_from_file("non_existent_config.yaml")


def test_process_frame_invalid_input():
    """测试无效输入的处理"""
    from AR-backend.core.face_processor import FaceProcessor
    
    processor = FaceProcessor()
    
    with pytest.raises(ValueError) as exc_info:
        processor.process_frame(None)  # 无效输入
    
    assert "Invalid frame" in str(exc_info.value)
```

---

## 集成测试

### 测试环境

使用 Docker Compose 搭建测试环境:

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  yl-monitor-test:
    build: ./YL-monitor
    ports:
      - "5500:5500"
    environment:
      - ENV=test
    volumes:
      - ./test-data:/app/data

  ar-backend-test:
    build: ./AR-backend
    ports:
      - "5501:5501"
    depends_on:
      - yl-monitor-test

  user-gui-test:
    build: ./user
    ports:
      - "5502:5502"
    depends_on:
      - ar-backend-test
```

### 编写集成测试

```python
# tests/integration/test_monitor_integration.py
import pytest
import requests
import time


class TestMonitorIntegration:
    """监控集成测试"""
    
    BASE_URL = "http://0.0.0.0:5500"
    
    @pytest.fixture(scope="class", autouse=True)
    def wait_for_services(self):
        """等待服务启动"""
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.BASE_URL}/api/health")
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
        else:
            pytest.fail("服务启动超时")
    
    def test_health_check_integration(self):
        """测试健康检查集成"""
        response = requests.get(f"{self.BASE_URL}/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_monitor_ar_backend_integration(self):
        """测试监控 AR-backend 集成"""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/monitor/nodes/ar-backend"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "ar-backend"
        assert data["status"] in ["online", "offline"]
    
    def test_monitor_user_gui_integration(self):
        """测试监控 User GUI 集成"""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/monitor/nodes/user-gui"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user-gui"
    
    def test_dag_execution_integration(self):
        """测试 DAG 执行集成"""
        # 创建测试 DAG
        dag_config = {
            "name": "test-dag",
            "tasks": [
                {"id": "task1", "action": "health_check"},
                {"id": "task2", "action": "status_check", "depends_on": ["task1"]}
            ]
        }
        
        # 提交 DAG
        response = requests.post(
            f"{self.BASE_URL}/api/v1/monitor/dag/submit",
            json=dag_config
        )
        assert response.status_code == 200
        
        # 执行 DAG
        dag_id = response.json()["dag_id"]
        response = requests.post(
            f"{self.BASE_URL}/api/v1/monitor/dag/{dag_id}/execute"
        )
        assert response.status_code == 200
        
        # 等待完成
        time.sleep(2)
        
        # 检查结果
        response = requests.get(
            f"{self.BASE_URL}/api/v1/monitor/dag/{dag_id}/status"
        )
        data = response.json()
        assert data["status"] in ["completed", "failed"]
```

---

## 端到端测试

### 使用 Playwright

```python
# tests/e2e/test_full_workflow.py
import pytest
from playwright.sync_api import sync_playwright


class TestFullWorkflow:
    """完整工作流程端到端测试"""
    
    @pytest.fixture(scope="class")
    def browser(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            yield browser
            browser.close()
    
    def test_monitor_dashboard_loads(self, browser):
        """测试监控面板加载"""
        page = browser.new_page()
        
        # 访问监控面板
        page.goto("http://0.0.0.0:5500")
        
        # 验证页面标题
        assert "YL-Monitor" in page.title()
        
        # 验证关键元素存在
        assert page.locator(".dashboard-header").is_visible()
        assert page.locator(".node-status-panel").is_visible()
        
        page.close()
    
    def test_service_status_displayed(self, browser):
        """测试服务状态显示"""
        page = browser.new_page()
        page.goto("http://0.0.0.0:5500")
        
        # 等待数据加载
        page.wait_for_selector(".node-card", timeout=5000)
        
        # 验证所有服务状态显示
        nodes = page.locator(".node-card").all()
        assert len(nodes) >= 2  # 至少显示 AR-backend 和 User GUI
        
        # 验证状态指示器
        for node in nodes:
            status = node.locator(".status-indicator")
            assert status.is_visible()
        
        page.close()
    
    def test_gui_launch_from_monitor(self, browser):
        """测试从监控面板启动 GUI"""
        page = browser.new_page()
        page.goto("http://0.0.0.0:5500")
        
        # 点击启动 GUI 按钮
        page.click("text=启动 User GUI")
        
        # 验证弹窗或新页面
        # 注意：实际 GUI 是桌面应用，这里可能需要特殊处理
        
        page.close()
```

---

## 性能测试

### 使用 Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between


class MonitorUser(HttpUser):
    """监控服务性能测试用户"""
    
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        """健康检查 - 高频"""
        self.client.get("/api/health")
    
    @task(2)
    def get_status(self):
        """获取状态 - 中频"""
        self.client.get("/api/v1/monitor/ui/status")
    
    @task(1)
    def get_metrics(self):
        """获取指标 - 低频"""
        self.client.get("/api/v1/monitor/api/metrics")


class BackendUser(HttpUser):
    """后端服务性能测试用户"""
    
    host = "http://0.0.0.0:5501"
    wait_time = between(2, 5)
    
    @task(2)
    def health_check(self):
        self.client.get("/health")
    
    @task(1)
    def get_status(self):
        self.client.get("/status")
```

运行性能测试:
```bash
locust -f tests/performance/locustfile.py --host=http://0.0.0.0:5500
```

---

## 测试自动化

### GitHub Actions 工作流

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r test-requirements.txt
    
    - name: Run unit tests
      run: |
        pytest tests/unit -v --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker
      uses: docker/setup-buildx-action@v2
    
    - name: Start services
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 30  # 等待服务启动
    
    - name: Run integration tests
      run: |
        pytest tests/integration -v
    
    - name: Cleanup
      run: |
        docker-compose -f docker-compose.test.yml down

  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run bandit
      run: |
        pip install bandit
        bandit -r . -f json -o bandit-report.json || true
    
    - name: Run safety
      run: |
        pip install safety
        safety check
```

---

## 测试报告

### 生成测试报告

```bash
# 运行测试并生成报告
pytest --html=report.html --self-contained-html

# 生成覆盖率报告
pytest --cov=. --cov-report=html:htmlcov
open htmlcov/index.html

# 生成 Allure 报告
pytest --alluredir=./allure-results
allure serve ./allure-results
```

### 测试报告内容

| 指标 | 目标 | 说明 |
|------|------|------|
| **测试通过率** | > 95% | 所有测试通过的比例 |
| **代码覆盖率** | > 80% | 被测试覆盖的代码比例 |
| **缺陷密度** | < 0.1/千行 | 每千行代码的缺陷数 |
| **平均修复时间** | < 4小时 | 从发现到修复的平均时间 |

---

## 最佳实践

### DO ✅

- 为每个功能编写对应的测试
- 使用有意义的测试名称
- 保持测试简单、独立、快速
- 使用 fixture 共享测试数据
- 定期运行测试套件

### DON'T ❌

- 不要编写相互依赖的测试
- 不要在测试中使用 sleep
- 不要测试第三方库的功能
- 不要忽略测试失败
- 不要在生产环境运行测试

---

## 参考资源

- [pytest 官方文档](https://docs.pytest.org/)
- [Python 测试最佳实践](https://testing.googleblog.com/)
- [测试金字塔](https://martinfowler.com/articles/practical-test-pyramid.html)

---

**最后更新:** 2026-02-16  
**维护者:** YL-AR-DGN 项目团队
