#!/usr/bin/env python3
"""
GUI Component Builder
YL-AR-DGN GUI Component Library
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ComponentType(Enum):
    """组件类型枚举"""
    BASIC = "basic"        # 基础组件
    CONTAINER = "container" # 容器组件
    ADVANCED = "advanced"   # 高级组件
    NAVIGATION = "navigation" # 导航组件
    DIALOG = "dialog"       # 对话框组件


@dataclass
class Component:
    """组件数据类"""
    name: str
    type: ComponentType
    description: str
    props: Dict[str, str] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class GUIComponentBuilder:
    """
    GUI组件库构建器
    
    提供组件库生成、文档创建和验证功能。
    """
    
    def __init__(self):
        """初始化组件库构建器"""
        self.components_dir = Path(__file__).parent.parent / "gui" / "components"
        self.output_dir = Path(__file__).parent.parent / "docs" / "project" / "gui-docs"
        
        # 组件库定义
        self.components: Dict[str, Component] = {}
        
        # 注册基础组件
        self._register_basic_components()
        
        # 注册容器组件
        self._register_container_components()
        
        # 注册高级组件
        self._register_advanced_components()
        
        # 注册导航组件
        self._register_navigation_components()
        
        # 注册对话框组件
        self._register_dialog_components()
    
    def _register_basic_components(self):
        """注册基础组件"""
        basic_components = [
            Component(
                name="Button",
                type=ComponentType.BASIC,
                description="按钮组件，支持多种类型和状态",
                props={
                    "text": "按钮文字",
                    "type": "primary | secondary | danger | text",
                    "size": "small | medium | large",
                    "disabled": "是否禁用",
                    "loading": "是否加载中",
                    "icon": "图标名称"
                },
                events=["click", "mousedown", "mouseup"],
                examples=[
                    '<Button type="primary">主要按钮</Button>',
                    '<Button type="danger" loading>删除</Button>'
                ],
                dependencies=["@qtpy/button"]
            ),
            Component(
                name="Input",
                type=ComponentType.BASIC,
                description="输入框组件，支持多种类型和验证",
                props={
                    "value": "输入值",
                    "placeholder": "占位文字",
                    "type": "text | password | number | email",
                    "disabled": "是否禁用",
                    "maxLength": "最大长度",
                    "allowClear": "是否允许清除"
                },
                events=["change", "focus", "blur", "pressEnter"],
                examples=[
                    '<Input placeholder="请输入" />',
                    '<Input.Password placeholder="请输入密码" />'
                ],
                dependencies=["@qtpy/input"]
            ),
            Component(
                name="Select",
                type=ComponentType.BASIC,
                description="下拉选择组件，支持单选和多选",
                props={
                    "value": "选中值",
                    "options": "选项列表",
                    "placeholder": "占位文字",
                    "disabled": "是否禁用",
                    "mode": "single | multiple",
                    "allowClear": "是否允许清除"
                },
                events=["change", "focus", "blur"],
                examples=[
                    '<Select options={options} placeholder="请选择" />'
                ],
                dependencies=["@qtpy/select"]
            ),
            Component(
                name="Checkbox",
                type=ComponentType.BASIC,
                description="复选框组件",
                props={
                    "checked": "是否选中",
                    "disabled": "是否禁用",
                    "indeterminate": "半选状态"
                },
                events=["change"],
                examples=[
                    '<Checkbox>选项</Checkbox>'
                ],
                dependencies=["@qtpy/checkbox"]
            ),
            Component(
                name="Radio",
                type=ComponentType.BASIC,
                description="单选框组件",
                props={
                    "value": "选中值",
                    "options": "选项列表",
                    "disabled": "是否禁用"
                },
                events=["change"],
                examples=[
                    '<Radio.Group options={options} />'
                ],
                dependencies=["@qtpy/radio"]
            ),
            Component(
                name="Switch",
                type=ComponentType.BASIC,
                description="开关组件",
                props={
                    "checked": "是否开启",
                    "disabled": "是否禁用",
                    "size": "small | default"
                },
                events=["change"],
                examples=[
                    '<Switch checked={value} onChange={handleChange} />'
                ],
                dependencies=["@qtpy/switch"]
            ),
            Component(
                name="Slider",
                type=ComponentType.BASIC,
                description="滑动输入组件",
                props={
                    "value": "当前值",
                    "min": "最小值",
                    "max": "最大值",
                    "step": "步长",
                    "disabled": "是否禁用"
                },
                events=["change", "afterChange"],
                examples=[
                    '<Slider min={0} max={100} />'
                ],
                dependencies=["@qtpy/slider"]
            ),
            Component(
                name="DatePicker",
                type=ComponentType.BASIC,
                description="日期选择组件",
                props={
                    "value": "选中日期",
                    "format": "日期格式",
                    "disabled": "是否禁用",
                    "showTime": "是否显示时间"
                },
                events=["change", "ok", "clear"],
                examples=[
                    '<DatePicker />',
                    '<RangePicker />'
                ],
                dependencies=["@qtpy/date-picker"]
            ),
            Component(
                name="Upload",
                type=ComponentType.BASIC,
                description="文件上传组件",
                props={
                    "action": "上传地址",
                    "accept": "接受文件类型",
                    "multiple": "是否多选",
                    "disabled": "是否禁用"
                },
                events=["change", "success", "error"],
                examples=[
                    '<Upload action="/api/upload">'
                ],
                dependencies=["@qtpy/upload"]
            ),
        ]
        
        for comp in basic_components:
            self.components[comp.name] = comp
    
    def _register_container_components(self):
        """注册容器组件"""
        container_components = [
            Component(
                name="Card",
                type=ComponentType.CONTAINER,
                description="卡片容器，用于组织和显示内容",
                props={
                    "title": "卡片标题",
                    "extra": "额外区域",
                    "bordered": "是否有边框",
                    "hoverable": "是否可悬停"
                },
                events=["click"],
                examples=[
                    '<Card title="标题">内容</Card>'
                ],
                dependencies=["@qtpy/card"]
            ),
            Component(
                name="Collapse",
                type=ComponentType.CONTAINER,
                description="折叠面板组件",
                props={
                    "accordion": "是否手风琴模式",
                    "expandIconPosition": "图标位置"
                },
                events=["change"],
                examples=[
                    '<Collapse items={items} />'
                ],
                dependencies=["@qtpy/collapse"]
            ),
            Component(
                name="Tabs",
                type=ComponentType.CONTAINER,
                description="标签页组件",
                props={
                    "type": "line | card | editable-card",
                    "size": "small | default | large",
                    "animated": "是否动画"
                },
                events=["change", "edit"],
                examples=[
                    '<Tabs items={items} />'
                ],
                dependencies=["@qtpy/tabs"]
            ),
            Component(
                name="List",
                type=ComponentType.CONTAINER,
                description="列表组件",
                props={
                    "dataSource": "数据源",
                    "renderItem": "渲染函数",
                    "grid": "网格配置",
                    "pagination": "分页配置"
                },
                events=["change"],
                examples=[
                    '<List dataSource={data} renderItem={renderItem} />'
                ],
                dependencies=["@qtpy/list"]
            ),
            Component(
                name="Table",
                type=ComponentType.CONTAINER,
                description="数据表格组件",
                props={
                    "columns": "列配置",
                    "dataSource": "数据源",
                    "pagination": "分页配置",
                    "rowKey": "行key"
                },
                events=["change", "rowClick", "expand"],
                examples=[
                    '<Table columns={columns} dataSource={data} />'
                ],
                dependencies=["@qtpy/table"]
            ),
        ]
        
        for comp in container_components:
            self.components[comp.name] = comp
    
    def _register_advanced_components(self):
        """注册高级组件"""
        advanced_components = [
            Component(
                name="Tree",
                type=ComponentType.ADVANCED,
                description="树形结构组件",
                props={
                    "treeData": "树数据",
                    "checkable": "是否可选择",
                    "expandedKeys": "展开的节点",
                    "selectedKeys": "选中的节点"
                },
                events=["expand", "select", "check"],
                examples=[
                    '<Tree treeData={treeData} checkable />'
                ],
                dependencies=["@qtpy/tree"]
            ),
            Component(
                name="Transfer",
                type=ComponentType.ADVANCED,
                description="穿梭框组件",
                props={
                    "dataSource": "数据源",
                    "targetKeys": "目标数据",
                    "selectedKeys": "选中数据"
                },
                events=["change", "search"],
                examples=[
                    '<Transfer dataSource={data} />'
                ],
                dependencies=["@qtpy/transfer"]
            ),
            Component(
                name="TreeSelect",
                type=ComponentType.ADVANCED,
                description="树形选择组件",
                props={
                    "treeData": "树数据",
                    "value": "选中值",
                    "treeCheckable": "是否可选择"
                },
                events=["change", "search"],
                examples=[
                    '<TreeSelect treeData={treeData} />'
                ],
                dependencies=["@qtpy/tree-select"]
            ),
        ]
        
        for comp in advanced_components:
            self.components[comp.name] = comp
    
    def _register_navigation_components(self):
        """注册导航组件"""
        navigation_components = [
            Component(
                name="Menu",
                type=ComponentType.NAVIGATION,
                description="导航菜单组件",
                props={
                    "mode": "vertical | horizontal | inline",
                    "selectedKeys": "选中的键",
                    "openKeys": "展开的子菜单"
                },
                events=["click", "openChange"],
                examples=[
                    '<Menu mode="vertical" items={items} />'
                ],
                dependencies=["@qtpy/menu"]
            ),
            Component(
                name="Breadcrumb",
                type=ComponentType.NAVIGATION,
                description="面包屑导航组件",
                props={
                    "items": "导航项列表",
                    "separator": "分隔符"
                },
                events=["click"],
                examples=[
                    '<Breadcrumb items={items} />'
                ],
                dependencies=["@qtpy/breadcrumb"]
            ),
            Component(
                name="Pagination",
                type=ComponentType.NAVIGATION,
                description="分页组件",
                props={
                    "current": "当前页",
                    "pageSize": "每页数量",
                    "total": "总数量",
                    "showSizeChanger": "显示数量选择"
                },
                events=["change", "showSizeChange"],
                examples=[
                    '<Pagination total={100} />'
                ],
                dependencies=["@qtpy/pagination"]
            ),
            Component(
                name="Steps",
                type=ComponentType.NAVIGATION,
                description="步骤条组件",
                props={
                    "current": "当前步骤",
                    "status": "wait | process | finish | error",
                    "type": "default | navigation"
                },
                events=["change"],
                examples=[
                    '<Steps items={items} current={1} />'
                ],
                dependencies=["@qtpy/steps"]
            ),
        ]
        
        for comp in navigation_components:
            self.components[comp.name] = comp
    
    def _register_dialog_components(self):
        """注册对话框组件"""
        dialog_components = [
            Component(
                name="Modal",
                type=ComponentType.DIALOG,
                description="模态对话框组件",
                props={
                    "open": "是否显示",
                    "title": "标题",
                    "footer": "底部内容",
                    "closable": "是否可关闭",
                    "maskClosable": "点击遮罩关闭"
                },
                events=["ok", "cancel", "close"],
                examples=[
                    '<Modal open={true} title="标题">内容</Modal>'
                ],
                dependencies=["@qtpy/modal"]
            ),
            Component(
                name="Message",
                type=ComponentType.DIALOG,
                description="全局提示组件",
                props={
                    "content": "提示内容",
                    "duration": "显示时长",
                    "type": "success | error | warning | info"
                },
                events=["close"],
                examples=[
                    'Message.success("操作成功")'
                ],
                dependencies=["@qtpy/message"]
            ),
            Component(
                name="Notification",
                type=ComponentType.DIALOG,
                description="通知提醒组件",
                props={
                    "message": "标题",
                    "description": "描述",
                    "duration": "显示时长",
                    "placement": "位置"
                },
                events=["close"],
                examples=[
                    'Notification.open({message: "标题", description: "描述"})'
                ],
                dependencies=["@qtpy/notification"]
            ),
            Component(
                name="Popconfirm",
                type=ComponentType.DIALOG,
                description="气泡确认框组件",
                props={
                    "title": "确认文字",
                    "okText": "确认按钮文字",
                    "cancelText": "取消按钮文字"
                },
                events=["confirm", "cancel"],
                examples=[
                    '<Popconfirm title="确定删除?">'
                ],
                dependencies=["@qtpy/popconfirm"]
            ),
            Component(
                name="Drawer",
                type=ComponentType.DIALOG,
                description="抽屉组件",
                props={
                    "open": "是否显示",
                    "placement": "位置",
                    "width": "宽度",
                    "height": "高度",
                    "closable": "是否可关闭"
                },
                events=["close", "afterOpenChange"],
                examples=[
                    '<Drawer open={true}>内容</Drawer>'
                ],
                dependencies=["@qtpy/drawer"]
            ),
        ]
        
        for comp in dialog_components:
            self.components[comp.name] = comp
    
    def generate_component_docs(self) -> str:
        """生成组件文档"""
        docs = f"""# GUI组件库文档

