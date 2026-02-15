#!/usr/bin/env python3
"""
Documentation Generator
YL-AR-DGN Documentation System
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import re


class DocsGenerator:
    """
    文档生成器
    
    提供文档生成、验证、链接检查和搜索索引构建功能。
    """
    
    def __init__(self, docs_root: str = None):
        """
        初始化文档生成器
        
        Args:
            docs_root: 文档根目录
        """
        if docs_root is None:
            self.docs_root = Path(__file__).parent.parent / "docs"
        else:
            self.docs_root = Path(docs_root)
        
        self.output_dir = self.docs_root / "generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载文档元数据
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """加载文档元数据"""
        metadata_file = self.docs_root / "docs.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"version": "1.0.0", "documents": {}}
    
    def save_metadata(self):
        """保存文档元数据"""
        metadata_file = self.docs_root / "docs.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def generate_index(self) -> str:
        """生成文档索引"""
        content = """# 📚 YL-AR-DGN 文档中心

**项目:** YL-AR-DGN  
**版本:** {version}  
**最后更新:** {generated}

---

## 📁 文档目录

### 核心文档

| 文档 | 描述 | 状态 |
|------|------|------|
| [README.md](README.md) | 项目主文档 | ✅ |
| [INDEX.md](INDEX.md) | 文档导航 | ✅ |
| [TODO.md](TODO.md) | 任务进度 | ✅ |
| [EXECUTION_RULES.md](EXECUTION_RULES.md) | 执行规则 | ✅ |
| [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) | 部署总结 | ✅ |

### 项目文档

| 文档 | 描述 | 状态 |
|------|------|------|
| [project/optimization-analysis.md](project/optimization-analysis.md) | 优化分析 | ✅ |
| [project/rules-docs/](project/rules-docs/) | 规则文档 | ✅ |

### 任务文档

| 文档 | 描述 | 状态 |
|------|------|------|
| [tasks/IMPLEMENTATION_SUMMARY.md](tasks/IMPLEMENTATION_SUMMARY.md) | 执行总结 | ✅ |
| [tasks/TODO.md](tasks/TODO.md) | 任务进度 | ✅ |

### 部署文档

| 文档 | 描述 | 状态 |
|------|------|------|
| [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) | 部署总结 | ✅ |
| [AR-backend/README_DEPLOYMENT.md](AR-backend/README_DEPLOYMENT.md) | 后端部署 | ✅ |

---

## 🚀 快速开始

### 新手入门

1. 阅读 [README.md](README.md) 了解项目
2. 查看 [INDEX.md](INDEX.md) 导航文档
3. 遵循 [EXECUTION_RULES.md](EXECUTION_RULES.md) 执行规则

### 开发指南

1. 查看 [project/optimization-analysis.md](project/optimization-analysis.md) 了解架构
2. 参考模块文档进行开发
3. 使用 Makefile 运行常用命令

### 部署指南

1. 阅读 [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)
2. 配置环境变量
3. 运行部署脚本

---

## 📊 文档统计

- **总文档数:** {total_docs}
- **已验证:** {valid_docs}
- **待更新:** {outdated_docs}

---

