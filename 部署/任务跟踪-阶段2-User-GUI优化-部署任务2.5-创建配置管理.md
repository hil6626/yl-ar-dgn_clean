# 阶段2 - 任务2.5: 创建配置管理 - 详细部署文档

**任务ID:** 2.5  
**任务名称:** 创建配置管理  
**优先级:** P1（重要）  
**预计工时:** 3小时  
**状态:** 待执行  
**前置依赖:** 任务2.1完成

---

## 一、任务目标

创建统一的配置管理系统，支持YAML配置文件、环境变量和默认配置的合并管理。

## 二、部署内容

### 2.1 创建文件清单

| 序号 | 文件路径 | 操作类型 | 说明 |
|------|----------|----------|------|
| 1 | `user/config/settings.py` | 新建 | 配置管理器 |
| 2 | `user/config/default_config.yaml` | 新建 | 默认配置 |
| 3 | `user/utils/config_loader.py` | 新建 | 配置加载器 |

### 2.2 详细代码实现

#### 文件1: user/config/settings.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
统一管理应用配置
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger('Settings')


@dataclass
class CameraConfig:
    """摄像头配置"""
    device_id: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30

@dataclass
class AudioConfig:
    """音频配置"""
    sample_rate: int = 44100
    channels: int = 2
    buffer_size: int = 1024

@dataclass
class MonitoringConfig:
    """监控配置"""
    enabled: bool = True
    report_interval: int = 30
    yl_monitor_url: str = "http://localhost:5500"

@dataclass
class AppConfig:
    """应用配置"""
    name: str = "AR Live Studio"
    version: str = "2.0.0"
    camera: CameraConfig = field(default_factory=CameraConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)


