#!/usr/bin/env python3
"""
YL-Monitor 项目落地验证脚本
验证所有核心功能是否正常工作
"""

import sys
import os
import asyncio
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def print_header(text):
    """打印标题"""
    print()
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_section(text):
    """打印小标题"""
    print(f"\n{'▶' * 2} {text}")
    print("-" * 70)

def check_mark(text):
    """成功标记"""
    print(f"  ✅ {text}")

def error_mark(text):
    """错误标记"""
    print(f"  ❌ {text}")

def warning_mark(text):
    """警告标记"""
    print(f"  ⚠️  {text}")

def info_mark(text):
    """信息标记"""
    print(f"  ℹ️  {text}")

# ============================================================================
# 第一步：环境检查
# ============================================================================

print_header("YL-Monitor 落地验证")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

print_section("1. 环境检查")

# 检查 Python 版本
python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
if sys.version_info >= (3, 8):
    check_mark(f"Python 版本: {python_version}")
else:
    error_mark(f"Python 版本过低: {python_version} (需要 >= 3.8)")
    sys.exit(1)

# 检查依赖
try:
    import fastapi
    check_mark(f"FastAPI 已安装: {fastapi.__version__}")
except ImportError:
    error_mark("FastAPI 未安装")
    sys.exit(1)

try:
    import uvicorn
    check_mark(f"Uvicorn 已安装: {uvicorn.__version__}")
except ImportError:
    error_mark("Uvicorn 未安装")

try:
    import jinja2
    check_mark(f"Jinja2 已安装: {jinja2.__version__}")
except ImportError:
    error_mark("Jinja2 未安装")

# 检查关键目录
print_section("2. 目录结构检查")

critical_dirs = {
    "app": "应用程序目录",
    "scripts": "监控脚本目录",
    "dags": "DAG配置目录",
    "logs": "日志目录",
    "templates": "模板目录",
    "static": "静态资源目录",
}

base_path = Path(__file__).parent
all_dirs_exist = True

for dir_name, description in critical_dirs.items():
    dir_path = base_path / dir_name
    if dir_path.exists():
        file_count = len(list(dir_path.glob("*")))
        check_mark(f"{description}: {dir_path.name}/ ({file_count} 项)")
    else:
        error_mark(f"{description}: {dir_path} 不存在")
        all_dirs_exist = False

if not all_dirs_exist:
    error_mark("关键目录缺失！")
    sys.exit(1)

# ============================================================================
# 第二步：应用加载检查
# ============================================================================

print_section("3. FastAPI 应用加载检查")

try:
    from app.main import app
    check_mark("FastAPI 应用加载成功")
except Exception as e:
    error_mark(f"应用加载失败: {e}")
    sys.exit(1)

# 检查路由
routes_by_type = {"http": [], "websocket": [], "mount": []}
try:
    for route in app.routes:
        if hasattr(route, "path"):
            path = route.path
            if hasattr(route, "methods"):  # HTTP 路由
                routes_by_type["http"].append(path)
            else:  # 可能是 WebSocket
                if "ws" in path or hasattr(route, "app"):
                    routes_by_type["websocket"].append(path)
    
    total_routes = len(routes_by_type["http"]) + len(routes_by_type["websocket"])
    check_mark(f"路由总数: {total_routes}")
    info_mark(f"HTTP 路由: {len(routes_by_type['http'])} 个")
    info_mark(f"WebSocket 路由: {len(routes_by_type['websocket'])} 个")
except Exception as e:
    warning_mark(f"路由枚举失败: {e}")

# ============================================================================
# 第三步：API 元数据检查
# ============================================================================

print_section("4. API 元数据检查")

try:
    from app.routes.api_doc import api_meta
    from app.routes.dashboard import get_summary
    from app.models import ScriptData, DAGData, ARNodeData
    
    # 获取 API 元数据
    meta = asyncio.run(api_meta())
    
    required_fields = ['version', 'generated_at', 'modules', 'ws_endpoints', 'function_registry']
    missing_fields = [f for f in required_fields if f not in meta]
    
    if missing_fields:
        error_mark(f"缺失字段: {missing_fields}")
    else:
        check_mark("所有必需字段存在")
        info_mark(f"版本: {meta.get('version')}")
        info_mark(f"生成时间: {meta.get('generated_at')}")
        
        modules = meta.get('modules', [])
        if modules:
            module_names = {m.get('name') for m in modules if isinstance(m, dict)}
            info_mark(f"模块数: {len(module_names)}")
            for name in sorted(module_names):
                info_mark(f"  - {name}")
except Exception as e:
    error_mark(f"API 元数据检查失败: {e}")

# ============================================================================
# 第四步：仪表板检查
# ============================================================================

print_section("5. 仪表板指标检查")

try:
    from app.routes.dashboard import get_summary
    
    summary = asyncio.run(get_summary())
    
    metrics = {
        'cpu_usage': 'CPU 使用率',
        'memory_usage': '内存使用率',
        'disk_usage': '磁盘使用率'
    }
    
    all_valid = True
    for metric_key, metric_name in metrics.items():
        value = summary.get(metric_key)
        if isinstance(value, (int, float)) and 0 <= float(value) <= 100:
            check_mark(f"{metric_name}: {value}%")
        else:
            error_mark(f"{metric_name}: 无效值 ({value})")
            all_valid = False
    
    if not all_valid:
        warning_mark("部分指标无效")
    
