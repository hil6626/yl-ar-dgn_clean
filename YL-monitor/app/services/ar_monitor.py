"""
AR 状态监控器
负责 AR 节点的心跳检测、状态同步和进度监控
集成事件总线支持模块联动
"""

import asyncio
import aiohttp
import yaml
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from pathlib import Path
from dataclasses import dataclass, field

from app.models.ar import ARNode, ARScene, ARStatus, ARNodeStatus, ARNodesResponse, ARStatusResponse
from app.services.event_bus import event_bus, EventType

import logging
logger = logging.getLogger('ARMonitor')


@dataclass
class NodeInfo:
    """节点信息"""
    node_id: str
    node_name: str
    node_type: str  # 'ar-backend' 或 'user-gui'
    host: str
    port: int
    health_endpoint: str
    status_endpoint: str
    check_interval: int = 30  # 秒
    timeout: int = 5  # 秒
    fail_threshold: int = 3  # 连续失败次数标记离线

    # 运行时状态
    status: str = 'unknown'  # online, offline, error
    last_check: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    consecutive_fails: int = 0
    metadata: Dict = field(default_factory=dict)

    @property
    def base_url(self) -> str:
        """获取基础URL"""
        return f"http://{self.host}:{self.port}"

    @property
    def is_online(self) -> bool:
        """检查是否在线"""
        if self.status != 'online':
            return False
        if self.last_heartbeat:
            # 心跳超时检查（2倍检查间隔）
            timeout = timedelta(seconds=self.check_interval * 2)
            if datetime.utcnow() - self.last_heartbeat > timeout:
                return False
        return True


