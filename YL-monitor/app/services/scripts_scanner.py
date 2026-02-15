"""
脚本扫描器服务
自动扫描 scripts 目录，识别和分类所有脚本
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ScriptMetadata:
    """脚本元数据"""
    id: str
    name: str
    filename: str
    category: str
    subcategory: str
    description: str
    path: str
    script_type: str  # python, shell, etc.
    tags: List[str] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    schedule: Optional[str] = None
    timeout: int = 300
    enabled: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ScriptsScanner:
    """
    脚本扫描器
    
    自动扫描 YL-monitor/scripts 目录，按功能分类所有脚本
    """
    
    # 脚本分类映射
    CATEGORIES = {
        "monitors/system": {
            "id": "system-monitor",
            "name": "系统监控",
            "icon": "🔍",
            "description": "CPU、内存、磁盘、系统负载监控"
        },
        "monitors/service": {
            "id": "service-monitor", 
            "name": "服务监控",
            "icon": "🌐",
            "description": "端口、网络、API、Web应用监控"
        },
        "monitors/ar": {
            "id": "ar-monitor",
            "name": "AR监控",
            "icon": "🎥",
            "description": "AR节点资源监控"
        },
        "optimizers/resource": {
            "id": "resource-optimizer",
            "name": "资源优化",
            "icon": "🧹",
            "description": "磁盘清理、缓存清理、日志轮转"
        },
        "optimizers/service": {
            "id": "service-optimizer",
            "name": "服务优化",
            "icon": "⚡",
            "description": "进程调度、内存泄漏检测、负载均衡"
        },
        "maintenance/backup": {
            "id": "maintenance-backup",
            "name": "维护备份",
            "icon": "💾",
            "description": "文件备份、日志归档、数据压缩"
        },
        "maintenance/health": {
            "id": "maintenance-health",
            "name": "维护健康",
            "icon": "🏥",
            "description": "状态监控、巡检报告、配置检查"
        },
        "maintenance/cleanup": {
            "id": "maintenance-cleanup",
            "name": "维护清理",
            "icon": "🧽",
            "description": "系统清理和垃圾回收"
        },
        "alerts": {
            "id": "alert-handler",
            "name": "告警处理",
            "icon": "🚨",
            "description": "告警处理器和通知器"
        },
        "utils": {
            "id": "tools",
            "name": "工具脚本",
            "icon": "🛠️",
            "description": "CSS管理、开发工具、验证工具"
        },
        "core": {
            "id": "core",
            "name": "核心脚本",
            "icon": "🔧",
            "description": "启动和验证脚本"
        }
    }
    
    def __init__(self, scripts_dir: str = "scripts"):
        self.scripts_dir = Path(scripts_dir)
        self.scripts: Dict[str, ScriptMetadata] = {}
        self._cache_file = Path("data/script_metadata_cache.json")
    
    def scan_all(self) -> List[ScriptMetadata]:
        """
        扫描所有脚本
        """
        self.scripts = {}
        
        # 确保目录存在
        if not self.scripts_dir.exists():
            print(f"脚本目录不存在: {self.scripts_dir}")
            return []
        
        # 扫描各分类目录
        for category_path, category_info in self.CATEGORIES.items():
            full_path = self.scripts_dir / category_path
            if full_path.exists():
                self._scan_category(full_path, category_info)
        
        # 扫描根目录的独立脚本
        self._scan_root_scripts()
        
        # 保存缓存
        self._save_cache()
        
        return list(self.scripts.values())
    
    def _scan_category(self, path: Path, category_info: Dict[str, Any]):
        """
        扫描特定分类目录
        """
        for file_path in path.rglob("*"):
            if file_path.is_file() and self._is_script(file_path):
                script = self._parse_script(file_path, category_info)
                if script:
                    self.scripts[script.id] = script
    
    def _scan_root_scripts(self):
        """
        扫描根目录的脚本
        """
        root_scripts = [
            ("backup.sh", "maintenance-backup", "系统备份脚本"),
            ("cleanup_duplicate_files.py", "maintenance-cleanup", "重复文件清理"),
            ("cleanup_old_files.sh", "maintenance-cleanup", "旧文件清理"),
            ("docker_build.sh", "tools", "Docker构建"),
            ("docker_start.sh", "tools", "Docker启动"),
            ("docker_stop.sh", "tools", "Docker停止"),
            ("optimize_project_structure.py", "tools", "项目结构优化"),
            ("run_all_monitors.sh", "system-monitor", "运行所有监控"),
            ("setup_vscode_testing.sh", "tools", "VSCode测试环境"),
            ("simple_alert_test.py", "alert-handler", "简单告警测试"),
            ("test_alert_system.py", "alert-handler", "告警系统测试"),
        ]
        
        for filename, category_id, description in root_scripts:
            file_path = self.scripts_dir / filename
            if file_path.exists():
                category_info = self._get_category_by_id(category_id)
                script = self._parse_script(file_path, category_info)
                if script:
                    script.description = description
                    self.scripts[script.id] = script
    
    def _is_script(self, path: Path) -> bool:
        """
        检查文件是否为脚本
        """
        script_extensions = {'.py', '.sh', '.bash', '.zsh'}
        return path.suffix.lower() in script_extensions
    
    def _parse_script(self, file_path: Path, category_info: Dict[str, Any]) -> Optional[ScriptMetadata]:
        """
        解析脚本文件，提取元数据
        """
        try:
            # 读取文件内容
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # 提取文件名信息
            filename = file_path.name
            script_type = self._get_script_type(file_path)
            
            # 生成脚本ID
            script_id = self._generate_script_id(file_path, category_info)
            
            # 提取描述信息
            description = self._extract_description(content, filename)
            
            # 提取参数信息
            parameters = self._extract_parameters(content)
            
            # 提取标签
            tags = self._extract_tags(content, category_info)
            
            # 检查是否有定时调度配置
            schedule = self._extract_schedule(content)
            
            return ScriptMetadata(
                id=script_id,
                name=self._format_name(filename),
                filename=filename,
                category=category_info["id"],
                subcategory=category_info.get("subcategory", ""),
                description=description,
                path=str(file_path.relative_to(self.scripts_dir.parent)),
                script_type=script_type,
                tags=tags,
                parameters=parameters,
                schedule=schedule,
                timeout=300,
                enabled=True
            )
            
        except Exception as e:
            print(f"解析脚本失败 {file_path}: {e}")
            return None
    
    def _get_script_type(self, path: Path) -> str:
        """
        获取脚本类型
        """
        ext = path.suffix.lower()
        type_map = {
            '.py': 'python',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell'
        }
        return type_map.get(ext, 'unknown')
    
    def _generate_script_id(self, file_path: Path, category_info: Dict[str, Any]) -> str:
        """
        生成脚本唯一ID
        """
        # 使用分类和文件名生成ID
        relative_path = file_path.relative_to(self.scripts_dir)
        path_parts = list(relative_path.parts)
        
        # 移除数字前缀（如 01_, 02_）
        clean_parts = []
        for part in path_parts:
            clean_part = re.sub(r'^\d+_', '', part)
            clean_parts.append(clean_part)
        
        # 生成ID
        script_id = "_".join(clean_parts)
        script_id = script_id.replace("/", "_").replace(".", "_")
        script_id = re.sub(r'_+', '_', script_id)  # 合并多个下划线
        script_id = script_id.strip('_')
        
        return f"{category_info['id']}_{script_id}"
    
    def _extract_description(self, content: str, filename: str) -> str:
        """
        从脚本内容提取描述
        """
        # 尝试提取文档字符串
        patterns = [
            r'"""(.*?)"""',  # Python 三引号
            r"'''(.*?)'''",  # Python 三单引号
            r'# (.*)\n',      # Shell 注释
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                desc = match.group(1).strip()
                # 只取第一行或前100字符
                first_line = desc.split('\n')[0].strip()
                return first_line[:200]
        
        # 如果没有文档字符串，从文件名生成描述
        name = filename.replace('_', ' ').replace('.py', '').replace('.sh', '')
        return f"脚本: {name}"
    
    def _extract_parameters(self, content: str) -> List[Dict[str, Any]]:
        """
        提取脚本参数信息
        """
        parameters = []
        
        # 匹配 argparse 参数定义
        arg_patterns = [
            r'add_argument\([\'"](.*?)[\'"],\s*.*?help=[\'"](.*?)[\'"]',
            r'add_argument\([\'"](.*?)[\'"].*?\)',
        ]
        
        for pattern in arg_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    param_name, help_text = match
                else:
                    param_name = match
                    help_text = ""
                
                parameters.append({
                    "name": param_name.lstrip('-'),
                    "type": "string",
                    "required": False,
                    "description": help_text,
                    "default": None
                })
        
        return parameters
    
    def _extract_tags(self, content: str, category_info: Dict[str, Any]) -> List[str]:
        """
        提取标签
        """
        tags = [category_info["id"]]
        
        # 从内容中提取关键词
        keywords = {
            "monitor": ["监控", "采集", "指标", "性能"],
            "alert": ["告警", "通知", "报警", "预警"],
            "cleanup": ["清理", "删除", "释放", "回收"],
            "backup": ["备份", "归档", "保存", "存储"],
            "optimize": ["优化", "加速", "提升", "调优"],
            "check": ["检查", "检测", "验证", "诊断"],
        }
        
        for tag, keywords_list in keywords.items():
            for keyword in keywords_list:
                if keyword in content or keyword in category_info.get("description", ""):
                    if tag not in tags:
                        tags.append(tag)
                    break
        
        return tags
    
    def _extract_schedule(self, content: str) -> Optional[str]:
        """
        提取定时调度配置
        """
        # 匹配 cron 表达式或调度配置
        schedule_patterns = [
            r'schedule\s*=\s*[\'"](.*?)[\'"]',
            r'cron\s*:\s*[\'"](.*?)[\'"]',
            r'interval\s*:\s*(\d+)',
        ]
        
        for pattern in schedule_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    
    def _format_name(self, filename: str) -> str:
        """
        格式化脚本名称
        """
        # 移除扩展名
        name = filename.replace('.py', '').replace('.sh', '')
        
        # 移除数字前缀
        name = re.sub(r'^\d+_', '', name)
        
        # 替换下划线为空格
        name = name.replace('_', ' ')
        
        # 首字母大写
        return name.title()
    
    def _get_category_by_id(self, category_id: str) -> Dict[str, Any]:
        """
        根据ID获取分类信息
        """
        for cat_path, cat_info in self.CATEGORIES.items():
            if cat_info["id"] == category_id:
                return cat_info
        
        return {
            "id": category_id,
            "name": "未分类",
            "icon": "📄",
            "description": "未分类脚本"
        }
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        获取所有分类信息
        """
        categories = []
        for cat_path, cat_info in self.CATEGORIES.items():
            # 统计该分类下的脚本数量
            count = sum(1 for s in self.scripts.values() if s.category == cat_info["id"])
            
            cat_data = {
                **cat_info,
                "script_count": count,
                "path": cat_path
            }
            categories.append(cat_data)
        
        # 按脚本数量排序
        categories.sort(key=lambda x: x["script_count"], reverse=True)
        return categories
    
    def get_scripts_by_category(self, category_id: str) -> List[ScriptMetadata]:
        """
        获取指定分类的脚本
        """
        return [s for s in self.scripts.values() if s.category == category_id]
    
    def get_script(self, script_id: str) -> Optional[ScriptMetadata]:
        """
        获取单个脚本信息
        """
        return self.scripts.get(script_id)
    
    def _save_cache(self):
        """
        保存缓存到文件
        """
        try:
            cache_data = {
                "scripts": {k: asdict(v) for k, v in self.scripts.items()},
                "categories": self.get_categories()
            }
            
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def load_cache(self) -> bool:
        """
        从缓存加载
        """
        try:
            if not self._cache_file.exists():
                return False
            
            with open(self._cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 恢复脚本数据
            for script_id, script_data in cache_data.get("scripts", {}).items():
                self.scripts[script_id] = ScriptMetadata(**script_data)
            
            return True
            
        except Exception as e:
            print(f"加载缓存失败: {e}")
            return False


# 全局扫描器实例
_scripts_scanner: Optional[ScriptsScanner] = None


def get_scripts_scanner(scripts_dir: str = "scripts") -> ScriptsScanner:
    """
    获取脚本扫描器实例（单例）
    """
    global _scripts_scanner
    if _scripts_scanner is None:
        _scripts_scanner = ScriptsScanner(scripts_dir)
    return _scripts_scanner
