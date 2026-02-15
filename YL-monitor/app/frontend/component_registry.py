"""
前端组件注册中心
实现组件化架构设计
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


class ComponentType(Enum):
    """组件类型"""
    CHART = "chart"
    TABLE = "table"
    FORM = "form"
    MODAL = "modal"
    CARD = "card"
    BUTTON = "button"
    INPUT = "input"
    SELECT = "select"
    DATE_PICKER = "date_picker"
    FILE_UPLOAD = "file_upload"
    PROGRESS = "progress"
    ALERT = "alert"
    BADGE = "badge"
    TAB = "tab"
    ACCORDION = "accordion"
    TREE = "tree"
    TIMELINE = "timeline"


@dataclass
class ComponentConfig:
    """组件配置"""
    name: str
    component_type: ComponentType
    template: str
    styles: List[str] = field(default_factory=list)
    scripts: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    props: Dict[str, Any] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)
    lazy_load: bool = True
    cache_ttl: int = 300  # 缓存时间（秒）


class ComponentRegistry:
    """组件注册中心"""
    
    def __init__(self):
        self._components: Dict[str, ComponentConfig] = {}
        self._lazy_loaders: Dict[str, Callable] = {}
        self._cache: Dict[str, Any] = {}
    
    def register(self, component_id: str, config: ComponentConfig) -> None:
        """注册组件"""
        self._components[component_id] = config
    
    def unregister(self, component_id: str) -> bool:
        """注销组件"""
        if component_id in self._components:
            del self._components[component_id]
            return True
        return False
    
    def get(self, component_id: str) -> Optional[ComponentConfig]:
        """获取组件配置"""
        return self._components.get(component_id)
    
    def list_by_type(self, component_type: ComponentType) -> List[ComponentConfig]:
        """按类型列出组件"""
        return [
            config for config in self._components.values()
            if config.component_type == component_type
        ]
    
    def register_lazy_loader(self, component_id: str, loader: Callable) -> None:
        """注册懒加载器"""
        self._lazy_loaders[component_id] = loader
    
    def load_component(self, component_id: str) -> Optional[Dict[str, Any]]:
        """懒加载组件"""
        # 检查缓存
        if component_id in self._cache:
            return self._cache[component_id]
        
        # 执行懒加载
        loader = self._lazy_loaders.get(component_id)
        if loader:
            component_data = loader()
            config = self._components.get(component_id)
            if config and config.cache_ttl > 0:
                self._cache[component_id] = component_data
            return component_data
        
        return None
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()


# 全局组件注册中心实例
component_registry = ComponentRegistry()


# 预定义常用组件
def register_default_components():
    """注册默认组件"""
    
    # 图表组件
    component_registry.register("line_chart", ComponentConfig(
        name="折线图",
        component_type=ComponentType.CHART,
        template="components/charts/line_chart.html",
        styles=["/static/css/components/line_chart.css"],
        scripts=["/static/js/components/line_chart.js"],
        dependencies=["chart.js"],
        props={"type": "line", "animation": True},
        lazy_load=True
    ))
    
    component_registry.register("bar_chart", ComponentConfig(
        name="柱状图",
        component_type=ComponentType.CHART,
        template="components/charts/bar_chart.html",
        styles=["/static/css/components/bar_chart.css"],
        scripts=["/static/js/components/bar_chart.js"],
        dependencies=["chart.js"],
        props={"type": "bar", "animation": True},
        lazy_load=True
    ))
    
    # 表格组件
    component_registry.register("data_table", ComponentConfig(
        name="数据表格",
        component_type=ComponentType.TABLE,
        template="components/tables/data_table.html",
        styles=["/static/css/components/data_table.css"],
        scripts=["/static/js/components/data_table.js"],
        props={"sortable": True, "filterable": True, "pagination": True},
        lazy_load=True
    ))
    
    # 表单组件
    component_registry.register("search_form", ComponentConfig(
        name="搜索表单",
        component_type=ComponentType.FORM,
        template="components/forms/search_form.html",
        styles=["/static/css/components/search_form.css"],
        scripts=["/static/js/components/search_form.js"],
        props={"submit_on_enter": True},
        lazy_load=False  # 搜索表单需要立即加载
    ))
    
    # 模态框组件
    component_registry.register("modal_dialog", ComponentConfig(
        name="模态对话框",
        component_type=ComponentType.MODAL,
        template="components/modals/modal_dialog.html",
        styles=["/static/css/components/modal_dialog.css"],
        scripts=["/static/js/components/modal_dialog.js"],
        props={"closable": True, "draggable": False},
        events=["open", "close", "confirm", "cancel"],
        lazy_load=True
    ))
    
    # 卡片组件
    component_registry.register("info_card", ComponentConfig(
        name="信息卡片",
        component_type=ComponentType.CARD,
        template="components/cards/info_card.html",
        styles=["/static/css/components/info_card.css"],
        scripts=["/static/js/components/info_card.js"],
        props={"collapsible": True, "refreshable": True},
        lazy_load=False
    ))


# 初始化默认组件
register_default_components()