except Exception as e:
    error_mark(f"仪表板检查失败: {e}")

# ============================================================================
# 第五步：模型检查
# ============================================================================

print_section("6. 数据模型检查")

try:
    from app.models import ScriptData, DAGData, ARNodeData, HealthStatus
    
    # 测试 ScriptData
    script = ScriptData(
        name="test_script",
        status="idle",
        last_run="2025-02-05T10:00:00Z",
        exec_time=1.5
    )
    check_mark(f"ScriptData 模型有效: {script.name}")
    
    # 测试 HealthStatus
    health = HealthStatus(status="healthy", timestamp=datetime.now().isoformat())
    check_mark(f"HealthStatus 模型有效: {health.status}")
    
except Exception as e:
    error_mark(f"数据模型检查失败: {e}")

# ============================================================================
# 第六步：页面路由检查
# ============================================================================

print_section("7. 页面路由检查")

expected_pages = {
    "/": "首页",
    "/dashboard": "仪表板",
    "/scripts": "脚本管理",
    "/dag": "DAG 编排",
    "/ar": "渲染节点",
    "/api-doc": "API 文档",
}

try:
    page_paths = {}
    for route in app.routes:
        if hasattr(route, 'path'):
            page_paths[route.path] = True
    
    for path, description in expected_pages.items():
        if path in page_paths:
            check_mark(f"页面路由存在: {path} ({description})")
        else:
            warning_mark(f"页面路由缺失: {path} ({description})")
            
except Exception as e:
    error_mark(f"页面路由检查失败: {e}")

# ============================================================================
# 第七步：监控脚本检查
# ============================================================================

print_section("8. 监控脚本检查")

scripts_dir = base_path / "scripts"
if scripts_dir.exists():
    script_files = sorted([f for f in scripts_dir.glob("*.py") if f.name != "_common.py"])
    check_mark(f"监控脚本总数: {len(script_files)}")
    
    # 显示前 10 个脚本
    for script in script_files[:10]:
        info_mark(f"  - {script.name}")
    
    if len(script_files) > 10:
        info_mark(f"  ... 还有 {len(script_files) - 10} 个脚本")
else:
    error_mark("脚本目录不存在")

# ============================================================================
# 第八步：DAG 配置检查
# ============================================================================

print_section("9. DAG 配置检查")

dags_dir = base_path / "dags"
if dags_dir.exists():
    dag_files = list(dags_dir.glob("*.json"))
    check_mark(f"DAG 配置文件: {len(dag_files)} 个")
    for dag in dag_files:
        try:
            with open(dag) as f:
                data = json.load(f)
                check_mark(f"  {dag.name} 有效")
        except json.JSONDecodeError:
            error_mark(f"  {dag.name} JSON 格式错误")
else:
    error_mark("DAG 目录不存在")

# ============================================================================
# 第九步：静态资源检查
# ============================================================================

print_section("10. 静态资源检查")

static_dir = base_path / "static"
if static_dir.exists():
    resources = {
        "css": len(list(static_dir.glob("css/*.css"))),
        "js": len(list(static_dir.glob("js/*.js"))),
        "images": len(list(static_dir.glob("images/*"))),
    }
    
    for res_type, count in resources.items():
        info_mark(f"{res_type.upper()} 文件: {count} 个")
else:
    error_mark("静态资源目录不存在")

# ============================================================================
# 第十步：配置文件检查
# ============================================================================

print_section("11. 配置文件检查")

config_files = {
    ".env.example": "环境变量示例",
    "requirements.txt": "Python 依赖",
    "docker-compose.yml": "Docker 编排",
    "Dockerfile": "Docker 镜像",
}

for config_file, description in config_files.items():
    config_path = base_path / config_file
    if config_path.exists():
        size = config_path.stat().st_size
        check_mark(f"{description}: {config_file} ({size} 字节)")
    else:
        warning_mark(f"{description}: {config_file} 不存在")

# ============================================================================
# 第十一步：OpenAPI 检查
# ============================================================================

print_section("12. OpenAPI 规范检查")

try:
    openapi = app.openapi()
    if openapi:
        paths = openapi.get('paths', {})
        check_mark(f"OpenAPI 路径数: {len(paths)}")
        
        # 列出关键 API 端点
        critical_paths = ['/api/health', '/api/meta', '/api/summary']
        for path in critical_paths:
            if path in paths:
                check_mark(f"  端点存在: {path}")
            else:
                warning_mark(f"  端点缺失: {path}")
    else:
        error_mark("OpenAPI 规范为空")
except Exception as e:
    error_mark(f"OpenAPI 检查失败: {e}")

# ============================================================================
# 最终总结
# ============================================================================

print_header("验证总结")

print("""
✅ 基础检查完成

后续建议：
1. 运行应用: uvicorn app.main:app --reload --host 0.0.0.0 --port 5500
2. 访问仪表板: http://0.0.0.0:5500/dashboard
3. 查看 API 文档: http://0.0.0.0:5500/api-doc
4. 测试 WebSocket: ws://0.0.0.0:5500/ws/scripts

主要功能模块：
  - 📊 仪表板: CPU、内存、磁盘监控
  - 🔧 脚本管理: 50+ 个监控脚本
  - 📋 DAG 编排: 支持复杂工作流
  - 🖥️  渲染节点: AR 节点监控
  - 📡 WebSocket: 实时数据推送

推荐使用 Docker 部署：
  docker-compose up -d
""")

print("=" * 70)
print(f"验证完成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