**项目:** YL-AR-DGN  
**版本:** 1.0.0  
**最后更新:** {datetime.now().strftime("%Y-%m-%d")}

---

## 概述

GUI组件库提供完整的用户界面组件，支持现代UI/UX设计规范。

## 组件统计

| 类型 | 数量 |
|------|------|
| 基础组件 | {len([c for c in self.components.values() if c.type == ComponentType.BASIC])} |
| 容器组件 | {len([c for c in self.components.values() if c.type == ComponentType.CONTAINER])} |
| 高级组件 | {len([c for c in self.components.values() if c.type == ComponentType.ADVANCED])} |
| 导航组件 | {len([c for c in self.components.values() if c.type == ComponentType.NAVIGATION])} |
| 对话框组件 | {len([c for c in self.components.values() if c.type == ComponentType.DIALOG])} |
| **总计** | {len(self.components)} |

---

## 基础组件

"""
        
        # 基础组件
        for comp in [c for c in self.components.values() if c.type == ComponentType.BASIC]:
            docs += self._generate_component_section(comp)
        
        docs += """
## 容器组件

"""
        
        # 容器组件
        for comp in [c for c in self.components.values() if c.type == ComponentType.CONTAINER]:
            docs += self._generate_component_section(comp)
        
        docs += """
## 导航组件

