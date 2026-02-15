"""
DAG引擎服务
提供DAG定义管理、执行控制和节点编排功能
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class DAGNode:
    """DAG节点"""
    id: str
    name: str
    type: str  # function, input, process, output
    x: float = 0
    y: float = 0
    status: str = "pending"  # pending, running, completed, failed
    script: Optional[str] = None
    enabled: bool = True
    dependencies: List[str] = field(default_factory=list)


@dataclass
class DAGEdge:
    """DAG连线"""
    from_node: str
    to_node: str


@dataclass
class DAGExecution:
    """DAG执行记录"""
    id: str
    dag_id: str
    status: str = "pending"
    progress: int = 0
    node_states: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DAGEngine:
    """
    DAG引擎
    
    职责:
    1. 管理DAG定义（节点和连线）
    2. 执行DAG流程
    3. 控制节点执行
    4. 提供事件流
    """
    
    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}
        self.edges: List[DAGEdge] = []
        self.executions: Dict[str, DAGExecution] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
    
    async def get_definition(self) -> Dict[str, Any]:
        """
        获取DAG定义
        """
        # 加载节点
        await self._load_nodes()
        
        return {
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.type,
                    "x": n.x,
                    "y": n.y,
                    "status": n.status,
                    "script": n.script,
                    "enabled": n.enabled
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {"from": e.from_node, "to": e.to_node}
                for e in self.edges
            ]
        }
    
    async def _load_nodes(self):
        """
        从数据库加载DAG节点
        """
        try:
            from app.models.function_mapping import FunctionMapping
            
            # 查询有DAG节点ID的功能
            functions = await FunctionMapping.filter(
                dag_node_id__isnull=False,
                is_active=True
            ).all()
            
            self.nodes = {}
            for func in functions:
                self.nodes[func.dag_node_id] = DAGNode(
                    id=func.dag_node_id,
                    name=func.name,
                    type=self._get_node_type(func.category),
                    x=func.dag_layer * 200 if func.dag_layer else 100,
                    y=len(self.nodes) * 100,
                    script=func.script_name,
                    enabled=True
                )
            
            # 如果没有节点，使用示例数据
            if not self.nodes:
                self._load_sample_nodes()
            
            # 生成连线（基于层级）
            self._generate_edges()
            
        except Exception as e:
            # 使用示例数据
            self._load_sample_nodes()
            self._generate_edges()
    
    def _get_node_type(self, category: Optional[str]) -> str:
        """根据分类获取节点类型"""
        type_map = {
            "input": "input",
            "process": "process",
            "output": "output"
        }
        return type_map.get(category, "function")
    
    def _load_sample_nodes(self):
        """加载示例节点"""
        self.nodes = {
            "data-collection": DAGNode(
                id="data-collection",
                name="数据采集",
                type="input",
                x=100,
                y=100,
                script="metrics_collector.py"
            ),
            "data-process": DAGNode(
                id="data-process",
                name="数据处理",
                type="process",
                x=350,
                y=100,
                script="data_processor.py"
            ),
            "alert-check": DAGNode(
                id="alert-check",
                name="告警检查",
                type="process",
                x=600,
                y=50,
                script="alert_monitor.py"
            ),
            "report-gen": DAGNode(
                id="report-gen",
                name="报告生成",
                type="output",
                x=850,
                y=100,
                script="report_generator.py"
            )
        }
    
    def _generate_edges(self):
        """生成节点连线"""
        self.edges = [
            DAGEdge("data-collection", "data-process"),
            DAGEdge("data-process", "alert-check"),
            DAGEdge("data-process", "report-gen")
        ]
    
    async def execute_all(self) -> str:
        """
        执行整个DAG
        
        返回执行ID
        """
        execution_id = str(uuid.uuid4())[:8]
        
        # 创建执行记录
        execution = DAGExecution(
            id=execution_id,
            dag_id="main-dag",
            status="running",
            started_at=datetime.utcnow()
        )
        self.executions[execution_id] = execution
        
        # 发布开始事件
        await self._publish_event({
            "type": "dag.started",
            "data": {"execution_id": execution_id},
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 异步执行DAG
        asyncio.create_task(self._run_dag(execution_id))
        
        return execution_id
    
    async def _run_dag(self, execution_id: str):
        """
        运行DAG流程
        """
        execution = self.executions.get(execution_id)
        if not execution:
            return
        
        try:
            # 拓扑排序获取执行顺序
            execution_order = self._topological_sort()
            
            total_nodes = len(execution_order)
            completed = 0
            
            for node_id in execution_order:
                # 执行节点
                result = await self._execute_node_internal(node_id, execution_id)
                
                # 更新进度
                completed += 1
                execution.progress = int(completed / total_nodes * 100)
                
                # 更新节点状态
                execution.node_states[node_id] = {
                    "status": "completed" if result else "failed",
                    "completed_at": datetime.utcnow().isoformat()
                }
                
                # 发布节点完成事件
                await self._publish_event({
                    "type": "dag.node.completed",
                    "data": {
                        "execution_id": execution_id,
                        "node_id": node_id,
                        "success": result
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # 如果节点失败，停止执行
                if not result:
                    execution.status = "failed"
                    break
            
            # 标记完成
            if execution.status != "failed":
                execution.status = "completed"
            
            execution.completed_at = datetime.utcnow()
            
            # 发布完成事件
            await self._publish_event({
                "type": "dag.completed",
                "data": {
                    "execution_id": execution_id,
                    "status": execution.status,
                    "progress": execution.progress
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            
            await self._publish_event({
                "type": "dag.failed",
                "data": {
                    "execution_id": execution_id,
                    "error": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def _topological_sort(self) -> List[str]:
        """
        拓扑排序获取节点执行顺序
        """
        # 构建依赖图
        in_degree = {node_id: 0 for node_id in self.nodes}
        graph = {node_id: [] for node_id in self.nodes}
        
        for edge in self.edges:
            if edge.to_node in in_degree:
                in_degree[edge.to_node] += 1
            if edge.from_node in graph:
                graph[edge.from_node].append(edge.to_node)
        
        # Kahn算法
        queue = [n for n, d in in_degree.items() if d == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            for neighbor in graph.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    async def _execute_node_internal(self, node_id: str, execution_id: str) -> bool:
        """
        内部执行节点
        """
        node = self.nodes.get(node_id)
        if not node:
            return False
        
        # 更新节点状态
        node.status = "running"
        
        # 发布节点开始事件
        await self._publish_event({
            "type": "dag.node.started",
            "data": {
                "execution_id": execution_id,
                "node_id": node_id,
                "name": node.name
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            # 模拟执行（实际应调用脚本执行器）
            if node.script:
                # 调用脚本执行
                await asyncio.sleep(1)  # 模拟执行时间
                success = True
            else:
                # 虚拟节点直接完成
                await asyncio.sleep(0.5)
                success = True
            
            node.status = "completed" if success else "failed"
            return success
            
        except Exception as e:
            node.status = "failed"
            return False
    
    async def execute_node(self, node_id: str) -> Dict[str, Any]:
        """
        执行单个节点（手动触发）
        """
        node = self.nodes.get(node_id)
        if not node:
            return {"success": False, "error": "节点不存在"}
        
        # 检查依赖是否完成
        dependencies = self._get_dependencies(node_id)
        for dep_id in dependencies:
            dep_node = self.nodes.get(dep_id)
            if dep_node and dep_node.status != "completed":
                return {
                    "success": False,
                    "error": f"前置依赖未完成: {dep_id}"
                }
        
        # 执行节点
        start_time = datetime.utcnow()
        success = await self._execute_node_internal(node_id, "manual")
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "success": success,
            "output": f"节点 {node.name} 执行{'成功' if success else '失败'}",
            "duration": duration
        }
    
    def _get_dependencies(self, node_id: str) -> List[str]:
        """获取节点的前置依赖"""
        return [e.from_node for e in self.edges if e.to_node == node_id]
    
    async def _publish_event(self, event: Dict[str, Any]):
        """发布事件到队列"""
        await self._event_queue.put(event)
    
    async def event_stream(self):
        """
        事件流生成器
        
        用于WebSocket实时推送
        """
        while True:
            try:
                # 等待事件（超时1秒）
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                yield event
            except asyncio.TimeoutError:
                # 发送心跳保持连接
                yield {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                }
    
    async def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的执行记录
        """
        executions = sorted(
            self.executions.values(),
            key=lambda e: e.started_at or datetime.min,
            reverse=True
        )[:limit]
        
        return [
            {
                "id": e.id,
                "dag_id": e.dag_id,
                "status": e.status,
                "progress": e.progress,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None
            }
            for e in executions
        ]
    
    async def get_execution_detail(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        获取执行详情
        """
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        return {
            "id": execution.id,
            "dag_id": execution.dag_id,
            "status": execution.status,
            "progress": execution.progress,
            "node_states": execution.node_states,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }
    
    async def start_dag(self, dag_id: str) -> str:
        """
        【启动DAG】启动指定DAG的执行
        
        【参数】
            dag_id: DAG标识
        
        【返回值】
            str: 执行ID
        """
        execution_id = str(uuid.uuid4())[:8]
        
        # 创建执行记录
        execution = DAGExecution(
            id=execution_id,
            dag_id=dag_id,
            status="running",
            started_at=datetime.utcnow()
        )
        self.executions[execution_id] = execution
        
        # 发布开始事件
        await self._publish_event({
            "type": "dag.started",
            "data": {
                "execution_id": execution_id,
                "dag_id": dag_id
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 异步执行DAG
        asyncio.create_task(self._run_dag(execution_id))
        
        return execution_id
    
    async def pause_dag(self, execution_id: str) -> bool:
        """
        【暂停DAG】暂停指定DAG的执行
        
        【参数】
            execution_id: 执行ID
        
        【返回值】
            bool: 是否成功暂停
        """
        execution = self.executions.get(execution_id)
        if not execution:
            return False
        
        if execution.status != "running":
            return False
        
        execution.status = "paused"
        
        # 发布暂停事件
        await self._publish_event({
            "type": "dag.paused",
            "data": {
                "execution_id": execution_id,
                "dag_id": execution.dag_id
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    
    async def resume_dag(self, execution_id: str) -> bool:
        """
        【恢复DAG】恢复指定DAG的执行
        
        【参数】
            execution_id: 执行ID
        
        【返回值】
            bool: 是否成功恢复
        """
        execution = self.executions.get(execution_id)
        if not execution:
            return False
        
        if execution.status != "paused":
            return False
        
        execution.status = "running"
        
        # 发布恢复事件
        await self._publish_event({
            "type": "dag.resumed",
            "data": {
                "execution_id": execution_id,
                "dag_id": execution.dag_id
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 继续执行
        asyncio.create_task(self._run_dag(execution_id))
        
        return True