class ARMonitor:
    """
    AR 节点监控器
    """

    def __init__(self, config_path: Optional[str] = None):
        self.nodes: Dict[str, NodeInfo] = {}
        self.scenes: Dict[str, ARScene] = {}
        self.config_path = config_path or self._find_config()
        self.session: Optional[aiohttp.ClientSession] = None
        self.check_task: Optional[asyncio.Task] = None
        self.running = False

        # 加载配置
        self._load_config()

        # 订阅 DAG 节点更新事件
        event_bus.subscribe(
            self._on_dag_node_updated,
            filter_types=[EventType.DAG_NODE_STARTED, EventType.DAG_NODE_COMPLETED],
            subscriber_id="ar_monitor_dag_listener"
        )

        # 订阅 AR 节点更新事件
        event_bus.subscribe(
            self._on_ar_node_update,
            filter_types=[EventType.AR_NODE_UPDATED],
            subscriber_id="ar_monitor_ar_listener"
        )

    def _find_config(self) -> Optional[str]:
        """查找配置文件"""
        possible_paths = [
            Path(__file__).parent.parent / 'config' / 'nodes.yaml',
            Path.cwd() / 'config' / 'nodes.yaml',
            Path('/etc/yl-monitor/nodes.yaml'),
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)
        return None

    def _load_config(self):
        """加载节点配置"""
        if not self.config_path or not Path(self.config_path).exists():
            logger.warning("未找到节点配置文件，使用默认配置")
            self._create_default_config()
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            for node_config in config.get('nodes', []):
                node = NodeInfo(**node_config)
                self.nodes[node.node_id] = node
                logger.info(f"加载节点配置: {node.node_id} ({node.node_name})")

        except Exception as e:
            logger.error(f"加载配置失败: {e}")

    def _create_default_config(self):
        """创建默认配置"""
        default_nodes = [
            NodeInfo(
                node_id='ar-backend',
                node_name='AR Backend Service',
                node_type='ar-backend',
                host='localhost',
                port=5501,
                health_endpoint='/health',
                status_endpoint='/status'
            ),
            NodeInfo(
                node_id='user-gui',
                node_name='User GUI Application',
                node_type='user-gui',
                host='localhost',
                port=5502,
                health_endpoint='/health',
                status_endpoint='/status'
            )
        ]

        for node in default_nodes:
            self.nodes[node.node_id] = node

        # 保存默认配置
        if self.config_path:
            self._save_config()

    def _save_config(self):
        """保存配置到文件"""
        try:
            config = {
                'nodes': [
                    {
                        'node_id': node.node_id,
                        'node_name': node.node_name,
                        'node_type': node.node_type,
                        'host': node.host,
                        'port': node.port,
                        'health_endpoint': node.health_endpoint,
                        'status_endpoint': node.status_endpoint,
                        'check_interval': node.check_interval,
                        'timeout': node.timeout,
                        'fail_threshold': node.fail_threshold
                    }
                    for node in self.nodes.values()
                ]
            }

            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    async def start_monitoring(self):
        """启动监控"""
        if self.running:
            return

        self.running = True
        self.session = aiohttp.ClientSession()

        # 启动定期检查任务
        self.check_task = asyncio.create_task(self._check_loop())

        logger.info(f"AR监控服务启动，监控 {len(self.nodes)} 个节点")

    async def stop_monitoring(self):
        """停止监控"""
        self.running = False

        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass

        if self.session:
            await self.session.close()

        logger.info("AR监控服务已停止")

    async def _check_loop(self):
        """检查循环"""
        while self.running:
            try:
                await self._check_all_nodes()
            except Exception as e:
                logger.error(f"检查循环异常: {e}")

            # 等待下一次检查（使用较短的间隔以便快速响应）
            await asyncio.sleep(10)

    async def _check_all_nodes(self):
        """检查所有节点"""
        tasks = [self._check_node(node) for node in self.nodes.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_node(self, node: NodeInfo):
        """检查单个节点"""
        try:
            url = f"{node.base_url}{node.health_endpoint}"

            async with self.session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=node.timeout)
            ) as response:

                if response.status == 200:
                    data = await response.json()

                    # 更新节点状态
                    node.status = 'online'
                    node.last_check = datetime.utcnow()
                    node.consecutive_fails = 0

                    # 合并返回的元数据
                    if isinstance(data, dict):
                        node.metadata.update(data)

                    logger.debug(f"节点 {node.node_id} 健康检查通过")

                else:
                    # HTTP错误
                    node.consecutive_fails += 1
                    logger.warning(
                        f"节点 {node.node_id} 健康检查失败: HTTP {response.status}"
                    )

        except asyncio.TimeoutError:
            node.consecutive_fails += 1
            logger.warning(f"节点 {node.node_id} 健康检查超时")

        except Exception as e:
            node.consecutive_fails += 1
            logger.error(f"节点 {node.node_id} 健康检查异常: {e}")

        # 检查是否达到失败阈值
        if node.consecutive_fails >= node.fail_threshold:
            if node.status != 'offline':
                node.status = 'offline'
                logger.error(f"节点 {node.node_id} 标记为离线")

                # 触发告警
                await self._trigger_alert(node, 'node_offline')

    async def _trigger_alert(self, node: NodeInfo, alert_type: str):
        """触发告警"""
        logger.warning(f"触发告警: {alert_type} - {node.node_id}")
        # 这里可以集成告警系统
        # 例如：发送邮件、钉钉通知等

    def update_heartbeat(self, node_id: str, data: dict):
        """更新节点心跳（由API调用）"""
        if node_id not in self.nodes:
            # 自动注册新节点
            logger.info(f"自动注册新节点: {node_id}")
            self._auto_register_node(node_id, data)
            return

        node = self.nodes[node_id]
        node.last_heartbeat = datetime.utcnow()
        node.status = data.get('status', 'unknown')

        # 更新元数据
        if 'gui' in data:
            node.metadata['gui'] = data['gui']
        if 'resources' in data:
            node.metadata['resources'] = data['resources']

        # 重置失败计数
        if node.consecutive_fails > 0:
            logger.info(f"节点 {node_id} 恢复在线")
            node.consecutive_fails = 0

    def _auto_register_node(self, node_id: str, data: dict):
        """自动注册节点"""
        node_type = data.get('node_type', 'unknown')

        # 根据类型确定端口
        port_map = {
            'ar-backend': 5501,
            'user-gui': 5502
        }

        node = NodeInfo(
            node_id=node_id,
            node_name=data.get('node_name', node_id),
            node_type=node_type,
            host='localhost',
            port=port_map.get(node_type, 5500),
            health_endpoint='/health',
            status_endpoint='/status'
        )

        self.nodes[node_id] = node
        logger.info(f"节点 {node_id} 已自动注册")

    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        """获取节点信息"""
        return self.nodes.get(node_id)

    def get_all_nodes(self) -> List[NodeInfo]:
        """获取所有节点"""
        return list(self.nodes.values())

    def get_online_nodes(self) -> List[NodeInfo]:
        """获取在线节点"""
        return [n for n in self.nodes.values() if n.is_online]

    def get_offline_nodes(self) -> List[NodeInfo]:
        """获取离线节点"""
        return [n for n in self.nodes.values() if not n.is_online]

    async def get_node_status(self, node_id: str) -> Optional[dict]:
        """获取节点详细状态"""
        node = self.nodes.get(node_id)
        if not node:
            return None

        try:
            url = f"{node.base_url}{node.status_endpoint}"
            async with self.session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=node.timeout)
            ) as response:

                if response.status == 200:
                    return await response.json()

        except Exception as e:
            logger.error(f"获取节点 {node_id} 状态失败: {e}")

        return None

    def _bootstrap_nodes(self):
        """初始化默认节点，确保前端可见数据"""
        defaults = [
            ARNode(id="ar_node_1", name="AR 渲染节点 1", status=ARNodeStatus.ONLINE, resources={"cpu": 25, "memory": 40, "gpu": 30}),
            ARNode(id="ar_node_2", name="AR 渲染节点 2", status=ARNodeStatus.BUSY, resources={"cpu": 55, "memory": 65, "gpu": 70}),
            ARNode(id="ar_node_3", name="AR 渲染节点 3", status=ARNodeStatus.OFFLINE, resources={"cpu": 0, "memory": 0, "gpu": 0}),
        ]
        # Store AR nodes separately from monitoring nodes
        self.ar_nodes: Dict[str, ARNode] = {}
        for node in defaults:
            self.ar_nodes[node.id] = node
                    
    def _on_dag_node_updated(self, event):
        """处理 DAG 节点更新事件，同步 AR 节点状态"""
        node_id = event.data.get('node_id')
        node_type = event.data.get('node_type')
        
        if node_type == 'ar':
            # 更新 AR 节点状态
            self.update_ar_node_from_dag(node_id, event.data)
    
    def _on_ar_node_update(self, event):
        """处理 AR 节点更新事件"""
        node_id = event.data.get('node_id')
        ar_config = event.data.get('ar_config', {})
        
        # 更新或创建 AR 节点
        if node_id not in self.nodes:
            node = ARNode(
                id=node_id,
                name=ar_config.get('name', node_id),
                type=ar_config.get('type', 'render'),
                status=ARNodeStatus.ONLINE
            )
            self.nodes[node_id] = node
        else:
            self.nodes[node_id].status = ARNodeStatus.ONLINE
            self.nodes[node_id].last_heartbeat = datetime.now()
        
        # 发布 AR 状态变更事件
        event_bus.publish_event(
            event_type=EventType.AR_STATUS_CHANGED,
            source="ar_monitor",
            data={
                "node_id": node_id,
                "status": "updated",
                "config": ar_config
            }
        )
    
    def update_ar_node_from_dag(self, node_id: str, dag_data: Dict):
        """从 DAG 节点更新 AR 节点状态"""
        if node_id not in self.nodes:
            node = ARNode(
                id=node_id,
                name=node_id,
                type="render",
                status=ARNodeStatus.ONLINE
            )
            self.nodes[node_id] = node
        else:
            self.nodes[node_id].status = ARNodeStatus.ONLINE
            self.nodes[node_id].last_heartbeat = datetime.now()
    
    def register_node(self, node: ARNode):
        """注册节点"""
        self.nodes[node.id] = node
        
        # 发布节点注册事件
        event_bus.publish_event(
            event_type=EventType.AR_NODE_UPDATED,
            source="ar_monitor",
            data={
                "node_id": node.id,
                "status": "registered",
                "node_type": node.type
            }
        )
        
    def unregister_node(self, node_id: str):
        """注销节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            
    def update_node_heartbeat(self, node_id: str):
        """更新节点心跳"""
        if node_id in self.nodes:
            self.nodes[node_id].last_heartbeat = datetime.now()
            if self.nodes[node_id].status != ARNodeStatus.ONLINE:
                self.nodes[node_id].status = ARNodeStatus.ONLINE
                # 发布心跳恢复事件
                event_bus.publish_event(
                    event_type=EventType.AR_STATUS_CHANGED,
                    source="ar_monitor",
                    data={
                        "node_id": node_id,
                        "status": "heartbeat_restored"
                    }
                )
            
    def get_nodes(self) -> ARNodesResponse:
        """获取所有节点"""
        node_infos = list(self.nodes.values())
        online_count = sum(1 for n in node_infos if n.status == ARNodeStatus.ONLINE)
        offline_count = len(node_infos) - online_count
        
        # Convert NodeInfo to ARNode
        ar_nodes = []
        for info in node_infos:
            ar_node = ARNode(
                id=info.node_id,
                name=info.node_name,
                type=info.node_type,
                status=ARNodeStatus(info.status) if info.status in [s.value for s in ARNodeStatus] else ARNodeStatus.OFFLINE,
                ip_address=info.host,
                port=info.port,
                last_heartbeat=info.last_heartbeat
            )
            ar_nodes.append(ar_node)
        
        return ARNodesResponse(
            nodes=ar_nodes,
            total=len(ar_nodes),
            online_count=online_count,
            offline_count=offline_count
        )
    
    def get_scene_status(self, scene_id: str) -> Optional[ARStatusResponse]:
        """获取场景状态"""
        scene = self.scenes.get(scene_id)
        if scene is None:
            return None
            
        online_nodes = sum(1 for n in scene.nodes if n.status == ARNodeStatus.ONLINE)
        
        return ARStatusResponse(
            scene_id=scene.id,
            status=scene.status,
            progress=scene.progress,
            nodes=scene.nodes,
            total_nodes=len(scene.nodes),
            online_nodes=online_nodes
        )
    
    def create_scene(self, scene: ARScene):
        """创建场景"""
        self.scenes[scene.id] = scene
        
    def update_scene_progress(self, scene_id: str, progress: float):
        """更新场景进度"""
        if scene_id in self.scenes:
            self.scenes[scene_id].progress = progress
            self.scenes[scene_id].updated_at = datetime.now()
            
            if progress >= 100:
                self.scenes[scene_id].status = ARStatus.COMPLETED
            elif progress > 0:
                self.scenes[scene_id].status = ARStatus.RENDERING
            
            # 发布进度更新事件
            event_bus.publish_event(
                event_type=EventType.AR_NODE_UPDATED,
                source="ar_monitor",
                data={
                    "scene_id": scene_id,
                    "progress": progress,
                    "status": self.scenes[scene_id].status.value
                }
            )
