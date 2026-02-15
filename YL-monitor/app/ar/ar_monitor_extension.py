"""
【AR监控扩展】AR项目监控扩展模块

功能:
- AR设备状态监控
- AR场景性能监控
- AR用户行为分析
- AR告警和通知
- 与现有监控系统集成

作者: AI Assistant
创建时间: 2026-02-10
版本: 1.0.0

依赖:
- 数据模型: app/models/ar.py
- WebSocket: app/ws/ar_ws.py
- 事件总线: app/services/event_bus.py

示例:
    extension = ARMonitorExtension()
    extension.register_device(device_id, device_info)
    extension.update_scene_metrics(scene_id, metrics)
    extension.start_monitoring()
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ARDeviceStatus(Enum):
    """
    【AR设备状态】AR设备运行状态
    
    Attributes:
        OFFLINE: 离线
        ONLINE: 在线
        ACTIVE: 活跃(正在使用)
        ERROR: 错误
        MAINTENANCE: 维护中
    """
    OFFLINE = auto()      # 离线
    ONLINE = auto()       # 在线
    ACTIVE = auto()       # 活跃(正在使用)
    ERROR = auto()        # 错误
    MAINTENANCE = auto()  # 维护中


class ARSceneType(Enum):
    """
    【AR场景类型】AR应用场景类型
    
    Attributes:
        INDUSTRIAL: 工业AR
        MEDICAL: 医疗AR
        EDUCATION: 教育AR
        ENTERTAINMENT: 娱乐AR
        NAVIGATION: 导航AR
        REMOTE_ASSIST: 远程协助
    """
    INDUSTRIAL = auto()     # 工业AR
    MEDICAL = auto()        # 医疗AR
    EDUCATION = auto()      # 教育AR
    ENTERTAINMENT = auto()  # 娱乐AR
    NAVIGATION = auto()     # 导航AR
    REMOTE_ASSIST = auto()  # 远程协助


class ARNodeType(Enum):
    """
    【AR节点类型】AR监控节点类型
    
    Attributes:
        RENDER: 渲染节点
        COMPUTE: 计算节点
        STORAGE: 存储节点
        NETWORK: 网络节点
        SENSOR: 传感器节点
        CONTROLLER: 控制节点
    """
    RENDER = auto()      # 渲染节点
    COMPUTE = auto()     # 计算节点
    STORAGE = auto()     # 存储节点
    NETWORK = auto()     # 网络节点
    SENSOR = auto()      # 传感器节点
    CONTROLLER = auto()  # 控制节点


@dataclass
class ARDevice:
    """
    【AR设备】AR设备信息
    
    Attributes:
        device_id: 设备唯一标识
        device_type: 设备类型(HoloLens/MagicLeap/手机AR等)
        device_name: 设备名称
        status: 设备状态
        ip_address: IP地址
        last_seen: 最后在线时间
        capabilities: 设备能力(摄像头/手势/语音等)
        metadata: 设备元数据
    """
    device_id: str
    device_type: str  # HoloLens, MagicLeap, PhoneAR, etc.
    device_name: str
    status: ARDeviceStatus = ARDeviceStatus.OFFLINE
    ip_address: Optional[str] = None
    last_seen: float = field(default_factory=time.time)
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'device_id': self.device_id,
            'device_type': self.device_type,
            'device_name': self.device_name,
            'status': self.status.name,
            'ip_address': self.ip_address,
            'last_seen': self.last_seen,
            'capabilities': self.capabilities,
            'metadata': self.metadata,
        }


@dataclass
class ARScene:
    """
    【AR场景】AR应用场景
    
    Attributes:
        scene_id: 场景唯一标识
        scene_name: 场景名称
        scene_type: 场景类型
        device_id: 关联设备ID
        status: 场景状态
        start_time: 开始时间
        end_time: 结束时间
        participants: 参与用户列表
        metrics: 场景性能指标
        metadata: 场景元数据
    """
    scene_id: str
    scene_name: str
    scene_type: ARSceneType
    device_id: str
    status: str = "pending"  # pending, running, paused, completed, error
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    participants: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'scene_id': self.scene_id,
            'scene_name': self.scene_name,
            'scene_type': self.scene_type.name,
            'device_id': self.device_id,
            'status': self.status,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'participants': self.participants,
            'metrics': self.metrics,
            'metadata': self.metadata,
        }


@dataclass
class ARMetrics:
    """
    【AR指标】AR性能指标
    
    Attributes:
        timestamp: 时间戳
        device_id: 设备ID
        scene_id: 场景ID
        fps: 帧率
        cpu_usage: CPU使用率
        memory_usage: 内存使用率
        tracking_quality: 追踪质量(0-100)
        network_latency: 网络延迟(ms)
        battery_level: 电池电量(%)
        temperature: 设备温度(°C)
        error_count: 错误计数
    """
    timestamp: float = field(default_factory=time.time)
    device_id: str = ""
    scene_id: Optional[str] = None
    fps: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    tracking_quality: float = 100.0
    network_latency: float = 0.0
    battery_level: float = 100.0
    temperature: float = 0.0
    error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp,
            'device_id': self.device_id,
            'scene_id': self.scene_id,
            'fps': self.fps,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'tracking_quality': self.tracking_quality,
            'network_latency': self.network_latency,
            'battery_level': self.battery_level,
            'temperature': self.temperature,
            'error_count': self.error_count,
        }


class ARAlertRule:
    """
    【AR告警规则】AR监控告警规则
    
    Attributes:
        rule_id: 规则ID
        rule_name: 规则名称
        metric_name: 监控指标名称
        threshold: 阈值
        operator: 比较运算符(>, <, >=, <=, ==)
        severity: 严重级别
        enabled: 是否启用
        cooldown: 冷却时间(秒)
    """
    
    def __init__(
        self,
        rule_id: str,
        rule_name: str,
        metric_name: str,
        threshold: float,
        operator: str = ">",
        severity: str = "warning",
        enabled: bool = True,
        cooldown: float = 300.0
    ):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.metric_name = metric_name
        self.threshold = threshold
        self.operator = operator
        self.severity = severity
        self.enabled = enabled
        self.cooldown = cooldown
        self._last_triggered: float = 0.0
    
    def check(self, value: float) -> bool:
        """
        检查指标是否触发告警
        
        Args:
            value: 指标值
        
        Returns:
            bool: 是否触发告警
        """
        if not self.enabled:
            return False
        
        # 检查冷却时间
        current_time = time.time()
        if current_time - self._last_triggered < self.cooldown:
            return False
        
        # 比较
        triggered = False
        if self.operator == ">":
            triggered = value > self.threshold
        elif self.operator == "<":
            triggered = value < self.threshold
        elif self.operator == ">=":
            triggered = value >= self.threshold
        elif self.operator == "<=":
            triggered = value <= self.threshold
        elif self.operator == "==":
            triggered = value == self.threshold
        
        if triggered:
            self._last_triggered = current_time
        
        return triggered
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'metric_name': self.metric_name,
            'threshold': self.threshold,
            'operator': self.operator,
            'severity': self.severity,
            'enabled': self.enabled,
            'cooldown': self.cooldown,
        }


class ARMonitorExtension:
    """
    【AR监控扩展】AR项目监控扩展主类
    
    功能特性:
    - 设备注册和管理
    - 场景监控
    - 性能指标采集
    - 告警规则管理
    - 实时数据推送
    - 与现有监控系统集成
    
    示例:
        extension = ARMonitorExtension()
        
        # 注册设备
        extension.register_device("hl-001", {
            'device_type': 'HoloLens2',
            'device_name': '工业AR头显-001',
            'capabilities': ['camera', 'gesture', 'voice', 'spatial_mapping']
        })
        
        # 启动场景
        extension.start_scene("scene-001", "装配指导", ARSceneType.INDUSTRIAL, "hl-001")
        
        # 更新指标
        extension.update_metrics("hl-001", ARMetrics(fps=58, cpu_usage=45.0))
        
        # 启动监控
        extension.start_monitoring()
    """
    
    def __init__(self):
        # 设备管理
        self._devices: Dict[str, ARDevice] = {}
        
        # 场景管理
        self._scenes: Dict[str, ARScene] = {}
        
        # 指标历史
        self._metrics_history: Dict[str, List[ARMetrics]] = {}
        self._max_history_size = 1000
        
        # 告警规则
        self._alert_rules: Dict[str, ARAlertRule] = {}
        
        # 告警处理器
        self._alert_handlers: List[Callable[[Dict[str, Any]], None]] = []
        
        # 监控状态
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # 事件处理器
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        logger.info("AR监控扩展已初始化")
    
    def register_device(
        self,
        device_id: str,
        device_info: Dict[str, Any]
    ) -> ARDevice:
        """
        注册AR设备
        
        Args:
            device_id: 设备唯一标识
            device_info: 设备信息字典
        
        Returns:
            ARDevice: 注册的设备对象
        """
        device = ARDevice(
            device_id=device_id,
            device_type=device_info.get('device_type', 'Unknown'),
            device_name=device_info.get('device_name', f'Device-{device_id}'),
            capabilities=device_info.get('capabilities', []),
            metadata=device_info.get('metadata', {}),
            status=ARDeviceStatus.ONLINE,
            ip_address=device_info.get('ip_address'),
        )
        
        self._devices[device_id] = device
        logger.info(f"AR设备已注册: {device_id} ({device.device_type})")
        
        # 触发事件
        self._trigger_event('device_registered', device.to_dict())
        
        return device
    
    def unregister_device(self, device_id: str) -> bool:
        """
        注销AR设备
        
        Args:
            device_id: 设备ID
        
        Returns:
            bool: 是否成功注销
        """
        if device_id in self._devices:
            device = self._devices.pop(device_id)
            logger.info(f"AR设备已注销: {device_id}")
            
            # 触发事件
            self._trigger_event('device_unregistered', device.to_dict())
            
            return True
        
        return False
    
    def update_device_status(
        self,
        device_id: str,
        status: ARDeviceStatus,
        **kwargs
    ) -> bool:
        """
        更新设备状态
        
        Args:
            device_id: 设备ID
            status: 新状态
            **kwargs: 其他更新字段
        
        Returns:
            bool: 是否更新成功
        """
        if device_id not in self._devices:
            return False
        
        device = self._devices[device_id]
        old_status = device.status
        device.status = status
        device.last_seen = time.time()
        
        # 更新其他字段
        for key, value in kwargs.items():
            if hasattr(device, key):
                setattr(device, key, value)
        
        logger.debug(f"设备状态更新: {device_id} {old_status.name} -> {status.name}")
        
        # 触发事件
        self._trigger_event('device_status_changed', {
            'device_id': device_id,
            'old_status': old_status.name,
            'new_status': status.name,
            'timestamp': time.time(),
        })
        
        return True
    
    def start_scene(
        self,
        scene_id: str,
        scene_name: str,
        scene_type: ARSceneType,
        device_id: str,
        **kwargs
    ) -> Optional[ARScene]:
        """
        启动AR场景
        
        Args:
            scene_id: 场景ID
            scene_name: 场景名称
            scene_type: 场景类型
            device_id: 设备ID
            **kwargs: 其他参数
        
        Returns:
            ARScene: 场景对象，如果设备不存在则返回None
        """
        if device_id not in self._devices:
            logger.warning(f"启动场景失败，设备不存在: {device_id}")
            return None
        
        scene = ARScene(
            scene_id=scene_id,
            scene_name=scene_name,
            scene_type=scene_type,
            device_id=device_id,
            status="running",
            start_time=time.time(),
            participants=kwargs.get('participants', []),
            metadata=kwargs.get('metadata', {}),
        )
        
        self._scenes[scene_id] = scene
        logger.info(f"AR场景已启动: {scene_id} ({scene_name}) on {device_id}")
        
        # 触发事件
        self._trigger_event('scene_started', scene.to_dict())
        
        return scene
    
    def stop_scene(self, scene_id: str, status: str = "completed") -> bool:
        """
        停止AR场景
        
        Args:
            scene_id: 场景ID
            status: 结束状态(completed/error/interrupted)
        
        Returns:
            bool: 是否成功停止
        """
        if scene_id not in self._scenes:
            return False
        
        scene = self._scenes[scene_id]
        scene.status = status
        scene.end_time = time.time()
        
        logger.info(f"AR场景已停止: {scene_id} ({status})")
        
        # 触发事件
        self._trigger_event('scene_stopped', scene.to_dict())
        
        return True
    
    def update_metrics(self, device_id: str, metrics: ARMetrics) -> bool:
        """
        更新设备性能指标
        
        Args:
            device_id: 设备ID
            metrics: 性能指标
        
        Returns:
            bool: 是否更新成功
        """
        if device_id not in self._devices:
            return False
        
        metrics.device_id = device_id
        
        # 保存到历史
        if device_id not in self._metrics_history:
            self._metrics_history[device_id] = []
        
        self._metrics_history[device_id].append(metrics)
        
        # 限制历史大小
        if len(self._metrics_history[device_id]) > self._max_history_size:
            self._metrics_history[device_id] = self._metrics_history[device_id][-self._max_history_size:]
        
        # 检查告警规则
        self._check_alert_rules(device_id, metrics)
        
        # 触发事件
        self._trigger_event('metrics_updated', metrics.to_dict())
        
        return True
    
    def _check_alert_rules(self, device_id: str, metrics: ARMetrics):
        """检查告警规则"""
        metrics_dict = metrics.to_dict()
        
        for rule in self._alert_rules.values():
            if rule.metric_name in metrics_dict:
                value = metrics_dict[rule.metric_name]
                if rule.check(value):
                    alert = {
                        'rule_id': rule.rule_id,
                        'rule_name': rule.rule_name,
                        'device_id': device_id,
                        'metric_name': rule.metric_name,
                        'metric_value': value,
                        'threshold': rule.threshold,
                        'severity': rule.severity,
                        'timestamp': time.time(),
                    }
                    
                    logger.warning(f"AR告警触发: {rule.rule_name} ({device_id})")
                    
                    # 调用告警处理器
                    for handler in self._alert_handlers:
                        try:
                            handler(alert)
                        except Exception as e:
                            logger.error(f"告警处理器错误: {e}")
                    
                    # 触发事件
                    self._trigger_event('alert_triggered', alert)
    
    def add_alert_rule(self, rule: ARAlertRule) -> 'ARMonitorExtension':
        """
        添加告警规则
        
        Args:
            rule: 告警规则
        
        Returns:
            ARMonitorExtension: 自身，支持链式调用
        """
        self._alert_rules[rule.rule_id] = rule
        logger.info(f"告警规则已添加: {rule.rule_id}")
        return self
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """
        移除告警规则
        
        Args:
            rule_id: 规则ID
        
        Returns:
            bool: 是否成功移除
        """
        if rule_id in self._alert_rules:
            del self._alert_rules[rule_id]
            logger.info(f"告警规则已移除: {rule_id}")
            return True
        return False
    
    def add_alert_handler(self, handler: Callable[[Dict[str, Any]], None]) -> 'ARMonitorExtension':
        """
        添加告警处理器
        
        Args:
            handler: 告警处理函数
        
        Returns:
            ARMonitorExtension: 自身，支持链式调用
        """
        self._alert_handlers.append(handler)
        return self
    
    def on(self, event_name: str, handler: Callable) -> 'ARMonitorExtension':
        """
        注册事件处理器
        
        Args:
            event_name: 事件名称
            handler: 处理函数
        
        Returns:
            ARMonitorExtension: 自身，支持链式调用
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)
        return self
    
    def _trigger_event(self, event_name: str, data: Dict[str, Any]):
        """触发事件"""
        if event_name in self._event_handlers:
            for handler in self._event_handlers[event_name]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"事件处理器错误: {e}")
    
    async def start_monitoring(self, interval: float = 5.0):
        """
        启动监控循环
        
        Args:
            interval: 检查间隔(秒)
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        logger.info(f"AR监控已启动，检查间隔: {interval}s")
        
        while self._monitoring:
            try:
                await self._monitoring_check()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"监控检查错误: {e}")
                await asyncio.sleep(interval)
    
    async def _monitoring_check(self):
        """执行监控检查"""
        current_time = time.time()
        
        # 检查设备心跳
        for device_id, device in list(self._devices.items()):
            # 超过30秒未更新视为离线
            if current_time - device.last_seen > 30:
                if device.status != ARDeviceStatus.OFFLINE:
                    self.update_device_status(device_id, ARDeviceStatus.OFFLINE)
                    logger.warning(f"设备离线: {device_id}")
        
        # 检查场景超时
        for scene_id, scene in list(self._scenes.items()):
            if scene.status == "running" and scene.start_time:
                duration = current_time - scene.start_time
                # 场景运行超过4小时，发送警告
                if duration > 4 * 3600:
                    logger.warning(f"场景运行时间过长: {scene_id} ({duration/3600:.1f}小时)")
    
    def stop_monitoring(self):
        """停止监控"""
        self._monitoring = False
        logger.info("AR监控已停止")
    
    def get_device(self, device_id: str) -> Optional[ARDevice]:
        """获取设备信息"""
        return self._devices.get(device_id)
    
    def get_scene(self, scene_id: str) -> Optional[ARScene]:
        """获取场景信息"""
        return self._scenes.get(scene_id)
    
    def get_all_devices(self) -> List[ARDevice]:
        """获取所有设备"""
        return list(self._devices.values())
    
    def get_all_scenes(self) -> List[ARScene]:
        """获取所有场景"""
        return list(self._scenes.values())
    
    def get_device_metrics(
        self,
        device_id: str,
        limit: int = 100
    ) -> List[ARMetrics]:
        """
        获取设备指标历史
        
        Args:
            device_id: 设备ID
            limit: 返回数量限制
        
        Returns:
            List[ARMetrics]: 指标历史列表
        """
        history = self._metrics_history.get(device_id, [])
        return history[-limit:] if limit > 0 else history
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_devices = len(self._devices)
        online_devices = sum(1 for d in self._devices.values() if d.status == ARDeviceStatus.ONLINE)
        active_devices = sum(1 for d in self._devices.values() if d.status == ARDeviceStatus.ACTIVE)
        
        total_scenes = len(self._scenes)
        running_scenes = sum(1 for s in self._scenes.values() if s.status == "running")
        
        return {
            'devices': {
                'total': total_devices,
                'online': online_devices,
                'active': active_devices,
                'offline': total_devices - online_devices,
            },
            'scenes': {
                'total': total_scenes,
                'running': running_scenes,
                'completed': sum(1 for s in self._scenes.values() if s.status == "completed"),
            },
            'alert_rules': len(self._alert_rules),
            'metrics_history_size': sum(len(h) for h in self._metrics_history.values()),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'devices': [d.to_dict() for d in self._devices.values()],
            'scenes': [s.to_dict() for s in self._scenes.values()],
            'alert_rules': [r.to_dict() for r in self._alert_rules.values()],
            'statistics': self.get_statistics(),
        }


# 便捷函数
def create_ar_monitor() -> ARMonitorExtension:
    """
    快速创建AR监控扩展
    
    Returns:
        ARMonitorExtension: 配置好的监控扩展
    """
    return ARMonitorExtension()


# 导出
__all__ = [
    'ARMonitorExtension',
    'ARDevice',
    'ARScene',
    'ARMetrics',
    'ARAlertRule',
    'ARDeviceStatus',
    'ARSceneType',
    'ARNodeType',
    'create_ar_monitor',
]
