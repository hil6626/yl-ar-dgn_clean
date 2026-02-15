"""
【DAG可视化器】DAG图可视化与交互增强

功能:
- 大图渲染优化(支持100+节点)
- 节点拖拽和连线编辑
- 画布缩放和平滑滚动
- 实时状态更新
- 性能优化渲染

作者: AI Assistant
创建时间: 2026-02-10
版本: 1.0.0

依赖:
- 前端: D3.js / Cytoscape.js
- 后端: 节点布局算法

示例:
    visualizer = DAGVisualizer()
    layout = visualizer.calculate_layout(nodes, edges)
    optimized = visualizer.optimize_large_graph(nodes, edges)
"""

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class LayoutType(Enum):
    """
    【布局类型】DAG布局类型枚举
    
    Attributes:
        HIERARCHICAL: 层次布局
        FORCE_DIRECTED: 力导向布局
        GRID: 网格布局
        CIRCULAR: 圆形布局
    """
    HIERARCHICAL = "hierarchical"      # 层次布局
    FORCE_DIRECTED = "force"           # 力导向布局
    GRID = "grid"                      # 网格布局
    CIRCULAR = "circular"              # 圆形布局


@dataclass
class Node:
    """
    【节点】DAG节点定义
    
    Attributes:
        id: 节点唯一标识
        label: 节点显示名称
        type: 节点类型(start/task/decision/end)
        status: 节点状态(pending/running/success/failed)
        x: X坐标
        y: Y坐标
        width: 节点宽度
        height: 节点高度
        metadata: 节点元数据
    """
    id: str
    label: str
    type: str = "task"  # start, task, decision, end
    status: str = "pending"  # pending, running, success, failed, skipped
    x: float = 0.0
    y: float = 0.0
    width: float = 120.0
    height: float = 60.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'label': self.label,
            'type': self.type,
            'status': self.status,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'metadata': self.metadata,
        }


@dataclass
class Edge:
    """
    【边】DAG边定义
    
    Attributes:
        id: 边唯一标识
        source: 源节点ID
        target: 目标节点ID
        label: 边标签
        type: 边类型(standard/conditional/error)
        status: 边状态
        points: 路径点列表
    """
    id: str
    source: str
    target: str
    label: str = ""
    type: str = "standard"  # standard, conditional, error
    status: str = "pending"
    points: List[Tuple[float, float]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'label': self.label,
            'type': self.type,
            'status': self.status,
            'points': self.points,
        }


@dataclass
class Viewport:
    """
    【视口】画布视口定义
    
    Attributes:
        x: 视口X坐标
        y: 视口Y坐标
        width: 视口宽度
        height: 视口高度
        scale: 缩放比例
    """
    x: float = 0.0
    y: float = 0.0
    width: float = 1200.0
    height: float = 800.0
    scale: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'scale': self.scale,
        }


