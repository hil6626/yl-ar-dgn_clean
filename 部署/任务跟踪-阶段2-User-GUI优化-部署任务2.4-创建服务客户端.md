# 阶段2 - 任务2.4: 创建服务客户端 - 详细部署文档

**任务ID:** 2.4  
**任务名称:** 创建服务客户端  
**优先级:** P1（重要）  
**预计工时:** 4小时  
**状态:** 待执行  
**前置依赖:** 任务2.3完成（GUI导入已修复）

---

## 一、任务目标

创建AR-backend服务客户端，实现服务发现、API调用封装、健康检查和重试机制。

## 二、部署内容

### 2.1 创建文件清单

| 序号 | 文件路径 | 操作类型 | 说明 |
|------|----------|----------|------|
| 1 | `user/services/ar_backend_client.py` | 新建 | AR-backend服务客户端 |
| 2 | `user/services/service_discovery.py` | 新建 | 服务发现模块 |
| 3 | `user/services/api_client.py` | 新建 | API客户端基类 |
| 4 | `user/config/services.yaml` | 新建 | 服务配置 |

### 2.2 详细代码实现

#### 文件1: user/services/ar_backend_client.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR-backend服务客户端
封装与AR-backend的所有交互
"""

import requests
import time
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger('ARBackendClient')


class ServiceStatus(Enum):
    """服务状态"""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    url: str
    status: ServiceStatus
    last_check: float
    version: Optional[str] = None
    latency_ms: Optional[float] = None
    error_count: int = 0


class ARBackendClient:
    """
    AR-backend服务客户端
    """
    
    DEFAULT_TIMEOUT = 5
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    
    def __init__(
        self,
        base_url: str = "http://localhost:5501",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # 服务信息
        self.service_info = ServiceInfo(
            name="ar-backend",
            url=self.base_url,
            status=ServiceStatus.UNKNOWN,
            last_check=0
        )
        
        # 回调函数
        self.on_status_change: Optional[Callable[[ServiceStatus], None]] = None
        
        logger.info(f"ARBackendClient initialized: {base_url}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Optional[requests.Response]:
        """
        执行HTTP请求（带重试）
        """
        url = f"{self.base_url}{endpoint}"
        
        # 设置默认超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                response = self.session.request(method, url, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # 更新服务信息
                self.service_info.latency_ms = latency
                self.service_info.last_check = time.time()
                
                if response.status_code < 500:
                    self.service_info.error_count = 0
                    if self.service_info.status != ServiceStatus.HEALTHY:
                        self._update_status(ServiceStatus.HEALTHY)
                else:
                    self.service_info.error_count += 1
                    if self.service_info.error_count > 2:
                        self._update_status(ServiceStatus.DEGRADED)
                
                return response
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
                self.service_info.error_count += 1
                if attempt < self.max_retries - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    self._update_status(ServiceStatus.OFFLINE)
                    raise
            
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.RETRY_DELAY)
                else:
                    self._update_status(ServiceStatus.DEGRADED)
                    raise
            
            except Exception as e:
                logger.error(f"Request error: {e}")
                raise
    
    def _update_status(self, new_status: ServiceStatus):
        """更新服务状态"""
        old_status = self.service_info.status
        if old_status != new_status:
            self.service_info.status = new_status
            logger.info(f"Service status changed: {old_status.value} -> {new_status.value}")
            
            if self.on_status_change:
                try:
                    self.on_status_change(new_status)
                except Exception as e:
                    logger.error(f"Status change callback error: {e}")
    
    # ==================== 健康检查 API ====================
    
    def health_check(self) -> bool:
        """
        健康检查
        """
        try:
            response = self._make_request('GET', '/health')
            if response and response.status_code == 200:
                data = response.json()
                self.service_info.version = data.get('version')
                return True
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    # ==================== 状态 API ====================
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        获取服务状态
        """
        try:
            response = self._make_request('GET', '/status')
            if response and response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Get status failed: {e}")
            return None
    
    # ==================== 指标 API ====================
    
    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """
        获取系统指标
        """
        try:
            response = self._make_request('GET', '/metrics')
            if response and response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Get metrics failed: {e}")
            return None
    
    # ==================== 摄像头控制 API ====================
    
    def start_camera(self, device_id: int = 0) -> bool:
        """
        启动摄像头
        """
        try:
            response = self._make_request(
                'POST',
                '/camera/start',
                json={'device_id': device_id}
            )
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Start camera failed: {e}")
            return False
    
    def stop_camera(self) -> bool:
        """
        停止摄像头
        """
        try:
            response = self._make_request('POST', '/camera/stop')
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Stop camera failed: {e}")
            return False
    
    def get_camera_status(self) -> Optional[Dict[str, Any]]:
        """
        获取摄像头状态
        """
        try:
            response = self._make_request('GET', '/camera/status')
            if response and response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Get camera status failed: {e}")
            return None
    
    # ==================== 音频控制 API ====================
    
    def start_audio(self) -> bool:
        """
        启动音频
        """
        try:
            response = self._make_request('POST', '/audio/start')
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Start audio failed: {e}")
            return False
    
    def stop_audio(self) -> bool:
        """
        停止音频
        """
        try:
            response = self._make_request('POST', '/audio/stop')
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Stop audio failed: {e}")
            return False
    
    def set_audio_effect(self, effect_type: str, params: Dict[str, Any]) -> bool:
        """
        设置音频效果
        """
        try:
            response = self._make_request(
                'POST',
                '/audio/effect',
                json={'type': effect_type, 'params': params}
            )
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Set audio effect failed: {e}")
            return False
    
    # ==================== 人脸合成 API ====================
    
    def load_face_model(self, model_path: str) -> bool:
        """
        加载人脸模型
        """
        try:
            response = self._make_request(
                'POST',
                '/face/load',
                json={'model_path': model_path}
            )
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Load face model failed: {e}")
            return False
    
    def start_face_swap(self) -> bool:
        """
        启动人脸合成
        """
        try:
            response = self._make_request('POST', '/face/start')
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Start face swap failed: {e}")
            return False
    
    def stop_face_swap(self) -> bool:
        """
        停止人脸合成
        """
        try:
            response = self._make_request('POST', '/face/stop')
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Stop face swap failed: {e}")
            return False
    
    # ==================== 监控上报 API ====================
    
    def report_status(self, status_data: Dict[str, Any]) -> bool:
        """
        上报状态到AR-backend
        """
        try:
            response = self._make_request(
                'POST',
                '/monitor/report',
                json=status_data
            )
            return response is not None and response.status_code == 200
        except Exception as e:
            logger.error(f"Report status failed: {e}")
            return False
    
    # ==================== 工具方法 ====================
    
    def is_available(self) -> bool:
        """
        检查服务是否可用
        """
        return self.service_info.status in [
            ServiceStatus.HEALTHY,
            ServiceStatus.DEGRADED
        ]
    
    def get_service_info(self) -> ServiceInfo:
        """
        获取服务信息
        """
        return self.service_info
    
    def close(self):
        """
        关闭客户端
        """
        self.session.close()
        logger.info("ARBackendClient closed")


