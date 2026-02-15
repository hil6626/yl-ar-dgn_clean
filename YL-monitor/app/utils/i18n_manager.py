"""
国际化管理器 (I18n Manager)
实现中文化说明注解的统一管理
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path


class Language(Enum):
    """支持的语言"""
    ZH_CN = "zh_CN"  # 简体中文
    ZH_TW = "zh_TW"  # 繁体中文
    EN = "en"        # 英文
    JA = "ja"        # 日文


@dataclass
class TermDefinition:
    """术语定义"""
    term: str                    # 术语原文
    translation: str             # 翻译
    category: str                # 分类
    description: str             # 详细说明
    examples: List[str] = field(default_factory=list)
    related_terms: List[str] = field(default_factory=list)


@dataclass
class MessageTemplate:
    """消息模板"""
    key: str                     # 模板键
    template: str                # 模板内容
    category: str                # 分类
    variables: List[str] = field(default_factory=list)
    description: str = ""


class I18nManager:
    """
    国际化管理器
    
    功能：
    1. 术语表管理
    2. 消息模板管理
    3. 多语言支持
    4. 注释规范检查
    """
    
    def __init__(self, locale: Language = Language.ZH_CN):
        self.locale = locale
        self._terms: Dict[str, TermDefinition] = {}
        self._templates: Dict[str, MessageTemplate] = {}
        self._translations: Dict[str, Dict[str, str]] = {}
        self._comment_standards: Dict[str, str] = {}
        
        # 加载默认术语表
        self._load_default_terms()
        self._load_default_templates()
        self._load_comment_standards()
    
    def _load_default_terms(self) -> None:
        """加载默认术语表"""
        default_terms = [
            TermDefinition(
                term="DAG",
                translation="有向无环图",
                category="技术术语",
                description="Directed Acyclic Graph，用于任务调度和依赖管理",
                examples=["DAG 流水线", "DAG 节点"],
                related_terms=["Node", "Edge", "Pipeline"]
            ),
            TermDefinition(
                term="AR",
                translation="增强现实",
                category="技术术语",
                description="Augmented Reality，将虚拟信息叠加到现实世界",
                examples=["AR 监控", "AR 节点"],
                related_terms=["VR", "MR", "3D"]
            ),
            TermDefinition(
                term="Script",
                translation="脚本",
                category="功能术语",
                description="可执行的自动化程序",
                examples=["监控脚本", "清理脚本"],
                related_terms=["Task", "Job", "Process"]
            ),
            TermDefinition(
                term="Monitor",
                translation="监控",
                category="功能术语",
                description="实时监测系统状态和性能指标",
                examples=["系统监控", "资源监控"],
                related_terms=["Alert", "Metric", "Dashboard"]
            ),
            TermDefinition(
                term="Alert",
                translation="告警",
                category="功能术语",
                description="当系统异常时发送的通知",
                examples=["阈值告警", "异常告警"],
                related_terms=["Notification", "Warning", "Error"]
            ),
            TermDefinition(
                term="Node",
                translation="节点",
                category="架构术语",
                description="系统中的单个处理单元",
                examples=["DAG 节点", "AR 节点"],
                related_terms=["Cluster", "Instance", "Server"]
            ),
            TermDefinition(
                term="Pipeline",
                translation="流水线",
                category="架构术语",
                description="按顺序执行的一系列任务",
                examples=["数据处理流水线", "部署流水线"],
                related_terms=["Workflow", "Stage", "Step"]
            ),
            TermDefinition(
                term="WebSocket",
                translation="WebSocket",
                category="技术术语",
                description="全双工通信协议，用于实时数据推送",
                examples=["WebSocket 连接", "WebSocket 消息"],
                related_terms=["HTTP", "TCP", "Real-time"]
            ),
            TermDefinition(
                term="Cache",
                translation="缓存",
                category="技术术语",
                description="临时存储数据以提高访问速度",
                examples=["页面缓存", "数据缓存"],
                related_terms=["Buffer", "Storage", "Memory"]
            ),
            TermDefinition(
                term="Lazy Load",
                translation="懒加载",
                category="技术术语",
                description="按需加载资源，减少初始加载时间",
                examples=["图片懒加载", "组件懒加载"],
                related_terms=["Preload", "Async", "Defer"]
            ),
        ]
        
        for term in default_terms:
            self._terms[term.term] = term
    
    def _load_default_templates(self) -> None:
        """加载默认消息模板"""
        templates = [
            MessageTemplate(
                key="script.started",
                template="脚本 {script_name} 已开始执行",
                category="脚本执行",
                variables=["script_name"],
                description="脚本开始执行时的通知消息"
            ),
            MessageTemplate(
                key="script.completed",
                template="脚本 {script_name} 执行完成，耗时 {duration} 秒",
                category="脚本执行",
                variables=["script_name", "duration"],
                description="脚本执行完成时的通知消息"
            ),
            MessageTemplate(
                key="script.failed",
                template="脚本 {script_name} 执行失败：{error}",
                category="脚本执行",
                variables=["script_name", "error"],
                description="脚本执行失败时的错误消息"
            ),
            MessageTemplate(
                key="dag.node.started",
                template="DAG {dag_id} 节点 {node_id} 开始执行",
                category="DAG执行",
                variables=["dag_id", "node_id"],
                description="DAG节点开始执行时的通知"
            ),
            MessageTemplate(
                key="dag.node.completed",
                template="DAG {dag_id} 节点 {node_id} 执行完成",
                category="DAG执行",
                variables=["dag_id", "node_id"],
                description="DAG节点执行完成时的通知"
            ),
            MessageTemplate(
                key="alert.triggered",
                template="告警触发：{alert_name} - {message}",
                category="告警通知",
                variables=["alert_name", "message"],
                description="告警触发时的通知消息"
            ),
            MessageTemplate(
                key="system.error",
                template="系统错误：{component} - {error}",
                category="系统错误",
                variables=["component", "error"],
                description="系统发生错误时的消息"
            ),
            MessageTemplate(
                key="api.success",
                template="操作成功：{action}",
                category="API响应",
                variables=["action"],
                description="API操作成功时的响应消息"
            ),
            MessageTemplate(
                key="api.error",
                template="操作失败：{action} - {reason}",
                category="API响应",
                variables=["action", "reason"],
                description="API操作失败时的响应消息"
            ),
        ]
        
        for template in templates:
            self._templates[template.key] = template
    
    def _load_comment_standards(self) -> None:
        """加载注释规范"""
        self._comment_standards = {
            "file_header": """文件头部注释规范：