*最后更新: {generated}*
""".format(
            version=self.metadata.get("version", "1.0.0"),
            generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_docs=len(self.metadata.get("documents", {})),
            valid_docs=sum(1 for d in self.metadata.get("documents", {}).values() if d.get("status") == "verified"),
            outdated_docs=sum(1 for d in self.metadata.get("documents", {}).values() if d.get("status") == "outdated")
        )
        
        return content
    
    def generate_toc(self, doc_path: Path) -> List[Dict[str, str]]:
        """生成文档目录"""
        if not doc_path.exists():
            return []
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析标题生成TOC
        lines = content.split('\n')
        toc = []
        for line in lines:
            if line.startswith('#'):
                level = len(line.split()[0])
                title = line.strip('#').strip()
                if title:
                    anchor = self._make_anchor(title)
                    toc.append({
                        'level': str(level),
                        'title': title,
                        'anchor': anchor
                    })
        
        return toc
    
    def _make_anchor(self, title: str) -> str:
        """生成锚点链接"""
        anchor = title.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = anchor.replace(' ', '-')
        anchor = anchor.replace('/', '-')
        return anchor
    
    def check_links(self, doc_path: Path) -> List[Dict[str, str]]:
        """检查文档链接"""
        broken_links = []
        
        if not doc_path.exists():
            return [{"file": str(doc_path), "link": "", "error": "File not found"}]
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查内部链接
        links = re.findall(r'\[.*?\]\((.*?)\)', content)
        
        for link in links:
            # 跳过外部链接和锚点
            if link.startswith(('http://', 'https://', '#', 'mailto:', 'tel:')):
                continue
            
            # 检查相对路径
            link_path = doc_path.parent / link
            if not link_path.exists():
                broken_links.append({
                    "file": str(doc_path),
                    "link": link,
                    "error": "File not found"
                })
        
        return broken_links
    
    def validate_docs(self) -> Dict[str, Any]:
        """验证所有文档"""
        report = {
            "check_time": datetime.now().isoformat(),
            "total_docs": 0,
            "valid_docs": 0,
            "broken_links": 0,
            "missing_docs": 0,
            "outdated_docs": 0,
            "details": []
        }
        
        for doc_id, doc_info in self.metadata.get("documents", {}).items():
            doc_path = self.docs_root / doc_info.get("path", "")
            report["total_docs"] += 1
            
            if not doc_path.exists():
                report["missing_docs"] += 1
                report["details"].append({
                    "id": doc_id,
                    "status": "missing",
                    "path": doc_info.get("path", ""),
                    "title": doc_info.get("title", "")
                })
            else:
                # 检查链接
                broken_links = self.check_links(doc_path)
                if broken_links:
                    report["broken_links"] += len(broken_links)
                    report["details"].append({
                        "id": doc_id,
                        "status": "broken_links",
                        "path": doc_info.get("path", ""),
                        "title": doc_info.get("title", ""),
                        "links": broken_links
                    })
                else:
                    report["valid_docs"] += 1
                    report["details"].append({
                        "id": doc_id,
                        "status": "valid",
                        "path": doc_info.get("path", ""),
                        "title": doc_info.get("title", "")
                    })
                
                # 检查是否过期
                last_mod = datetime.fromtimestamp(os.path.getmtime(doc_path))
                last_update = doc_info.get("updated", "")
                if last_update:
                    try:
                        expected_update = datetime.strptime(last_update, "%Y-%m-%d")
                        if last_mod.date() > expected_update.date():
                            report["outdated_docs"] += 1
                            report["details"].append({
                                "id": doc_id,
                                "status": "outdated",
                                "path": doc_info.get("path", ""),
                                "title": doc_info.get("title", "")
                            })
                    except ValueError:
                        pass
        
        return report
    
    def build_search_index(self) -> Dict[str, Any]:
        """构建搜索索引"""
        search_index = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "documents": []
        }
        
        for doc_id, doc_info in self.metadata.get("documents", {}).items():
            doc_path = self.docs_root / doc_info.get("path", "")
            if doc_path.exists():
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取关键词
                words = set()
                for word in re.findall(r'\b[a-zA-Z]{4,}\b', content):
                    if word.lower() not in ('this', 'that', 'with', 'from', 'have', 'will', 'been', 'were', 'they', 'their'):
                        words.add(word.lower())
                
                # 提取标题
                titles = []
                for line in content.split('\n'):
                    if line.startswith('#'):
                        titles.append(line.strip('#').strip())
                
                search_index["documents"].append({
                    "id": doc_id,
                    "title": doc_info.get("title", ""),
                    "path": doc_info.get("path", ""),
                    "description": doc_info.get("description", ""),
                    "tags": doc_info.get("tags", []),
                    "titles": titles[:5],
                    "keywords": list(words)[:50]
                })
        
        return search_index
    
    def register_document(
        self,
        doc_id: str,
        path: str,
        title: str,
        description: str = "",
        category: str = "general",
        tags: List[str] = None
    ):
        """注册文档"""
        self.metadata["documents"][doc_id] = {
            "path": path,
            "title": title,
            "description": description,
            "category": category,
            "tags": tags or [],
            "status": "registered",
            "updated": datetime.now().strftime("%Y-%m-%d")
        }
        self.save_metadata()
    
    def update_document_status(self, doc_id: str, status: str):
        """更新文档状态"""
        if doc_id in self.metadata.get("documents", {}):
            self.metadata["documents"][doc_id]["status"] = status
            self.metadata["documents"][doc_id]["updated"] = datetime.now().strftime("%Y-%m-%d")
            self.save_metadata()
    
    def generate_all(self):
        """生成所有文档"""
        # 生成索引
        index_content = self.generate_index()
        index_path = self.output_dir / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        # 生成搜索索引
        search_index = self.build_search_index()
        search_path = self.output_dir / "search-index.json"
        with open(search_path, 'w', encoding='utf-8') as f:
            json.dump(search_index, f, ensure_ascii=False, indent=2)
        
        # 生成验证报告
        validation = self.validate_docs()
        validation_path = self.output_dir / "validation-report.json"
        with open(validation_path, 'w', encoding='utf-8') as f:
            json.dump(validation, f, ensure_ascii=False, indent=2)
        
        print(f"文档生成完成:")
        print(f"  - 索引: {index_path}")
        print(f"  - 搜索索引: {search_path}")
        print(f"  - 验证报告: {validation_path}")
        
        return {
            "index": str(index_path),
            "search_index": str(search_path),
            "validation_report": str(validation_path)
        }


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="YL-AR-DGN 文档生成器")
    parser.add_argument("--generate", action="store_true", help="生成所有文档")
    parser.add_argument("--validate", action="store_true", help="验证文档")
    parser.add_argument("--check-links", type=str, help="检查指定文档的链接")
    parser.add_argument("--build-index", action="store_true", help="构建搜索索引")
    parser.add_argument("--register", type=str, nargs=4, metavar=("ID", "PATH", "TITLE", "DESC"), help="注册文档")
    parser.add_argument("--status", type=str, nargs=2, metavar=("ID", "STATUS"), help="更新文档状态")
    
    args = parser.parse_args()
    
    generator = DocsGenerator()
    
    if args.generate:
        result = generator.generate_all()
        print(f"生成结果: {result}")
    elif args.validate:
        report = generator.validate_docs()
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.check_links:
        doc_path = Path(args.check_links)
        broken_links = generator.check_links(doc_path)
        print(json.dumps(broken_links, ensure_ascii=False, indent=2))
    elif args.build_index:
        search_index = generator.build_search_index()
        print(json.dumps(search_index, ensure_ascii=False, indent=2))
    elif args.register:
        doc_id, path, title, description = args.register
        generator.register_document(doc_id, path, title, description)
        print(f"文档已注册: {doc_id}")
    elif args.status:
        doc_id, status = args.status
        generator.update_document_status(doc_id, status)
        print(f"文档状态已更新: {doc_id} -> {status}")


if __name__ == "__main__":
    main()