# 全局实例
_client: Optional[ARBackendClient] = None

def get_client(
    base_url: str = "http://localhost:5501",
    **kwargs
) -> ARBackendClient:
    """
    获取ARBackendClient实例（单例）
    """
    global _client
    if _client is None:
        _client = ARBackendClient(base_url, **kwargs)
    return _client


def reset_client():
    """
    重置客户端实例
    """
    global _client
    if _client:
        _client.close()
    _client = None
```

#### 文件2: user/services/service_discovery.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务发现模块
自动发现项目中的服务
"""

import os
import socket
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger('ServiceDiscovery')


@dataclass
class DiscoveredService:
    """发现的服务"""
    name: str
    host: str
    port: int
    url: str
    healthy: bool
    metadata: Dict


class ServiceDiscovery:
    """
    服务发现
    """
    
    # 默认服务端口
    DEFAULT_PORTS = {
        'yl-monitor': 5500,
        'ar-backend': 5501,
        'user-gui': 5502,
    }
    
    def __init__(self):
        self.discovered_services: Dict[str, DiscoveredService] = {}
    
    def discover_local_services(self) -> List[DiscoveredService]:
        """
        发现本地服务
        """
        services = []
        
        for name, port in self.DEFAULT_PORTS.items():
            service = self._check_service(name, 'localhost', port)
            if service:
                services.append(service)
                self.discovered_services[name] = service
        
        return services
    
    def _check_service(
        self,
        name: str,
        host: str,
        port: int
    ) -> Optional[DiscoveredService]:
        """
        检查服务是否可用
        """
        try:
            # 尝试连接端口
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                # 端口开放，进一步检查健康端点
                url = f"http://{host}:{port}"
                healthy = self._check_health(url, name)
                
                return DiscoveredService(
                    name=name,
                    host=host,
                    port=port,
                    url=url,
                    healthy=healthy,
                    metadata={}
                )
            
            return None
            
        except Exception as e:
            logger.debug(f"Service check failed for {name}: {e}")
            return None
    
    def _check_health(self, base_url: str, service_name: str) -> bool:
        """
        检查服务健康状态
        """
        import requests
        
        # 不同服务的健康端点
        health_endpoints = {
            'yl-monitor': '/api/health',
            'ar-backend': '/health',
            'user-gui': '/health',
        }
        
        endpoint = health_endpoints.get(service_name, '/health')
        
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                timeout=3
            )
            return response.status_code == 200
        except:
            return False
    
    def find_service(self, name: str) -> Optional[DiscoveredService]:
        """
        查找特定服务
        """
        # 先检查已发现的服务
        if name in self.discovered_services:
            service = self.discovered_services[name]
            # 验证是否仍然健康
            if self._check_health(service.url, name):
                return service
        
        # 重新发现
        port = self.DEFAULT_PORTS.get(name)
        if port:
            service = self._check_service(name, 'localhost', port)
            if service:
                self.discovered_services[name] = service
                return service
        
        return None
    
    def get_service_url(self, name: str) -> Optional[str]:
        """
        获取服务URL
        """
        service = self.find_service(name)
        return service.url if service else None
    
    def get_all_healthy_services(self) -> List[DiscoveredService]:
        """
        获取所有健康的服务
        """
        healthy = []
        
        for name in self.DEFAULT_PORTS.keys():
            service = self.find_service(name)
            if service and service.healthy:
                healthy.append(service)
        
        return healthy


# 便捷函数
def discover_services() -> List[DiscoveredService]:
    """发现所有本地服务"""
    discovery = ServiceDiscovery()
    return discovery.discover_local_services()


def get_service_url(name: str) -> Optional[str]:
    """获取服务URL"""
    discovery = ServiceDiscovery()
    return discovery.get_service_url(name)
```