/**
 * 文件名: {filename}
 * 功能描述: {description}
 * 作者: {author}
 * 创建时间: {created_at}
 * 最后更新: {updated_at}
 * 版本: {version}
 */""",
            
            "function_docstring": """函数/方法注释规范：
def function_name(param1: type, param2: type) -> return_type:
    \\\"\\\"\\\"
    函数简要说明（一句话）
    
    详细说明（多行，可选）
    
    参数:
        param1: 参数1说明
        param2: 参数2说明
    
    返回:
        返回值说明
    
    异常:
        ExceptionType: 异常说明
    
    示例:
        >>> function_name(value1, value2)
        result
    
    注意:
        - 注意事项1
        - 注意事项2
    \\\"\\\"\\\"
    pass""",
            
            "class_docstring": """类注释规范：
class ClassName(BaseClass):
    \\\"\\\"\\\"
    类简要说明
    
    详细说明（可选）
    
    属性:
        attr1: 属性1说明
        attr2: 属性2说明
    
    方法:
        method1: 方法1说明
        method2: 方法2说明
    
    示例:
        >>> obj = ClassName()
        >>> obj.method1()
    \\\"\\\"\\\"
    pass""",
            
            "inline_comment": """行内注释规范：
# 简短说明（与代码同行，#后加空格）
code = value  # 这是行内注释

# 块注释（独立成行，用于解释代码块）
# 以下代码用于处理用户输入验证
# 包括格式检查、长度限制、特殊字符过滤
validated_input = validate_input(user_input)""",
            
            "todo_comment": """TODO注释规范：
