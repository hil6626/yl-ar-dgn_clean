"""
统一配置管理中心
实现配置集中管理、热更新、变更通知
"""

import os
import json
import threading
from typing import Any, Dict, List, Callable, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ConfigSection:
    """配置节基类"""
    name: str
    version: str = "1.0.0"
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


@dataclass
class DatabaseConfig(ConfigSection):
    """数据库配置"""
    host: str = "0.0.0.0"
    port: int = 5432
    username: str = ""
    password: str = ""
    database: str = "yl_monitor"
    pool_size: int = 10
    max_overflow: int = 20
    
    def __post_init__(self):
        super().__post_init__()
        self.name = "database"


@dataclass
class CacheConfig(ConfigSection):
    """缓存配置"""
    enabled: bool = True
    backend: str = "memory"  # memory, redis, memcached
    ttl: int = 300  # 默认5分钟
    max_size: int = 1000
    
    def __post_init__(self):
        super().__post_init__()
        self.name = "cache"


@dataclass
class SecurityConfig(ConfigSection):
    """安全配置"""
    jwt_secret: str = ""
    token_expire_hours: int = 24
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    allowed_hosts: List[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.name = "security"
        if self.allowed_hosts is None:
            self.allowed_hosts = ["*"]


class ConfigCenter:
    """
    统一配置管理中心（单例模式）
    
    功能：
    1. 配置集中管理
    2. 支持配置热更新
    3. 配置变更自动通知
    4. 配置版本控制
    5. 配置持久化
    """
    
    _instance: Optional['ConfigCenter'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._config: Dict[str, Any] = {}
        self._observers: Dict[str, List[Callable]] = {}
        self._history: List[Dict] = []
        self._max_history = 100
        self._config_file = Path("config/center_config.json")
        self._lock = threading.RLock()
        
        self._load_config()
        self._initialized = True
    
    def _load_config(self):
        """从文件加载配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._config = data.get('config', {})
                    self._history = data.get('history', [])[-self._max_history:]
            except Exception as e:
                print(f"加载配置失败: {e}")
                self._init_default_config()
        else:
            self._init_default_config()
    
    def _init_default_config(self):
        """初始化默认配置"""
        self._config = {
            'database': asdict(DatabaseConfig()),
            'cache': asdict(CacheConfig()),
            'security': asdict(SecurityConfig()),
            'app': {
                'name': 'YL-Monitor',
                'version': '1.0.6',
                'debug': False,
                'log_level': 'INFO'
            }
        }
        self._save_config()
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'config': self._config,
                    'history': self._history[-self._max_history:],
                    'saved_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的路径）
        
        示例：
            get('database.host')  # 获取数据库主机
            get('app.version')    # 获取应用版本
        """
        with self._lock:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def set(self, key: str, value: Any, notify: bool = True) -> bool:
        """
        设置配置值（支持点号分隔的路径）
        
        参数：
            key: 配置键（支持路径，如 'database.host'）
            value: 配置值
            notify: 是否通知观察者
        
        返回：
            bool: 是否设置成功
        """
        with self._lock:
            keys = key.split('.')
            config = self._config
            
            # 遍历到倒数第二层
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            old_value = config.get(keys[-1])
            config[keys[-1]] = value
            
            # 记录历史
            self._history.append({
                'action': 'set',
                'key': key,
                'old_value': old_value,
                'new_value': value,
                'timestamp': datetime.now().isoformat()
            })
            
            # 保存到文件
            self._save_config()
            
            # 通知观察者
            if notify:
                self._notify_observers(key, old_value, value)
            
            return True
    
    def register_observer(self, key: str, callback: Callable[[str, Any, Any], None]):
        """
        注册配置变更观察者
        
        参数：
            key: 监听的配置键（支持通配符 '*'）
            callback: 回调函数，参数为 (key, old_value, new_value)
        """
        with self._lock:
            if key not in self._observers:
                self._observers[key] = []
            self._observers[key].append(callback)
    
    def unregister_observer(self, key: str, callback: Callable):
        """注销观察者"""
        with self._lock:
            if key in self._observers:
                self._observers[key] = [cb for cb in self._observers[key] if cb != callback]
    
    def _notify_observers(self, key: str, old_value: Any, new_value: Any):
        """通知所有相关观察者"""
        # 精确匹配
        if key in self._observers:
            for callback in self._observers[key]:
                try:
                    callback(key, old_value, new_value)
                except Exception as e:
                    print(f"通知观察者失败: {e}")
        
        # 父级匹配（如 database.host 变更，通知 database.* 的观察者）
        parts = key.split('.')
        for i in range(1, len(parts)):
            parent_key = '.'.join(parts[:i]) + '.*'
            if parent_key in self._observers:
                for callback in self._observers[parent_key]:
                    try:
                        callback(key, old_value, new_value)
                    except Exception as e:
                        print(f"通知父级观察者失败: {e}")
        
        # 全局匹配
        if '*' in self._observers:
            for callback in self._observers['*']:
                try:
                    callback(key, old_value, new_value)
                except Exception as e:
                    print(f"通知全局观察者失败: {e}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取整个配置节"""
        return self._config.get(section, {}).copy()
    
    def update_section(self, section: str, values: Dict[str, Any], notify: bool = True):
        """更新整个配置节"""
        with self._lock:
            if section not in self._config:
                self._config[section] = {}
            
            old_section = self._config[section].copy()
            self._config[section].update(values)
            
            # 记录历史
            self._history.append({
                'action': 'update_section',
                'section': section,
                'old_values': old_section,
                'new_values': values,
                'timestamp': datetime.now().isoformat()
            })
            
            self._save_config()
            
            if notify:
                for key, value in values.items():
                    full_key = f"{section}.{key}"
                    self._notify_observers(full_key, old_section.get(key), value)
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """获取配置变更历史"""
        return self._history[-limit:]
    
    def rollback(self, steps: int = 1) -> bool:
        """
        回滚配置到历史版本
        
        参数：
            steps: 回滚步数
        
        返回：
            bool: 是否回滚成功
        """
        with self._lock:
            if len(self._history) < steps:
                return False
            
            # 找到要回滚到的状态
            target_index = len(self._history) - steps - 1
            if target_index < 0:
                return False
            
            # 这里简化处理，实际应该保存完整配置快照
            # 当前实现仅支持单键回滚
            recent_changes = self._history[-steps:]
            for change in reversed(recent_changes):
                if change['action'] == 'set':
                    self.set(change['key'], change['old_value'], notify=False)
            
            self._history.append({
                'action': 'rollback',
                'steps': steps,
                'timestamp': datetime.now().isoformat()
            })
            
            return True


# 全局配置中心实例
config_center = ConfigCenter()


# 使用示例
if __name__ == "__main__":
    # 获取配置
    db_host = config_center.get('database.host')
    print(f"数据库主机: {db_host}")
    
    # 设置配置
    config_center.set('database.host', '192.168.1.100')
    
    # 注册观察者
    def on_db_config_changed(key, old, new):
        print(f"数据库配置变更: {key} = {new} (原值: {old})")
    
    config_center.register_observer('database.*', on_db_config_changed)
    
    # 更新配置节
    config_center.update_section('cache', {
        'ttl': 600,
        'max_size': 2000
    })