class Settings:
    """
    配置管理器（单例）
    """
    
    _instance: Optional['Settings'] = None
    _config_file: Optional[Path] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._config: Dict[str, Any] = {}
        self._app_config: Optional[AppConfig] = None
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        # 1. 加载默认配置
        self._config = self._load_default_config()
        
        # 2. 加载配置文件
        config_file = self._get_config_file()
        if config_file.exists():
            file_config = self._load_yaml(config_file)
            self._merge_config(self._config, file_config)
            logger.info(f"Loaded config from: {config_file}")
        
        # 3. 加载环境变量
        env_config = self._load_env_config()
        self._merge_config(self._config, env_config)
        
        # 4. 转换为AppConfig
        self._app_config = self._dict_to_config(self._config)
        
        logger.info("Configuration loaded successfully")
    
    def _get_config_file(self) -> Path:
        """获取配置文件路径"""
        if self._config_file:
            return self._config_file
        
        # 默认路径
        user_dir = Path(__file__).parent.parent
        return user_dir / 'config' / 'user_config.yaml'
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            'app': {
                'name': 'AR Live Studio',
                'version': '2.0.0',
            },
            'camera': {
                'device_id': 0,
                'width': 1280,
                'height': 720,
                'fps': 30,
            },
            'audio': {
                'sample_rate': 44100,
                'channels': 2,
                'buffer_size': 1024,
            },
            'monitoring': {
                'enabled': True,
                'report_interval': 30,
                'yl_monitor_url': 'http://localhost:5500',
            },
            'gui': {
                'theme': 'dark',
                'window_width': 1400,
                'window_height': 900,
            }
        }
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """加载YAML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load YAML: {e}")
            return {}
    
    def _load_env_config(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        config = {}
        
        # 摄像头配置
        if 'CAMERA_DEVICE' in os.environ:
            config.setdefault('camera', {})['device_id'] = int(os.environ['CAMERA_DEVICE'])
        
        # 监控配置
        if 'YL_MONITOR_URL' in os.environ:
            config.setdefault('monitoring', {})['yl_monitor_url'] = os.environ['YL_MONITOR_URL']
        
        if 'MONITORING_ENABLED' in os.environ:
            config.setdefault('monitoring', {})['enabled'] = os.environ['MONITORING_ENABLED'].lower() == 'true'
        
        return config
    
    def _merge_config(self, base: Dict, update: Dict):
        """合并配置"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _dict_to_config(self, config_dict: Dict) -> AppConfig:
        """字典转换为配置对象"""
        return AppConfig(
            name=config_dict.get('app', {}).get('name', 'AR Live Studio'),
            version=config_dict.get('app', {}).get('version', '2.0.0'),
            camera=CameraConfig(**config_dict.get('camera', {})),
            audio=AudioConfig(**config_dict.get('audio', {})),
            monitoring=MonitoringConfig(**config_dict.get('monitoring', {})),
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号路径）"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, file_path: Optional[Path] = None):
        """保存配置到文件"""
        save_path = file_path or self._get_config_file()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Configuration saved to: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    @property
    def app_config(self) -> AppConfig:
        """获取应用配置对象"""
        return self._app_config or AppConfig()


# 便捷函数
def get_settings() -> Settings:
    """获取配置管理器实例"""
    return Settings()


def get_config(key: str, default: Any = None) -> Any:
    """获取配置值（便捷函数）"""
    return Settings().get(key, default)
```

#### 文件2: user/config/default_config.yaml

```yaml
# AR Live Studio - 默认配置

app:
  name: "AR Live Studio"
  version: "2.0.0"
  organization: "AR Studio Team"

camera:
  device_id: 0
  width: 1280
  height: 720
  fps: 30
  buffer_size: 1
  format: "MJPG"

audio:
  sample_rate: 44100
  channels: 2
  buffer_size: 1024
  format: "float32"

face:
  models_dir: "models"
  default_model: "default"
  blend_ratio: 0.5
  smoothing: 0.7

monitoring:
  enabled: true
  report_interval: 30
  yl_monitor_url: "http://localhost:5500"
  timeout: 5
  max_retries: 3

gui:
  theme: "dark"
  window_width: 1400
  window_height: 900
  min_width: 1200
  min_height: 700
  show_fps: true

logging:
  level: "INFO"
  max_file_size: 10485760  # 10MB
  backup_count: 5
  format: "%(asctime)s | %(levelname)-8s | %(message)s"

shortcuts:
  start_camera: "Ctrl+S"
  stop_camera: "Ctrl+X"
  take_screenshot: "Ctrl+P"
  toggle_fullscreen: "F11"
  open_monitor: "Ctrl+M"
```

#### 文件3: user/utils/config_loader.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载器
支持多种配置源
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """
    配置加载器
    """
    
    @staticmethod
    def load_yaml(file_path: Path) -> Dict[str, Any]:
        """加载YAML配置"""
        if not file_path.exists():
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    @staticmethod
    def load_json(file_path: Path) -> Dict[str, Any]:
        """加载JSON配置"""
        if not file_path.exists():
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def load_env(prefix: str = "AR_") -> Dict[str, Any]:
        """从环境变量加载"""
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 转换键名 AR_CAMERA_DEVICE -> camera.device
                config_key = key[len(prefix):].lower().replace('_', '.')
                config[config_key] = value
        
        return config


def load_config(config_dir: Path) -> Dict[str, Any]:
    """加载完整配置"""
    loader = ConfigLoader()
    config = {}
    
    # 加载YAML配置
    yaml_file = config_dir / 'config.yaml'
    if yaml_file.exists():
        config.update(loader.load_yaml(yaml_file))
    
    # 加载JSON配置（覆盖YAML）
    json_file = config_dir / 'config.json'
    if json_file.exists():
        config.update(loader.load_json(json_file))
    
    # 加载环境变量（最高优先级）
    env_config = loader.load_env()
    for key, value in env_config.items():
        # 设置嵌套值
        keys = key.split('.')
        target = config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
    
    return config
```

## 三、部署执行步骤

```bash
# 1. 创建配置目录
mkdir -p user/config

# 2. 创建配置文件
# user/config/settings.py
# user/config/default_config.yaml
# user/utils/config_loader.py

# 3. 测试配置加载
cd user
python3 -c "
from config.settings import get_settings
settings = get_settings()
print('App name:', settings.get('app.name'))
print('Camera device:', settings.get('camera.device_id'))
"

# 4. 保存配置
python3 -c "
from config.settings import get_settings
settings = get_settings()
settings.set('camera.width', 1920)
settings.save()
print('Config saved')
"
```

## 四、验证清单

- [ ] 配置管理器创建成功
- [ ] 默认配置加载正常
- [ ] 环境变量覆盖正常
- [ ] 配置保存正常
- [ ] 点号路径访问正常

## 五、下一步

完成本任务后，继续执行 **任务2.6: 修复 GUI 功能**

查看文档: `部署/任务跟踪-阶段2-User-GUI优化-部署任务2.6-修复GUI功能.md`