# TODO: 待办事项说明
# FIXME: 需要修复的问题
# HACK: 临时解决方案，需要优化
# NOTE: 重要说明或注意事项
# WARNING: 警告信息""",
        }
    
    def get_term(self, term: str) -> Optional[TermDefinition]:
        """获取术语定义"""
        return self._terms.get(term)
    
    def add_term(self, term: TermDefinition) -> None:
        """添加术语"""
        self._terms[term.term] = term
    
    def list_terms(self, category: Optional[str] = None) -> List[TermDefinition]:
        """列出术语"""
        if category:
            return [t for t in self._terms.values() if t.category == category]
        return list(self._terms.values())
    
    def get_template(self, key: str, **kwargs) -> str:
        """获取消息模板"""
        template = self._templates.get(key)
        if template:
            try:
                return template.template.format(**kwargs)
            except KeyError as e:
                return f"模板渲染错误: 缺少变量 {e}"
        return f"未知模板: {key}"
    
    def add_template(self, template: MessageTemplate) -> None:
        """添加消息模板"""
        self._templates[template.key] = template
    
    def get_comment_standard(self, standard_type: str) -> str:
        """获取注释规范"""
        return self._comment_standards.get(standard_type, "未知规范类型")
    
    def validate_comment(self, comment: str, comment_type: str) -> Dict[str, Any]:
        """验证注释是否符合规范"""
        result = {
            "valid": True,
            "issues": [],
            "suggestions": []
        }
        
        # 基本检查
        if not comment.strip():
            result["valid"] = False
            result["issues"].append("注释为空")
            return result
        
        # 根据类型进行特定检查
        if comment_type == "file_header":
            required_fields = ["文件名", "功能描述", "作者"]
            for field in required_fields:
                if field not in comment:
                    result["issues"].append(f"缺少必要字段: {field}")
        
        elif comment_type == "function_docstring":
            # 检查是否包含必要章节
            required_sections = ["参数", "返回"]
            for section in required_sections:
                if section not in comment:
                    result["suggestions"].append(f"建议添加 '{section}' 章节")
        
        # 通用检查
        if "#TODO" in comment or "#FIXME" in comment:
            if "日期" not in comment and "负责人" not in comment:
                result["suggestions"].append("TODO/FIXME 建议添加日期和负责人信息")
        
        result["valid"] = len(result["issues"]) == 0
        return result
    
    def generate_glossary(self, format: str = "markdown") -> str:
        """生成术语表文档"""
        terms = sorted(self._terms.values(), key=lambda t: t.category)
        
        if format == "markdown":
            lines = ["# YL-Monitor 术语表\n"]
            current_category = None
            
            for term in terms:
                if term.category != current_category:
                    current_category = term.category
                    lines.append(f"\n## {current_category}\n")
                
                lines.append(f"### {term.term}")
                lines.append(f"**中文**: {term.translation}\n")
                lines.append(f"{term.description}\n")
                
                if term.examples:
                    lines.append("**示例**:")
                    for example in term.examples:
                        lines.append(f"- {example}")
                    lines.append("")
                
                if term.related_terms:
                    lines.append(f"**相关术语**: {', '.join(term.related_terms)}\n")
            
            return "\n".join(lines)
        
        elif format == "json":
            return json.dumps(
                {k: {
                    "translation": v.translation,
                    "category": v.category,
                    "description": v.description,
                    "examples": v.examples,
                    "related_terms": v.related_terms
                } for k, v in self._terms.items()},
                ensure_ascii=False,
                indent=2
            )
        
        return "不支持的格式"
    
    def export_to_file(self, filepath: str, format: str = "markdown") -> bool:
        """导出术语表到文件"""
        try:
            content = self.generate_glossary(format)
            Path(filepath).write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False


# 全局国际化管理器实例
i18n_manager = I18nManager(locale=Language.ZH_CN)


# 便捷函数
def get_term(term: str) -> Optional[TermDefinition]:
    """获取术语定义"""
    return i18n_manager.get_term(term)


def t(key: str, **kwargs) -> str:
    """获取翻译后的消息"""
    return i18n_manager.get_template(key, **kwargs)


def validate_docstring(docstring: str, doc_type: str = "function") -> Dict[str, Any]:
    """验证文档字符串"""
    return i18n_manager.validate_comment(docstring, f"{doc_type}_docstring")
