#!/usr/bin/env python3
"""
Postman 集合与 REST Client 配置同步工具
自动将 Postman 集合转换为 REST Client .http 文件

功能特性：
- 自动解析 Postman 集合 JSON
- 生成标准 REST Client .http 文件
- 支持环境变量替换
- 保持请求顺序和分组结构
- 自动生成请求注释和命名
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class PostmanToRestClientConverter:
    """Postman 集合到 REST Client 转换器"""
    
    def __init__(self, collection_path: str, output_path: str, environment_path: Optional[str] = None):
        self.collection_path = Path(collection_path)
        self.output_path = Path(output_path)
        self.environment_path = Path(environment_path) if environment_path else None
        self.base_url = "http://0.0.0.0:5500"
        self.environment_vars = {}
        self.request_counter = 0
        
    def load_collection(self) -> Dict[str, Any]:
        """加载 Postman 集合"""
        try:
            with open(self.collection_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ 错误: 找不到 Postman 集合文件: {self.collection_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ 错误: JSON 解析失败: {e}")
            sys.exit(1)
    
    def load_environment(self) -> Dict[str, Any]:
        """加载 Postman 环境配置"""
        if not self.environment_path or not self.environment_path.exists():
            return {}
        
        try:
            with open(self.environment_path, 'r', encoding='utf-8') as f:
                env_data = json.load(f)
                # 转换为键值对字典
                values = env_data.get('values', [])
                return {item['key']: item['value'] for item in values if item.get('enabled', True)}
        except Exception as e:
            print(f"⚠️ 警告: 加载环境配置失败: {e}")
            return {}
    
    def replace_variables(self, text: str) -> str:
        """替换 Postman 变量为实际值"""
        if not text:
            return text
        
        # 替换 {{variable}} 格式
        def replace_var(match):
            var_name = match.group(1)
            if var_name in self.environment_vars:
                return self.environment_vars[var_name]
            # 保留为 REST Client 变量格式
            return f"{{{{{var_name}}}}}"
        
        return re.sub(r'\{\{(\w+)\}\}', replace_var, text)
    
    def convert_headers(self, headers: List[Dict[str, Any]]) -> List[str]:
        """转换请求头"""
        header_lines = []
        essential_headers = {'Accept', 'Content-Type'}
        
        for header in headers:
            key = header.get('key', '')
            value = header.get('value', '')
            
            if key and value:
                value = self.replace_variables(value)
                header_lines.append(f"{key}: {value}")
                essential_headers.discard(key)
        
        # 添加默认的必要请求头
        if 'Accept' in essential_headers:
            header_lines.append("Accept: application/json")
        if 'Content-Type' in essential_headers:
            header_lines.append("Content-Type: application/json")
        
        return header_lines
    
    def convert_body(self, body: Dict[str, Any]) -> str:
        """转换请求体"""
        if not body:
            return ""
        
        mode = body.get('mode', '')
        
        if mode == 'raw':
            raw_body = body.get('raw', '')
            # 替换变量
            raw_body = self.replace_variables(raw_body)
            return raw_body
        
        elif mode == 'urlencoded':
            params = body.get('urlencoded', [])
            if params:
                pairs = []
                for param in params:
                    key = param.get('key', '')
                    value = param.get('value', '')
                    if key:
                        value = self.replace_variables(value)
                        pairs.append(f"{key}={value}")
                return "&".join(pairs)
        
        elif mode == 'formdata':
            # 表单数据简化处理
            return "# [表单数据 - 请在 REST Client 中手动配置]"
        
        return ""
    
    def convert_url(self, url_data: Any) -> str:
        """转换 URL"""
        if isinstance(url_data, str):
            return self.replace_variables(url_data)
        
        if isinstance(url_data, dict):
            # 优先使用 raw
            raw_url = url_data.get('raw', '')
            if raw_url:
                return self.replace_variables(raw_url)
            
            # 构建 URL
            protocol = url_data.get('protocol', 'http')
            host_parts = url_data.get('host', [])
            if isinstance(host_parts, list):
                host = ".".join(host_parts)
            else:
                host = str(host_parts)
            
            port = url_data.get('port', '')
            path_parts = url_data.get('path', [])
            if isinstance(path_parts, list):
                path = "/".join(path_parts)
            else:
                path = str(path_parts)
            
            # 处理查询参数
            query = url_data.get('query', [])
            query_str = ""
            if query:
                params = []
                for q in query:
                    key = q.get('key', '')
                    value = q.get('value', '')
                    if key:
                        value = self.replace_variables(value)
                        params.append(f"{key}={value}")
                if params:
                    query_str = "?" + "&".join(params)
            
            full_url = f"{protocol}://{host}"
            if port:
                full_url += f":{port}"
            full_url += f"/{path}{query_str}"
            
            return self.replace_variables(full_url)
        
        return ""
    
    def convert_request(self, item: Dict[str, Any], folder_name: str = "") -> str:
        """转换单个请求"""
        self.request_counter += 1
        request = item.get('request', {})
        name = item.get('name', f'请求 {self.request_counter}')
        
        method = request.get('method', 'GET')
        url_data = request.get('url', {})
        url = self.convert_url(url_data)
        
        # 如果没有协议，添加 base_url
        if not url.startswith('http'):
            url = f"{self.base_url}{url}"
        
        # 转换请求头
        headers = request.get('header', [])
        header_lines = self.convert_headers(headers)
        
        # 转换请求体
        body = request.get('body', {})
        body_content = self.convert_body(body)
        
        # 生成请求名称（用于 REST Client 变量引用）
        request_name = self.generate_request_name(name)
        
        # 组装请求
        lines = []
        lines.append(f"### {self.request_counter}. {name}")
        if folder_name:
            lines.append(f"# 所属模块: {folder_name}")
        
        # 添加 REST Client 变量名注释
        lines.append(f"# @name {request_name}")
        
        # 请求行
        lines.append(f"{method} {url}")
        
        # 请求头
        lines.extend(header_lines)
        
        # 请求体
        if body_content:
            lines.append('')
            lines.append(body_content)
        
        lines.append('')
        lines.append('')
        
        return '\n'.join(lines)
    
    def generate_request_name(self, name: str) -> str:
        """生成请求变量名"""
        # 转换为小写，替换空格和特殊字符
        clean_name = re.sub(r'[^\w\s]', '', name.lower())
        clean_name = re.sub(r'\s+', '_', clean_name)
        # 限制长度
        if len(clean_name) > 50:
            clean_name = clean_name[:50]
        return clean_name
    
    def process_items(self, items: List[Dict[str, Any]], level: int = 0) -> str:
        """处理请求项列表"""
        result = []
        
        for item in items:
            if 'item' in item:
                # 这是一个文件夹/分组
                folder_name = item.get('name', '未命名分组')
                separator = '=' * (20 - level * 2)
                
                result.append(f"### {separator} {folder_name} {separator}")
                result.append('')
                
                # 递归处理子项
                sub_items = self.process_items(item['item'], level + 1)
                result.append(sub_items)
            else:
                # 这是一个请求
                folder_name = item.get('__folder_name', '')
                request_str = self.convert_request(item, folder_name)
                result.append(request_str)
        
        return '\n'.join(result)
    
    def flatten_items(self, items: List[Dict[str, Any]], folder_name: str = "") -> List[Dict[str, Any]]:
        """扁平化项目列表，添加文件夹名称"""
        result = []
        
        for item in items:
            if 'item' in item:
                # 递归处理子文件夹
                sub_folder = item.get('name', '')
                sub_items = self.flatten_items(item['item'], sub_folder)
                result.extend(sub_items)
            else:
                # 添加文件夹名称到请求
                item['__folder_name'] = folder_name
                result.append(item)
        
        return result
    
    def convert(self) -> str:
        """执行转换"""
        collection = self.load_collection()
        self.environment_vars = self.load_environment()
        
        # 获取集合信息
        info = collection.get('info', {})
        collection_name = info.get('name', 'Unknown Collection')
        
        # 生成文件头
        header_lines = [
            "### 配置说明",
            f"# 自动生成自 Postman 集合: {collection_name}",
            f"# 生成时间: {self.get_timestamp()}",
            f"# 源文件: {self.collection_path}",
        ]
        
        if self.environment_path and self.environment_path.exists():
            header_lines.append(f"# 环境配置: {self.environment_path}")
        
        header_lines.extend([
            "# @base_url = " + self.base_url,
            "# @api_version = v1",
            "# @timeout = 30000",
            "",
            ""
        ])
        
        # 扁平化并处理所有请求
        items = collection.get('item', [])
        flat_items = self.flatten_items(items)
        
        # 按模块分组处理
        content = self.process_items_by_module(flat_items)
        
        return '\n'.join(header_lines) + content
    
    def process_items_by_module(self, items: List[Dict[str, Any]]) -> str:
        """按模块分组处理请求"""
        # 按文件夹名称分组
        modules = {}
        for item in items:
            folder = item.get('__folder_name', '其他')
            if folder not in modules:
                modules[folder] = []
            modules[folder].append(item)
        
        # 生成内容
        result = []
        module_counter = 0
        
        for module_name, module_items in sorted(modules.items()):
            module_counter += 1
            separator = "=" * 20
            
            result.append(f"### {separator} {module_name} {separator}")
            result.append('')
            
            for item in module_items:
                request_str = self.convert_request(item, module_name)
                result.append(request_str)
        
        # 添加工作流部分
        result.append(self.generate_workflows())
        
        return '\n'.join(result)
    
    def generate_workflows(self) -> str:
        """生成测试工作流部分"""
        workflows = [
            "",
            "### ==================== 测试工作流 ====================",
            "",
            "### 完整系统检查工作流",
            "# 执行顺序: 健康检查 -> 系统摘要 -> 资源监控",
            "# @ref health_check",
            "# @ref system_summary",
            "# @ref system_resources",
            "",
            "### DAG 完整测试工作流",
            "# 执行顺序: 获取列表 -> 获取详情 -> 执行 -> 查询状态",
            "# @ref dag_list",
            "# @ref dag_detail",
            "# @ref dag_execute",
            "# @ref dag_status",
            "",
            "### 告警完整测试工作流",
            "# 执行顺序: 获取规则 -> 创建规则 -> 获取活跃告警 -> 确认告警",
            "# @ref alert_rules_list",
            "# @ref alert_rule_create",
            "# @ref active_alerts",
            "# @ref alert_acknowledge",
            "",
            "### 指标完整测试工作流",
            "# 执行顺序: 实时指标 -> 历史指标 -> 聚合数据",
            "# @ref metrics_realtime",
            "# @ref metrics_history",
            "# @ref metrics_aggregate",
            ""
        ]
        return '\n'.join(workflows)
    
    def get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def save(self):
        """保存转换结果"""
        content = self.convert()
        
        # 确保目录存在
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ REST Client 配置已生成: {self.output_path}")
            print(f"   - 包含 {self.request_counter} 个 API 请求")
            print(f"   - 源集合: {self.collection_path}")
            if self.environment_path:
                print(f"   - 环境配置: {self.environment_path}")
            return self.output_path
            
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
            sys.exit(1)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Postman 集合到 REST Client 配置同步工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python3 sync_postman_to_rest_client.py
  
  # 指定自定义路径
  python3 sync_postman_to_rest_client.py -c my-collection.json -o output.http
  
  # 使用环境配置
  python3 sync_postman_to_rest_client.py -e environments/local.json
        """
    )
    
    parser.add_argument(
        '-c', '--collection',
        default='tests/postman/yl-monitor-collection.json',
        help='Postman 集合文件路径 (默认: tests/postman/yl-monitor-collection.json)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='.vscode/rest-client.http',
        help='输出文件路径 (默认: .vscode/rest-client.http)'
    )
    
    parser.add_argument(
        '-e', '--environment',
        default='tests/postman/environments/local.json',
        help='Postman 环境配置文件路径'
    )
    
    parser.add_argument(
        '--no-env',
        action='store_true',
        help='不使用环境配置文件'
    )
    
    args = parser.parse_args()
    
    # 确定环境路径
    env_path = None if args.no_env else args.environment
    
    try:
        converter = PostmanToRestClientConverter(
            args.collection,
            args.output,
            env_path
        )
        converter.save()
        print("\n🎉 同步完成！")
        print(f"请在 VS Code 中打开 {args.output} 文件")
        print("然后点击请求上方的 'Send Request' 链接进行测试")
        
    except KeyboardInterrupt:
        print("\n⚠️ 操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 同步失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