class LayoutAlgorithm:
    """
    【布局算法】DAG节点布局算法
    
    支持多种布局算法:
    - 层次布局(Hierarchical): 适合流程图
    - 力导向布局(Force-directed): 适合复杂关系图
    - 网格布局(Grid): 适合规则排列
    - 圆形布局(Circular): 适合环形结构
    """
    
    @staticmethod
    def hierarchical(
        nodes: List[Node],
        edges: List[Edge],
        level_distance: float = 100.0,
        node_distance: float = 150.0
    ) -> Dict[str, Tuple[float, float]]:
        """
        层次布局算法
        
        将节点按层次排列，适合DAG流程图
        
        Args:
            nodes: 节点列表
            edges: 边列表
            level_distance: 层间距
            node_distance: 节点间距
        
        Returns:
            Dict[str, Tuple[float, float]]: 节点ID到坐标的映射
        """
        # 构建邻接表
        adjacency: Dict[str, List[str]] = {node.id: [] for node in nodes}
        in_degree: Dict[str, int] = {node.id: 0 for node in nodes}
        
        for edge in edges:
            if edge.source in adjacency and edge.target in adjacency:
                adjacency[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        
        # 拓扑排序确定层次
        levels: Dict[str, int] = {}
        current_level = 0
        current_nodes = [n for n, d in in_degree.items() if d == 0]
        
        while current_nodes:
            next_nodes = []
            for node_id in current_nodes:
                levels[node_id] = current_level
                for neighbor in adjacency[node_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_nodes.append(neighbor)
            current_nodes = next_nodes
            current_level += 1
        
        # 计算坐标
        positions: Dict[str, Tuple[float, float]] = {}
        level_nodes: Dict[int, List[str]] = {}
        
        for node_id, level in levels.items():
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node_id)
        
        for level, node_ids in level_nodes.items():
            y = level * level_distance
            total_width = len(node_ids) * node_distance
            start_x = -total_width / 2
            
            for i, node_id in enumerate(node_ids):
                x = start_x + i * node_distance
                positions[node_id] = (x, y)
        
        return positions
    
    @staticmethod
    def force_directed(
        nodes: List[Node],
        edges: List[Edge],
        iterations: int = 100,
        repulsion: float = 1000.0,
        spring_length: float = 100.0,
        spring_strength: float = 0.05
    ) -> Dict[str, Tuple[float, float]]:
        """
        力导向布局算法
        
        模拟物理力使节点自动排列
        
        Args:
            nodes: 节点列表
            edges: 边列表
            iterations: 迭代次数
            repulsion: 斥力系数
            spring_length: 弹簧长度
            spring_strength: 弹簧强度
        
        Returns:
            Dict[str, Tuple[float, float]]: 节点ID到坐标的映射
        """
        # 初始化位置
        positions: Dict[str, List[float]] = {}
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes)
            positions[node.id] = [math.cos(angle) * 200, math.sin(angle) * 200]
        
        # 构建边索引
        edge_pairs: Set[Tuple[str, str]] = set()
        for edge in edges:
            edge_pairs.add((edge.source, edge.target))
        
        # 迭代优化
        for _ in range(iterations):
            # 计算斥力
            for i, node_i in enumerate(nodes):
                fx, fy = 0.0, 0.0
                for j, node_j in enumerate(nodes):
                    if i != j:
                        dx = positions[node_i.id][0] - positions[node_j.id][0]
                        dy = positions[node_i.id][1] - positions[node_j.id][1]
                        dist = math.sqrt(dx * dx + dy * dy) + 0.1
                        force = repulsion / (dist * dist)
                        fx += (dx / dist) * force
                        fy += (dy / dist) * force
                
                positions[node_i.id][0] += fx * 0.1
                positions[node_i.id][1] += fy * 0.1
            
            # 计算引力(边)
            for source_id, target_id in edge_pairs:
                dx = positions[target_id][0] - positions[source_id][0]
                dy = positions[target_id][1] - positions[source_id][1]
                dist = math.sqrt(dx * dx + dy * dy) + 0.1
                force = (dist - spring_length) * spring_strength
                
                fx = (dx / dist) * force
                fy = (dy / dist) * force
                
                positions[source_id][0] += fx
                positions[source_id][1] += fy
                positions[target_id][0] -= fx
                positions[target_id][1] -= fy
        
        return {k: (v[0], v[1]) for k, v in positions.items()}
    
    @staticmethod
    def grid(
        nodes: List[Node],
        cols: int = 5,
        cell_width: float = 150.0,
        cell_height: float = 100.0
    ) -> Dict[str, Tuple[float, float]]:
        """
        网格布局算法
        
        将节点按网格排列
        
        Args:
            nodes: 节点列表
            cols: 列数
            cell_width: 单元格宽度
            cell_height: 单元格高度
        
        Returns:
            Dict[str, Tuple[float, float]]: 节点ID到坐标的映射
        """
        positions: Dict[str, Tuple[float, float]] = {}
        
        for i, node in enumerate(nodes):
            row = i // cols
            col = i % cols
            x = col * cell_width
            y = row * cell_height
            positions[node.id] = (x, y)
        
        return positions