"""
        
        # 导航组件
        for comp in [c for c in self.components.values() if c.type == ComponentType.NAVIGATION]:
            docs += self._generate_component_section(comp)
        
        docs += """
## 对话框组件

"""
        
        # 对话框组件
        for comp in [c for c in self.components.values() if c.type == ComponentType.DIALOG]:
            docs += self._generate_component_section(comp)
        
        return docs
    
    def _generate_component_section(self, comp: Component) -> str:
        """生成组件文档章节"""
        section = f"""### {comp.name}

**类型:** {comp.type.value}  
**描述:** {comp.description}

#### 属性

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
"""
        
        for prop, desc in comp.props.items():
            section += f"| {prop} | any | - | {desc} |\n"
        
        section += """
#### 事件

"""
        
        for event in comp.events:
            section += f"- `{event}`\n"
        
        section += """
#### 示例

"""
        
        for example in comp.examples:
            section += f"```jsx\n{example}\n```\n"
        
        section += """
#### 依赖

"""
        
        for dep in comp.dependencies:
            section += f"- `{dep}`\n"
        
        section += "\n---\n"
        
        return section
    
    def generate_component_index(self) -> Dict[str, Any]:
        """生成组件索引"""
        index = {
            "version": "1.0.0",
            "generated": datetime.now().isoformat(),
            "total_components": len(self.components),
            "categories": {},
            "components": []
        }
        
        # 按类别分组
        for comp in self.components.values():
            type_name = comp.type.value
            if type_name not in index["categories"]:
                index["categories"][type_name] = []
            
            index["categories"][type_name].append({
                "name": comp.name,
                "description": comp.description,
                "props_count": len(comp.props),
                "events_count": len(comp.events),
                "dependencies": comp.dependencies
            })
            
            index["components"].append({
                "name": comp.name,
                "type": type_name,
                "description": comp.description,
                "props": list(comp.props.keys()),
                "events": comp.events,
                "examples": comp.examples,
                "dependencies": comp.dependencies
            })
        
        return index
    
    def save_docs(self):
        """保存组件文档"""
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成并保存文档
        docs = self.generate_component_docs()
        docs_path = self.output_dir / "component-library.md"
        docs_path.write_text(docs, encoding='utf-8')
        print(f"✅ 组件文档已生成: {docs_path}")
        
        # 生成索引
        index = self.generate_component_index()
        index_path = self.output_dir / "component-index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        print(f"✅ 组件索引已生成: {index_path}")
        
        return {
            "docs": str(docs_path),
            "index": str(index_path)
        }


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GUI组件库构建器")
    parser.add_argument("--generate", action="store_true", help="生成组件文档")
    parser.add_argument("--index", action="store_true", help="生成组件索引")
    parser.add_argument("--all", action="store_true", help="生成所有")
    
    args = parser.parse_args()
    
    builder = GUIComponentBuilder()
    
    if args.generate or args.all:
        builder.save_docs()
    
    if args.index or args.all:
        index = builder.generate_component_index()
        print(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