#### 文件3: user/services/api_client.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API客户端基类
提供通用的API客户端功能
"""

import requests
import json
import logging
from typing import Optional, Dict, Any, Callable
from abc import ABC, abstractmethod

logger = logging.getLogger('APIClient')


class APIError(Exception):
    """API错误"""
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class APIClient(ABC):
    """
    API客户端基类
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 5,
        api_key: Optional[str] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.api_key = api_key
        self.session = requests.Session()
        
        # 设置默认头
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'AR-User-GUI/2.0'
        })
        
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
        
        # 响应处理器
        self.response_handlers: Dict[int, Callable] = {}
        
        logger.info(f"APIClient initialized: {base_url}")
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """
        执行请求
        """
        url = f"{self.base_url}{endpoint}"
        
        # 设置超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # 调用状态码处理器
            if response.status_code in self.response_handlers:
                self.response_handlers[response.status_code](response)
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIError(f"Request failed: {e}")
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET请求"""
        return self._request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """POST请求"""
        return self._request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """PUT请求"""
        return self._request('PUT', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE请求"""
        return self._request('DELETE', endpoint, **kwargs)
    
    def get_json(self, endpoint: str, **kwargs) -> Optional[Dict]:
        """
        GET请求并解析JSON
        """
        response = self.get(endpoint, **kwargs)
        
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return None
        
        return None
    
    def post_json(
        self,
        endpoint: str,
        data: Dict,
        **kwargs
    ) -> Tuple[bool, Optional[Dict]]:
        """
        POST JSON数据
        """
        kwargs['json'] = data
        response = self.post(endpoint, **kwargs)
        
        success = response.status_code in [200, 201]
        
        try:
            result = response.json() if response.text else None
        except:
            result = None
        
        return success, result
    
    def register_handler(
        self,
        status_code: int,
        handler: Callable[[requests.Response], None]
    ):
        """
        注册状态码处理器
        """
        self.response_handlers[status_code] = handler
    
    def close(self):
        """
        关闭客户端
        """
        self.session.close()
        logger.info("APIClient closed")