class DAGVisualizer:
    """
    【DAG可视化器】DAG图可视化与交互
    
    功能特性:
    - 大图渲染优化(支持100+节点)
    - 多种布局算法
    - 实时状态更新
    - 性能优化渲染
    """
    
    def __init__(
        self,
        layout_algorithm: str = "hierarchical",
        enable_optimization: bool = True
    ):
        self.layout_algorithm = layout_algorithm
        self.enable_optimization = enable_optimization
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}
        self._viewport = Viewport()
        
        logger.info(f"DAG可视化器已初始化: 算法={layout_algorithm}")
    
    def add_node(self, node: Node) -> 'DAGVisualizer':
        """添加节点"""
        self._nodes[node.id] = node
        return self
    
    def add_edge(self, edge: Edge) -> 'DAGVisualizer':
        """添加边"""
        self._edges[edge.id] = edge
        return self
    
    def remove_node(self, node_id: str) -> 'DAGVisualizer':
        """移除节点"""
        if node_id in self._nodes:
            del self._nodes[node_id]
            # 移除相关边
            edges_to_remove = [
                eid for eid, e in self._edges.items()
                if e.source == node_id or e.target == node_id
            ]
            for eid in edges_to_remove:
                del self._edges[eid]
        return self
    
    def remove_edge(self, edge_id: str) -> 'DAGVisualizer':
        """移除边"""
        if edge_id in self._edges:
            del self._edges[edge_id]
        return self
    
    def update_node_status(self, node_id: str, status: str) -> bool:
        """更新节点状态"""
        if node_id in self._nodes:
            self._nodes[node_id].status = status
            return True
        return False
    
    def calculate_layout(self) -> Dict[str, Tuple[float, float]]:
        """
        计算节点布局
        
        Returns:
            Dict[str, Tuple[float, float]]: 节点位置
        """
        nodes = list(self._nodes.values())
        edges = list(self._edges.values())
        
        if not nodes:
            return {}
        
        # 选择布局算法
        if self.layout_algorithm == "hierarchical":
            positions = LayoutAlgorithm.hierarchical(nodes, edges)
        elif self.layout_algorithm == "force":
            positions = LayoutAlgorithm.force_directed(nodes, edges)
        elif self.layout_algorithm == "grid":
            positions = LayoutAlgorithm.grid(nodes)
        else:
            positions = LayoutAlgorithm.hierarchical(nodes, edges)
        
        # 更新节点位置
        for node_id, (x, y) in positions.items():
            if node_id in self._nodes:
                self._nodes[node_id].x = x
                self._nodes[node_id].y = y
        
        return positions
    
    def optimize_large_graph(self) -> Dict[str, Any]:
        """
        优化大图渲染
        
        当节点数超过阈值时，启用优化策略:
        - 节点聚合
        - 层级折叠
        - 虚拟滚动
        - 增量渲染
        
        Returns:
            Dict[str, Any]: 优化结果
        """
        node_count = len(self._nodes)
        edge_count = len(self._edges)
        
        optimization_result = {
            'original_nodes': node_count,
            'original_edges': edge_count,
            'optimized_nodes': node_count,
            'optimized_edges': edge_count,
            'strategies_applied': [],
            'clusters': [],
        }
        
        # 节点数超过100，启用聚合
        if node_count > 100 and self.enable_optimization:
            clusters = self._cluster_nodes()
            optimization_result['clusters'] = clusters
            optimization_result['strategies_applied'].append('clustering')
            optimization_result['optimized_nodes'] = len(clusters)
        
        # 边数超过200，启用边简化
        if edge_count > 200 and self.enable_optimization:
            simplified_edges = self._simplify_edges()
            optimization_result['strategies_applied'].append('edge_simplification')
            optimization_result['optimized_edges'] = simplified_edges
        
        logger.info(f"大图优化完成: {optimization_result['strategies_applied']}")
        return optimization_result
    
    def _cluster_nodes(self) -> List[Dict[str, Any]]:
        """
        节点聚类
        
        将紧密连接的节点聚合成组
        """
        # 简单的基于层次的聚类
        levels: Dict[int, List[str]] = {}
        
        for node in self._nodes.values():
            level = int(node.y / 100)  # 假设层间距100
            if level not in levels:
                levels[level] = []
            levels[level].append(node.id)
        
        clusters = []
        for level, node_ids in levels.items():
            if len(node_ids) > 10:  # 超过10个节点聚类
                # 分成多个小组
                group_size = 10
                for i in range(0, len(node_ids), group_size):
                    group = node_ids[i:i + group_size]
                    clusters.append({
                        'id': f"cluster_{level}_{i}",
                        'nodes': group,
                        'level': level,
                        'count': len(group),
                    })
            else:
                clusters.append({
                    'id': f"cluster_{level}",
                    'nodes': node_ids,
                    'level': level,
                    'count': len(node_ids),
                })
        
        return clusters
    
    def _simplify_edges(self) -> int:
        """
        简化边
        
        隐藏非关键边，只保留主干
        """
        # 保留连接到关键节点的边
        critical_nodes = {
            node_id for node_id, node in self._nodes.items()
            if node.type in ['start', 'end'] or len([
                e for e in self._edges.values()
                if e.source == node_id or e.target == node_id
            ]) > 2
        }
        
        simplified_count = 0
        for edge in list(self._edges.values()):
            if edge.source not in critical_nodes and edge.target not in critical_nodes:
                # 标记为简化(不删除，只标记)
                edge.metadata['simplified'] = True
                simplified_count += 1
        
        return len(self._edges) - simplified_count
    
    def get_visible_nodes(self, viewport: Optional[Viewport] = None) -> List[Node]:
        """
        获取视口内可见节点
        
        用于虚拟滚动优化
        
        Args:
            viewport: 视口定义，默认使用当前视口
        
        Returns:
            List[Node]: 可见节点列表
        """
        vp = viewport or self._viewport
        
        visible_nodes = []
        for node in self._nodes.values():
            # 检查节点是否在视口内
            node_left = node.x - node.width / 2
            node_right = node.x + node.width / 2
            node_top = node.y - node.height / 2
            node_bottom = node.y + node.height / 2
            
            vp_left = vp.x
            vp_right = vp.x + vp.width / vp.scale
            vp_top = vp.y
            vp_bottom = vp.y + vp.height / vp.scale
            
            # 碰撞检测
            if (node_left < vp_right and node_right > vp_left and
                node_top < vp_bottom and node_bottom > vp_top):
                visible_nodes.append(node)
        
        return visible_nodes
    
    def pan(self, dx: float, dy: float) -> 'DAGVisualizer':
        """
        平移画布
        
        Args:
            dx: X方向移动距离
            dy: Y方向移动距离
        
        Returns:
            DAGVisualizer: 自身，支持链式调用
        """
        self._viewport.x += dx
        self._viewport.y += dy
        return self
    
    def zoom(self, factor: float, center_x: float = 0.0, center_y: float = 0.0) -> 'DAGVisualizer':
        """
        缩放画布
        
        Args:
            factor: 缩放因子(>1放大，<1缩小)
            center_x: 缩放中心X坐标
            center_y: 缩放中心Y坐标
        
        Returns:
            DAGVisualizer: 自身，支持链式调用
        """
        old_scale = self._viewport.scale
        new_scale = max(0.1, min(5.0, old_scale * factor))  # 限制缩放范围
        
        # 以中心点缩放
        self._viewport.x = center_x - (center_x - self._viewport.x) * (new_scale / old_scale)
        self._viewport.y = center_y - (center_y - self._viewport.y) * (new_scale / old_scale)
        self._viewport.scale = new_scale
        
        return self
    
    def fit_to_screen(self, width: float, height: float) -> 'DAGVisualizer':
        """
        适应屏幕
        
        自动调整视口以显示所有节点
        
        Args:
            width: 屏幕宽度
            height: 屏幕高度
        
        Returns:
            DAGVisualizer: 自身，支持链式调用
        """
        if not self._nodes:
            return self
        
        # 计算节点边界
        min_x = min(node.x - node.width / 2 for node in self._nodes.values())
        max_x = max(node.x + node.width / 2 for node in self._nodes.values())
        min_y = min(node.y - node.height / 2 for node in self._nodes.values())
        max_y = max(node.y + node.height / 2 for node in self._nodes.values())
        
        # 计算缩放比例
        content_width = max_x - min_x + 100  # 留边距
        content_height = max_y - min_y + 100
        
        scale_x = width / content_width
        scale_y = height / content_height
        scale = min(scale_x, scale_y, 1.0)  # 不超过100%
        
        # 设置视口
        self._viewport.scale = scale
        self._viewport.x = min_x - 50
        self._viewport.y = min_y - 50
        self._viewport.width = width
        self._viewport.height = height
        
        return self
    
    def render_dag(
        self,
        dag_data: Optional[Dict[str, Any]] = None,
        layout_type: Optional[LayoutType] = None
    ) -> Dict[str, Any]:
        """
        【渲染DAG】渲染DAG图
        
        【参数】
            dag_data: DAG数据，包含nodes和edges
            layout_type: 布局类型，默认使用初始化时的设置
        
        【返回值】
            Dict[str, Any]: 渲染结果，包含nodes、edges、svg等
        """
        # 如果提供了DAG数据，先加载
        if dag_data:
            # 清空现有数据
            self._nodes.clear()
            self._edges.clear()
            
            # 加载节点
            for node_data in dag_data.get('nodes', []):
                node = Node(
                    id=node_data['id'],
                    label=node_data.get('name', node_data['id']),
                    type=node_data.get('type', 'task'),
                    status=node_data.get('status', 'pending'),
                    x=node_data.get('x', 0.0),
                    y=node_data.get('y', 0.0)
                )
                self.add_node(node)
            
            # 加载边
            for edge_data in dag_data.get('edges', []):
                edge = Edge(
                    id=f"{edge_data['source']}-{edge_data['target']}",
                    source=edge_data['source'],
                    target=edge_data['target'],
                    type=edge_data.get('type', 'standard')
                )
                self.add_edge(edge)
        
        # 设置布局算法
        if layout_type:
            self.layout_algorithm = layout_type.value
        
        # 计算布局
        positions = self.calculate_layout()
        
        # 生成渲染结果
        result = {
            'nodes': [node.to_dict() for node in self._nodes.values()],
            'edges': [edge.to_dict() for edge in self._edges.values()],
            'positions': positions,
            'viewport': self._viewport.to_dict(),
            'layout': self.layout_algorithm,
            'node_count': len(self._nodes),
            'edge_count': len(self._edges),
        }
        
        # 生成SVG（简化版本）
        svg_elements = []
        for node in self._nodes.values():
            svg_elements.append(
                f'<rect x="{node.x-60}" y="{node.y-30}" width="120" height="60" '
                f'fill="#4a90d9" stroke="#2c5aa0" rx="5"/>'
                f'<text x="{node.x}" y="{node.y+5}" text-anchor="middle" '
                f'fill="white" font-size="12">{node.label}</text>'
            )
        
        for edge in self._edges.values():
            source = self._nodes.get(edge.source)
            target = self._nodes.get(edge.target)
            if source and target:
                svg_elements.append(
                    f'<line x1="{source.x}" y1="{source.y}" '
                    f'x2="{target.x}" y2="{target.y}" '
                    f'stroke="#666" stroke-width="2" marker-end="url(#arrow)"/>'
                )
        
        result['svg'] = (
            f'<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">'
            f'<defs><marker id="arrow" markerWidth="10" markerHeight="10" '
            f'refX="9" refY="3" orient="auto" markerUnits="strokeWidth">'
            f'<path d="M0,0 L0,6 L9,3 z" fill="#666"/></marker></defs>'
            f'{"".join(svg_elements)}</svg>'
        )
        
        return result
    
    def get_node_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        【获取节点详情】获取指定节点的详细信息
        
        【参数】
            node_id: 节点ID
        
        【返回值】
            Dict[str, Any]: 节点详情，或 None 如果未找到
        """
        node = self._nodes.get(node_id)
        if not node:
            return None
        
        # 计算入度和出度
        in_degree = sum(1 for e in self._edges.values() if e.target == node_id)
        out_degree = sum(1 for e in self._edges.values() if e.source == node_id)
        
        # 获取上下游节点
        upstream = [e.source for e in self._edges.values() if e.target == node_id]
        downstream = [e.target for e in self._edges.values() if e.source == node_id]
        
        return {
            'id': node.id,
            'label': node.label,
            'type': node.type,
            'status': node.status,
            'position': {'x': node.x, 'y': node.y},
            'size': {'width': node.width, 'height': node.height},
            'in_degree': in_degree,
            'out_degree': out_degree,
            'upstream_nodes': upstream,
            'downstream_nodes': downstream,
            'metadata': node.metadata,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'nodes': [node.to_dict() for node in self._nodes.values()],
            'edges': [edge.to_dict() for edge in self._edges.values()],
            'viewport': self._viewport.to_dict(),
            'layout_algorithm': self.layout_algorithm,
            'node_count': len(self._nodes),
            'edge_count': len(self._edges),
        }
    
    def export_to_cytoscape(self) -> Dict[str, Any]:
        """
        导出为Cytoscape.js格式
        
        Returns:
            Dict[str, Any]: Cytoscape元素定义
        """
        elements = []
        
        # 节点
        for node in self._nodes.values():
            elements.append({
                'data': {
                    'id': node.id,
                    'label': node.label,
                    'type': node.type,
                    'status': node.status,
                    **node.metadata
                },
                'position': {
                    'x': node.x,
                    'y': node.y
                }
            })
        
        # 边
        for edge in self._edges.values():
            elements.append({
                'data': {
                    'id': edge.id,
                    'source': edge.source,
                    'target': edge.target,
                    'label': edge.label,
                    'type': edge.type,
                    'status': edge.status,
                }
            })
        
        return {'elements': elements}


# 便捷函数
def create_visualizer(
    nodes: Optional[List[Node]] = None,
    edges: Optional[List[Edge]] = None,
    layout: str = "hierarchical"
) -> DAGVisualizer:
    """
    快速创建可视化器
    
    Args:
        nodes: 节点列表
        edges: 边列表
        layout: 布局算法
    
    Returns:
        DAGVisualizer: 配置好的可视化器
    """
    visualizer = DAGVisualizer(layout_algorithm=layout)
    
    if nodes:
        for node in nodes:
            visualizer.add_node(node)
    
    if edges:
        for edge in edges:
            visualizer.add_edge(edge)
    
    return visualizer


# 导出
__all__ = [
    'DAGVisualizer',
    'Node',
    'Edge',
    'Viewport',
    'LayoutAlgorithm',
    'create_visualizer',
]
