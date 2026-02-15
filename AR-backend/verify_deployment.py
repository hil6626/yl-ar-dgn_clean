#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR Backend 部署验证脚本
功能:
- 验证Python环境和依赖
- 验证路径配置
- 验证模块导入
- 验证服务启动

使用方法: python verify_deployment.py
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

# 配置
PROJECT_ROOT = Path(__file__).parent.resolve()
VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"


class DeploymentVerifier:
    """部署验证器"""

    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.checks_passed = 0
        self.checks_failed = 0

    def add_result(self, category: str, name: str, passed: bool, message: str = ""):
        """添加验证结果"""
        if category not in self.results:
            self.results[category] = {"passed": 0, "failed": 0, "checks": []}

        check = {
            "name": name,
            "passed": passed,
            "message": message
        }
        self.results[category]["checks"].append(check)

        if passed:
            self.results[category]["passed"] += 1
            self.checks_passed += 1
            print(f"  ✅ {name}")
        else:
            self.results[category]["failed"] += 1
            self.checks_failed += 1
            print(f"  ❌ {name}: {message}")

    def check_python_environment(self) -> bool:
        """检查Python环境"""
        print("\n📋 Python 环境检查")
        print("-" * 50)

        # 检查Python版本
        try:
            version = sys.version
            major, minor = sys.version_info[:2]
            if major >= 3 and minor >= 8:
                self.add_result("python", "Python版本", True, version)
            else:
                self.add_result("python", "Python版本", False, f"需要Python 3.8+, 当前: {version}")
        except Exception as e:
            self.add_result("python", "Python版本", False, str(e))

        # 检查pip
        try:
            import pip
            self.add_result("python", "pip模块", True, pip.__version__)
        except ImportError:
            # 尝试使用 subprocess 检查 pip3
            import subprocess
            result = subprocess.run(['pip3', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.add_result("python", "pip3", True, result.stdout.strip())
            else:
                self.add_result("python", "pip模块", False, "pip模块/pip3不可用")

        # 检查venv
        try:
            import venv
            self.add_result("python", "venv模块", True, "可用")
        except ImportError:
            self.add_result("python", "venv模块", False, "venv模块不可用")

        # 检查虚拟环境
        venv_path = PROJECT_ROOT / "venv"
        if venv_path.exists():
            venv_python = venv_path / "bin" / "python"
            if venv_python.exists():
                self.add_result("python", "虚拟环境", True, str(venv_path))
            else:
                self.add_result("python", "虚拟环境", False, "Python可执行文件不存在")
        else:
            self.add_result("python", "虚拟环境", False, "虚拟环境不存在")

        return self.results["python"]["failed"] == 0

    def check_dependencies(self) -> bool:
        """检查依赖"""
        print("\n📦 依赖检查")
        print("-" * 50)

        # 核心依赖
        core_deps = [
            ("flask", "Flask"),
            ("flask_socketio", "Flask-SocketIO"),
            ("flask_cors", "Flask-CORS"),
            ("psutil", "psutil"),
            ("numpy", "NumPy"),
            ("cv2", "OpenCV"),
            ("requests", "requests"),
        ]

        for import_name, display_name in core_deps:
            try:
                module = __import__(import_name)
                version = getattr(module, '__version__', 'unknown')
                self.add_result("dependencies", display_name, True, version)
            except ImportError:
                self.add_result("dependencies", display_name, False, "未安装")

        # 可选依赖
        optional_deps = [
            ("torch", "PyTorch"),
            ("torchvision", "TorchVision"),
            ("torchaudio", "TorchAudio"),
        ]

        for import_name, display_name in optional_deps:
            try:
                module = __import__(import_name)
                version = getattr(module, '__version__', 'unknown')
                self.add_result("dependencies", f"{display_name}(可选)", True, version)
            except ImportError:
                self.add_result("dependencies", f"{display_name}(可选)", False, "未安装（可选）")

        return self.results["dependencies"]["failed"] == 0

    def check_paths(self) -> bool:
        """检查路径配置"""
        print("\n📁 路径配置检查")
        print("-" * 50)

        # 检查项目根目录
        if PROJECT_ROOT.exists():
            self.add_result("paths", "项目根目录", True, str(PROJECT_ROOT))
        else:
            self.add_result("paths", "项目根目录", False, "不存在")

        # 检查core目录
        core_dir = PROJECT_ROOT / "core"
        if core_dir.exists():
            self.add_result("paths", "core目录", True, str(core_dir))
        else:
            self.add_result("paths", "core目录", False, "不存在")

        # 检查services目录
        services_dir = PROJECT_ROOT / "services"
        if services_dir.exists():
            self.add_result("paths", "services目录", True, str(services_dir))
        else:
            self.add_result("paths", "services目录", False, "不存在")

        # 检查config目录
        config_dir = PROJECT_ROOT / "config"
        if config_dir.exists():
            self.add_result("paths", "config目录", True, str(config_dir))
        else:
            self.add_result("paths", "config目录", False, "不存在")

        # 检查data目录
        data_dir = PROJECT_ROOT / "data"
        if data_dir.exists():
            self.add_result("paths", "data目录", True, str(data_dir))
        else:
            self.add_result("paths", "data目录", False, "不存在")

        # 检查logs目录
        logs_dir = PROJECT_ROOT / "logs"
        if logs_dir.exists():
            self.add_result("paths", "logs目录", True, str(logs_dir))
        else:
            # 尝试创建
            try:
                logs_dir.mkdir(parents=True, exist_ok=True)
                self.add_result("paths", "logs目录", True, "已创建")
            except Exception as e:
                self.add_result("paths", "logs目录", False, str(e))

        return self.results["paths"]["failed"] == 0

    def check_modules(self) -> bool:
        """检查模块导入"""
        print("\n🔌 模块导入检查")
        print("-" * 50)

        # 设置PYTHONPATH
        os.environ['PYTHONPATH'] = str(PROJECT_ROOT) + ":" + os.environ.get('PYTHONPATH', '')

        # 检查path_manager
        try:
            from core.path_manager import PathManager
            pm = PathManager()
            self.add_result("modules", "path_manager", True, str(pm.project_root))
        except Exception as e:
            self.add_result("modules", "path_manager", False, str(e))

        # 检查utils
        try:
            from core.utils import Utils
            self.add_result("modules", "core.utils", True, "可用")
        except ImportError as e:
            self.add_result("modules", "core.utils", False, f"导入失败: {e}")
        except Exception as e:
            self.add_result("modules", "core.utils", False, f"错误: {e}")

        # 检查services模块
        try:
            from services.health_check import HealthCheck
            self.add_result("modules", "health_check", True, "可用")
        except ImportError as e:
            self.add_result("modules", "health_check", False, f"导入失败: {e}")
        except Exception as e:
            self.add_result("modules", "health_check", False, f"错误: {e}")

        # 检查config_service
        try:
            from services.config_service import ConfigService
            self.add_result("modules", "config_service", True, "可用")
        except Exception as e:
            self.add_result("modules", "config_service", False, str(e))

        return self.results["modules"]["failed"] == 0

    def check_config(self) -> bool:
        """检查配置文件"""
        print("\n⚙️ 配置文件检查")
        print("-" * 50)

        # 检查pipeline.yaml
        pipeline_config = PROJECT_ROOT / "config" / "pipeline.yaml"
        if pipeline_config.exists():
            self.add_result("config", "pipeline.yaml", True, "存在")
        else:
            self.add_result("config", "pipeline.yaml", False, "不存在")

        # 检查requirements.txt
        requirements = PROJECT_ROOT / "requirements" / "requirements.txt"
        if requirements.exists():
            self.add_result("config", "requirements.txt", True, "存在")
        else:
            self.add_result("config", "requirements.txt", False, "不存在")

        return self.results["config"]["failed"] == 0

    def run_all_checks(self) -> Dict:
        """运行所有检查"""
        print("=" * 60)
        print("🚀 AR Backend 部署验证")
        print("=" * 60)
        print(f"项目根目录: {PROJECT_ROOT}")
        print(f"Python版本: {sys.version}")
        print(f"验证时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 运行所有检查
        self.check_python_environment()
        self.check_dependencies()
        self.check_paths()
        self.check_modules()
        self.check_config()

        return self.results

    def print_summary(self) -> bool:
        """打印摘要"""
        print("\n" + "=" * 60)
        print("📊 验证结果摘要")
        print("=" * 60)

        total_passed = 0
        total_failed = 0

        for category, data in self.results.items():
            passed = data["passed"]
            failed = data["failed"]
            total_passed += passed
            total_failed += failed

            status = "✅ 通过" if failed == 0 else "❌ 失败"
            print(f"{category}: {passed} 通过, {failed} 失败 {status}")

        print("-" * 60)
        print(f"总计: {total_passed} 通过, {total_failed} 失败")

        if total_failed == 0:
            print("\n🎉 所有检查通过！")
            return True
        else:
            print(f"\n⚠️  有 {total_failed} 项检查失败，请查看上述信息")
            return False


def main():
    """主函数"""
    verifier = DeploymentVerifier()
    results = verifier.run_all_checks()
    success = verifier.print_summary()

    # 保存结果
    output_file = PROJECT_ROOT / "deployment_verification.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "project_root": str(PROJECT_ROOT),
            "python_version": sys.version,
            "results": results,
            "summary": {
                "passed": verifier.checks_passed,
                "failed": verifier.checks_failed,
                "success": success
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"\n📄 验证结果已保存到: {output_file}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

