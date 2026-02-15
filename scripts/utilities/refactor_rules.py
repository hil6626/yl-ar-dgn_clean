#!/usr/bin/env python3
"""
Rules System Refactoring Script
YL-AR-DGN Rules System v2.0
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import hashlib


class RulesRefactor:
    """
    规则体系重构工具
    
    支持规则文件的备份、目录重组、配置更新和验证。
    """
    
    def __init__(self):
        """初始化重构工具"""
        self.rules_root = Path(__file__).parent.parent / "rules"
        self.backup_dir = Path(__file__).parent.parent / "backup"
        self.new_structure = {
            "meta": "rules/meta",
            "understanding": "rules/understanding",
            "constraints": "rules/constraints",
            "decisions": "rules/decisions",
            "execution": "rules/execution"
        }
        
        # 文件映射
        self.file_mapping = {
            "L1-meta-goal.json": ("meta", "goals.json"),
            "L2-understanding.json": ("understanding", "core.json"),
            "L3-constraints.json": ("constraints", "core.json"),
            "L4-decisions.json": ("decisions", "core.json"),
            "L5-execution.json": ("execution", "core.json")
        }
        
        # 版本信息
        self.version = "2.0.0"
    
    def backup_rules(self) -> bool:
        """
        备份当前规则文件
        
        Returns:
            bool: 是否成功
        """
        try:
            # 创建备份目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"rules_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 复制所有规则文件
            for json_file in self.rules_root.glob("*.json"):
                shutil.copy2(json_file, backup_path / json_file.name)
            
            # 复制配置文件
            config_file = self.rules_root / "rules.config.js"
            if config_file.exists():
                shutil.copy2(config_file, backup_path / "rules.config.js")
            
            # 创建备份清单
            manifest = {
                "timestamp": timestamp,
                "version": self.version,
                "files": [],
                "md5_checksums": {}
            }
            
            for file_path in backup_path.glob("*.json"):
                with open(file_path, 'rb') as f:
                    md5 = hashlib.md5(f.read()).hexdigest()
                manifest["files"].append(file_path.name)
                manifest["md5_checksums"][file_path.name] = md5
            
            with open(backup_path / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            print(f"✅ 备份完成: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ 备份失败: {e}")
            return False
    
    def create_new_structure(self) -> bool:
        """
        创建新的目录结构
        
        Returns:
            bool: 是否成功
        """
        try:
            for dir_name, dir_path in self.new_structure.items():
                path = Path(dir_path)
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ 创建目录: {path}")
            
            return True
            
        except Exception as e:
            print(f"❌ 创建目录结构失败: {e}")
            return False
    
    def migrate_rules(self) -> bool:
        """
        迁移规则文件到新目录
        
        Returns:
            bool: 是否成功
        """
        try:
            for old_name, (new_dir, new_name) in self.file_mapping.items():
                old_path = self.rules_root / old_name
                new_path = Path(self.new_structure[new_dir]) / new_name
                
                if old_path.exists():
                    # 读取并转换内容
                    with open(old_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                    
                    # 添加版本元数据
                    if isinstance(content, dict):
                        content["_meta"] = {
                            "migrated_at": datetime.now().isoformat(),
                            "migrated_from": old_name,
                            "version": self.version
                        }
                    
                    # 写入新位置
                    with open(new_path, 'w', encoding='utf-8') as f:
                        json.dump(content, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ 迁移: {old_name} -> {new_path}")
                    
                    # 保留原文件作为备份标记
                    marker_file = old_path.with_suffix(".json.migrated")
                    marker_file.write_text(json.dumps({
                        "migrated": True,
                        "new_location": str(new_path),
                        "timestamp": datetime.now().isoformat()
                    }, indent=2))
            
            return True
            
        except Exception as e:
            print(f"❌ 迁移规则文件失败: {e}")
            return False
    
    def update_config(self) -> bool:
        """
        更新规则配置文件
        
        Returns:
            bool: 是否成功
        """
        try:
            config_path = self.rules_root / "rules.config.js"
            
            # 创建新的配置
            new_config = f'''/**
 * Rules Configuration
 * YL-AR-DGN Rules System v{self.version}
 * 
 * 最后更新: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
 */

module.exports = {{
    // 版本信息
    version: "{self.version}",
    
    // 规则目录配置
    rulesDir: __dirname,
    
    // 规则文件配置
    ruleFiles: {{
        meta: "./rules/meta/goals.json",
        understanding: "./rules/understanding/core.json",
        constraints: "./rules/constraints/core.json",
        decisions: "./rules/decisions/core.json",
        execution: "./rules/execution/core.json"
    }},
    
    // 缓存配置
    cache: {{
        enabled: true,
        ttl: 3600,  // 1小时
        maxSize: 100
    }},
    
    // 验证配置
    validation: {{
        strict: true,
        logErrors: true,
        failOnError: false
    }},
    
    // 加载顺序（依赖关系）
    loadOrder: [
        "meta",
        "understanding",
        "constraints",
        "decisions",
        "execution"
    ]
}};
'''
            config_path.write_text(new_config)
            print(f"✅ 更新配置: {config_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ 更新配置失败: {e}")
            return False
    
    def validate_rules(self) -> Dict[str, Any]:
        """
        验证规则文件
        
        Returns:
            Dict: 验证结果
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "version": self.version,
            "valid": True,
            "rules": {},
            "errors": [],
            "warnings": []
        }
        
        # 验证每个规则文件
        for rule_name, (new_dir, new_name) in self.file_mapping.items():
            new_path = Path(self.new_structure[new_dir]) / new_name
            
            if new_path.exists():
                try:
                    with open(new_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                    
                    result["rules"][rule_name] = {
                        "status": "valid",
                        "path": str(new_path),
                        "size": new_path.stat().st_size
                    }
                    
                except json.JSONDecodeError as e:
                    result["valid"] = False
                    result["errors"].append({
                        "file": str(new_path),
                        "error": str(e)
                    })
            else:
                result["warnings"].append({
                    "file": str(new_path),
                    "message": "文件不存在"
                })
        
        return result
    
    def generate_dependency_graph(self) -> Dict[str, Any]:
        """
        生成规则依赖关系图
        
        Returns:
            Dict: 依赖关系图
        """
        graph = {
            "version": self.version,
            "generated": datetime.now().isoformat(),
            "nodes": [],
            "edges": []
        }
        
        # 定义节点
        for rule_name in self.file_mapping.keys():
            graph["nodes"].append({
                "id": rule_name.replace(".json", ""),
                "name": rule_name,
                "type": "rule"
            })
        
        # 定义边（依赖关系）
        dependencies = [
            ("meta", []),
            ("understanding", ["meta"]),
            ("constraints", ["meta", "understanding"]),
            ("decisions", ["meta", "understanding", "constraints"]),
            ("execution", ["meta", "understanding", "constraints", "decisions"])
        ]
        
        for target, deps in dependencies:
            for dep in deps:
                graph["edges"].append({
                    "from": dep,
                    "to": target,
                    "type": "depends_on"
                })
        
        return graph
    
    def full_refactor(self) -> Dict[str, Any]:
        """
        执行完整的重构流程
        
        Returns:
            Dict: 执行结果
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "version": self.version,
            "steps": [],
            "success": True,
            "errors": []
        }
        
        # 步骤1: 备份
        step_result = {"step": "backup", "success": self.backup_rules()}
        result["steps"].append(step_result)
        if not step_result["success"]:
            result["success"] = False
            result["errors"].append("备份失败")
            return result
        
        # 步骤2: 创建目录结构
        step_result = {"step": "create_structure", "success": self.create_new_structure()}
        result["steps"].append(step_result)
        if not step_result["success"]:
            result["success"] = False
            result["errors"].append("创建目录结构失败")
            return result
        
        # 步骤3: 迁移规则文件
        step_result = {"step": "migrate_rules", "success": self.migrate_rules()}
        result["steps"].append(step_result)
        if not step_result["success"]:
            result["success"] = False
            result["errors"].append("迁移规则文件失败")
            return result
        
        # 步骤4: 更新配置
        step_result = {"step": "update_config", "success": self.update_config()}
        result["steps"].append(step_result)
        if not step_result["success"]:
            result["success"] = False
            result["errors"].append("更新配置失败")
            return result
        
        # 步骤5: 验证
        validation = self.validate_rules()
        result["validation"] = validation
        result["dependencies"] = self.generate_dependency_graph()
        
        return result


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="规则体系重构工具")
    parser.add_argument("--backup", action="store_true", help="备份规则文件")
    parser.add_argument("--create-structure", action="store_true", help="创建新目录结构")
    parser.add_argument("--migrate", action="store_true", help="迁移规则文件")
    parser.add_argument("--update-config", action="store_true", help="更新配置")
    parser.add_argument("--validate", action="store_true", help="验证规则")
    parser.add_argument("--graph", action="store_true", help="生成依赖图")
    parser.add_argument("--full", action="store_true", help="执行完整重构")
    
    args = parser.parse_args()
    
    refactor = RulesRefactor()
    
    if args.backup:
        success = refactor.backup_rules()
        print(f"备份{'成功' if success else '失败'}")
    
    elif args.create_structure:
        success = refactor.create_new_structure()
        print(f"创建目录结构{'成功' if success else '失败'}")
    
    elif args.migrate:
        success = refactor.migrate_rules()
        print(f"迁移规则{'成功' if success else '失败'}")
    
    elif args.update_config:
        success = refactor.update_config()
        print(f"更新配置{'成功' if success else '失败'}")
    
    elif args.validate:
        result = refactor.validate_rules()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.graph:
        graph = refactor.generate_dependency_graph()
        print(json.dumps(graph, indent=2, ensure_ascii=False))
    
    elif args.full:
        result = refactor.full_refactor()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["success"]:
            print("\n✅ 重构完成!")
        else:
            print("\n❌ 重构失败!")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