```

#### 文件4: user/config/services.yaml

```yaml
# 服务配置

services:
  yl-monitor:
    name: "YL-Monitor"
    host: "localhost"
    port: 5500
    health_endpoint: "/api/health"
    timeout: 5
    retry: 3
    
  ar-backend:
    name: "AR-backend"
    host: "localhost"
    port: 5501
    health_endpoint: "/health"
    timeout: 5
    retry: 3
    
  user-gui:
    name: "User GUI"
    host: "localhost"
    port: 5502
    health_endpoint: "/health"
    timeout: 3
    retry: 2

# 服务发现配置
discovery:
  enabled: true
  interval: 30
  timeout: 2

# 负载均衡配置（未来扩展）
load_balancing:
  enabled: false
  strategy: "round_robin"
```

## 三、关联内容修复

### 3.1 需要同步修复的文件

| 文件 | 修复内容 | 原因 |
|------|----------|------|
| `user/gui/gui.py` | 使用ARBackendClient | 替换直接HTTP调用 |
| `user/main.py` | 初始化服务客户端 | 启动时创建客户端 |

### 3.2 详细修复说明

#### 修复1: user/gui/gui.py

```python
# 在ARApp.__init__中添加
from services.ar_backend_client import get_client

# 初始化客户端
self.ar_client = get_client("http://localhost:5501")
self.ar_client.on_status_change = self.on_service_status_change

def on_service_status_change(self, status):
    """服务状态变化回调"""
    self.log_message(f"AR-backend状态: {status.value}", "info")

# 使用客户端调用API
def start_camera(self):
    if self.ar_client.start_camera():
        self.log_message("摄像头已启动", "success")
    else:
        self.log_message("摄像头启动失败", "error")
```

## 四、部署执行步骤

### 4.1 执行前检查

```bash
# 1. 检查requests库
python3 -c "import requests; print('requests:', requests.__version__)"

# 2. 检查服务目录
ls -la user/services/
```

### 4.2 部署执行

```bash
# 1. 创建服务文件
# user/services/ar_backend_client.py
# user/services/service_discovery.py
# user/services/api_client.py

# 2. 创建配置
mkdir -p user/config
# user/config/services.yaml

# 3. 安装依赖（如果需要）
pip install requests pyyaml

# 4. 测试客户端
cd user
python3 -c "
from services.ar_backend_client import ARBackendClient
client = ARBackendClient()
print('Client created')
print('Health check:', client.health_check())
"
```

### 4.3 部署验证

```bash
# 1. 验证客户端创建
python3 -c "
from services.ar_backend_client import get_client
client = get_client()
print('✓ Client created')
print('✓ Service info:', client.get_service_info())
"

# 2. 验证服务发现
python3 -c "
from services.service_discovery import discover_services
services = discover_services()
print(f'✓ Discovered {len(services)} services')
for s in services:
    print(f'  - {s.name}: {s.url} (healthy: {s.healthy})')
"

# 3. 验证API调用
python3 -c "
from services.ar_backend_client import get_client
client = get_client()
status = client.get_status()
print('✓ Status:', status)
"
```

## 五、常见问题及解决

### 问题1: 连接被拒绝

**现象:** `Connection refused` 错误

**解决:**
```bash
# 检查AR-backend是否运行
curl http://localhost:5501/health

# 检查端口
netstat -tlnp | grep 5501
```

### 问题2: 超时错误

**现象:** 请求超时

**解决:**
```python
# 增加超时时间
client = ARBackendClient(timeout=10)
```

## 六、验证清单

- [ ] ARBackendClient创建成功
- [ ] 服务发现正常
- [ ] 健康检查通过
- [ ] API调用成功
- [ ] 重试机制工作
- [ ] 状态回调正常

## 七、下一步

完成本任务后，继续执行 **任务2.5: 创建配置管理**

查看文档: `部署/任务跟踪-阶段2-User-GUI优化-部署任务2.5-创建配置管理.md`
