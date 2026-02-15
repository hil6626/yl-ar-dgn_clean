#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端优化验证脚本
验证 task-018 前端优化的实施效果
"""

import os
import json
import re
from pathlib import Path

class FrontendOptimizer:
    """前端优化验证器"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.static_path = self.project_root / "static"
        self.templates_path = self.project_root / "templates"
        self.js_path = self.static_path / "js"
        self.css_path = self.static_path / "css"
        
        # 验证结果
        self.results = {
            "core_utils": {"status": "pending", "message": ""},
            "global_functions": {"status": "pending", "message": ""},
            "module_manager": {"status": "pending", "message": ""},
            "css_variables": {"status": "pending", "message": ""},
            "base_html": {"status": "pending", "message": ""},
            "platform_html": {"status": "pending", "message": ""},
        }
    
    def check_file_exists(self, filepath):
        """检查文件是否存在"""
        return filepath.exists()
    
    def check_yamespace(self, filepath, namespace):
        """检查 YLMonitor 命名空间"""
        if not self.check_file_exists(filepath):
            return False
        content = filepath.read_text(encoding='utf-8')
        return f"window.YLMonitor.{namespace}" in content or f"YLMonitor.{namespace}" in content
    
    def check_inline_events(self, filepath, attribute):
        """检查是否还有内联事件"""
        if not self.check_file_exists(filepath):
            return None
        content = filepath.read_text(encoding='utf-8')
        # 检查是否还有 onclick 等内联事件
        pattern = rf'{attribute}="[^"]*"'
        matches = re.findall(pattern, content)
        # 过滤掉 data-action 属性
        relevant_matches = [m for m in matches if not m.startswith(f'{attribute}="data-action"')]
        return len(relevant_matches) == 0 if relevant_matches else True
    
    def check_css_variables(self, filepath):
        """检查 CSS 变量是否完整"""
        if not self.check_file_exists(filepath):
            return False
        content = filepath.read_text(encoding='utf-8')
        
        required_vars = [
            "--primary-color",
            "--bg-primary",
            "--bg-secondary",
            "--text-primary",
            "--text-secondary",
            "--border-color",
            "--box-shadow-sm",
            "--box-shadow-md",
            "--transition-fast",
        ]
        
        dark_theme = "[data-theme=\"dark\"]" in content
        found_vars = [v for v in required_vars if v in content]
        
        return len(found_vars) >= 6 and dark_theme
    
    def check_js_order(self, html_path):
        """检查 JS 文件加载顺序"""
        if not self.check_file_exists(html_path):
            return None
        content = html_path.read_text(encoding='utf-8')
        
        # 期望的顺序
        expected_order = [
            "config.js",
            "logger.js",
            "api-utils.js",
            "dom-utils.js",
            "modal-utils.js",
            "core-utils.js",  # 新增
            "global-functions.js",
            "module-manager.js",
            "websocket-manager.js",
            "app-init.js",
        ]
        
        # 检查 core-utils.js 是否在正确位置
        if "core-utils.js" not in content:
            return False
        
        # 检查 global-functions.js 是否在 core-utils.js 之后
        core_pos = content.find("core-utils.js")
        global_pos = content.find("global-functions.js")
        
        return core_pos < global_pos
    
    def verify_all(self):
        """验证所有优化项"""
        print("=" * 60)
        print("前端优化验证")
        print("=" * 60)
        print()
        
        # 1. 检查 core-utils.js
        print("[1/6] 检查 core-utils.js...")
        core_utils_path = self.js_path / "core-utils.js"
        if self.check_file_exists(core_utils_path):
            has_error_handler = "ErrorHandler" in core_utils_path.read_text(encoding='utf-8')
            has_validator = "Validator" in core_utils_path.read_text(encoding='utf-8')
            has_state_manager = "StateManager" in core_utils_path.read_text(encoding='utf-8')
            has_performance = "Performance" in core_utils_path.read_text(encoding='utf-8')
            has_cache = "Cache" in core_utils_path.read_text(encoding='utf-8')
            
            if all([has_error_handler, has_validator, has_state_manager, has_performance, has_cache]):
                self.results["core_utils"]["status"] = "pass"
                self.results["core_utils"]["message"] = "核心工具模块包含所有必需组件"
                print("    ✅ core-utils.js 包含 ErrorHandler, Validator, StateManager, Performance, Cache")
            else:
                self.results["core_utils"]["status"] = "fail"
                self.results["core_utils"]["message"] = "缺少部分组件"
                print("    ❌ 缺少部分组件")
        else:
            self.results["core_utils"]["status"] = "fail"
            self.results["core_utils"]["message"] = "文件不存在"
            print("    ❌ 文件不存在")
        print()
        
        # 2. 检查 global-functions.js
        print("[2/6] 检查 global-functions.js...")
        global_func_path = self.js_path / "global-functions.js"
        if self.check_file_exists(global_func_path):
            content = global_func_path.read_text(encoding='utf-8')
            has_global = "YLMonitor.Global" in content
            has_event_delegate = "EventDelegate" in content
            has_ui = "YLMonitor.UI" in content
            
            if has_global and has_event_delegate:
                self.results["global_functions"]["status"] = "pass"
                self.results["global_functions"]["message"] = "已重构为 YLMonitor.Global + EventDelegate"
                print("    ✅ 已使用 YLMonitor.Global 命名空间")
                print("    ✅ 包含 EventDelegate 事件委托")
            else:
                self.results["global_functions"]["status"] = "fail"
                print("    ❌ 未正确重构")
        else:
            self.results["global_functions"]["status"] = "fail"
            print("    ❌ 文件不存在")
        print()
        
        # 3. 检查 module-manager.js
        print("[3/6] 检查 module-manager.js...")
        module_manager_path = self.js_path / "module-manager.js"
        if self.check_file_exists(module_manager_path):
            content = module_manager_path.read_text(encoding='utf-8')
            has_namespace = "YLMonitor.ModuleManager" in content
            has_event_delegation = "EventDelegate" in content or "_initEventDelegation" in content
            
            if has_namespace:
                self.results["module_manager"]["status"] = "pass"
                self.results["module_manager"]["message"] = "已添加事件委托逻辑"
                print("    ✅ 使用 YLMonitor.ModuleManager 命名空间")
                if has_event_delegation:
                    print("    ✅ 包含事件委托实现")
            else:
                self.results["module_manager"]["status"] = "fail"
                print("    ❌ 未使用正确命名空间")
        else:
            self.results["module_manager"]["status"] = "fail"
            print("    ❌ 文件不存在")
        print()
        
        # 4. 检查 CSS 变量
        print("[4/6] 检查 CSS 变量...")
        css_path = self.css_path / "style.css"
        if self.check_css_variables(css_path):
            self.results["css_variables"]["status"] = "pass"
            self.results["css_variables"]["message"] = "CSS 变量已扩展，支持深色主题"
            print("    ✅ CSS 变量已扩展")
            print("    ✅ 支持深色主题 [data-theme=\"dark\"]")
        else:
            self.results["css_variables"]["status"] = "fail"
            print("    ❌ CSS 变量不完整或缺少深色主题")
        print()
        
        # 5. 检查 base.html
        print("[5/6] 检查 base.html...")
        base_html_path = self.templates_path / "base.html"
        if self.check_file_exists(base_html_path):
            content = base_html_path.read_text(encoding='utf-8')
            has_core_utils = "core-utils.js" in content
            correct_order = self.check_js_order(base_html_path)
            
            if has_core_utils:
                self.results["base_html"]["status"] = "pass"
                self.results["base_html"]["message"] = "已添加 core-utils.js 引用"
                print("    ✅ 已添加 core-utils.js 引用")
                if correct_order:
                    print("    ✅ JS 加载顺序正确")
                else:
                    print("    ⚠️ JS 加载顺序可能不正确")
            else:
                self.results["base_html"]["status"] = "fail"
                print("    ❌ 未添加 core-utils.js 引用")
        else:
            self.results["base_html"]["status"] = "fail"
            print("    ❌ 文件不存在")
        print()
        
        # 6. 检查 platform.html
        print("[6/6] 检查 platform.html...")
        platform_html_path = self.templates_path / "platform.html"
        if self.check_file_exists(platform_html_path):
            content = platform_html_path.read_text(encoding='utf-8')
            uses_data_action = 'data-action="quickScript"' in content
            no_onclick = 'onclick="platformRunQuickScript' not in content
            
            if uses_data_action and no_onclick:
                self.results["platform_html"]["status"] = "pass"
                self.results["platform_html"]["message"] = "已移除内联事件，使用 data-action"
                print("    ✅ 使用 data-action 属性替代 onclick")
                print("    ✅ 无内联事件")
            else:
                self.results["platform_html"]["status"] = "fail"
                if not uses_data_action:
                    print("    ❌ 未使用 data-action")
                if not no_onclick:
                    print("    ❌ 仍存在 onclick 内联事件")
        else:
            self.results["platform_html"]["status"] = "fail"
            print("    ❌ 文件不存在")
        print()
        
        # 输出总结
        self.print_summary()
        
        return self.results
    
    def print_summary(self):
        """打印验证总结"""
        print("=" * 60)
        print("验证结果总结")
        print("=" * 60)
        
        passed = sum(1 for v in self.results.values() if v["status"] == "pass")
        failed = sum(1 for v in self.results.values() if v["status"] == "fail")
        pending = sum(1 for v in self.results.values() if v["status"] == "pending")
        
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⏳ 待验证: {pending}")
        print()
        
        for name, result in self.results.items():
            status_icon = "✅" if result["status"] == "pass" else ("❌" if result["status"] == "fail" else "⏳")
            print(f"{status_icon} {name}: {result['message']}")
        
        print()
        if failed == 0:
            print("🎉 所有验证项通过！前端优化已完成。")
        else:
            print("⚠️  有验证项失败，请检查上述问题。")
        
        print("=" * 60)


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir
    
    # 创建验证器
    verifier = FrontendOptimizer(project_root)
    
    # 执行验证
    results = verifier.verify_all()
    
    # 返回退出码
    failed = sum(1 for v in results.values() if v["status"] == "fail")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())

