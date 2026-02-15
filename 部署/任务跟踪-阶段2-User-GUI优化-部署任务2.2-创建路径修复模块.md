# 阶段2 - 任务2.2: 创建路径修复模块 - 详细部署文档

**任务ID:** 2.2  
**任务名称:** 创建路径修复模块  
**优先级:** P0（阻塞性）  
**预计工时:** 3小时  
**状态:** 待执行  
**前置依赖:** 任务2.1完成

---

## 一、任务目标

创建统一的路径修复模块，解决User GUI与AR-backend之间的模块导入问题，确保所有依赖能正确加载。

## 二、部署内容

### 2.1 创建文件清单

| 序号 | 文件路径 | 操作类型 | 说明 |
|------|----------|----------|------|
| 1 | `user/utils/path_resolver.py` | 新建 | 路径解析器 |
| 2 | `user/utils/module_loader.py` | 新建 | 模块加载器 |
| 3 | `user/utils/dependency_checker.py` | 新建 | 依赖检查器 |
| 4 | `user/fix_imports.py` | 新建 | 导入修复脚本 |

### 2.2 详细代码实现

#### 文件1: user/utils/path_resolver.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径解析器
自动解析和修复项目路径问题
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict

logger = logging.getLogger('PathResolver')


class PathResolver:
    """
    路径解析器
    自动发现和配置项目路径
    """
    
    # 已知项目结构
    PROJECT_STRUCTURE = {
        'AR-backend': {
            'core': ['camera.py', 'audio_module.py', 'utils.py', 'path_manager.py'],
            'services': ['__init__.py'],
            'integrations': ['Deep-Live-Cam', 'DeepFaceLab', 'faceswap'],
        },
        'YL-monitor': {
            'app': ['main.py'],
            'monitor': ['monitor-py'],
        },
        'user': {
            'gui': ['gui.py'],
            'services': ['status_reporter.py'],
        }
    }
    
    def __init__(self):
        self.project_root: Optional[Path] = None
        self.ar_backend_dir: Optional[Path] = None
        self.user_dir: Optional[Path] = None
        self.yl_monitor_dir: Optional[Path] = None
        
        self._resolve_paths()
    
    def _resolve_paths(self):
        """
        解析项目路径
        从当前文件位置向上查找项目根目录
        """
        # 从当前文件开始
        current_file = Path(__file__).resolve()
        current_dir = current_file.parent
        
        # 向上查找项目根目录
        for parent in current_dir.parents:
            # 检查是否包含关键目录
            has_ar_backend = (parent / 'AR-backend').exists()
            has_user = (parent / 'user').exists()
            has_yl_monitor = (parent / 'YL-monitor').exists()
            
            if has_ar_backend and has_user:
                self.project_root = parent
                self.ar_backend_dir = parent / 'AR-backend'
                self.user_dir = parent / 'user'
                self.yl_monitor_dir = parent / 'YL-monitor' if has_yl_monitor else None
                
                logger.info(f"项目根目录: {self.project_root}")
                logger.info(f"AR-backend: {self.ar_backend_dir}")
                logger.info(f"User: {self.user_dir}")
                if self.yl_monitor_dir:
                    logger.info(f"YL-monitor: {self.yl_monitor_dir}")
                break
        
        if not self.project_root:
            raise RuntimeError("无法找到项目根目录")
    
    def get_python_paths(self) -> List[str]:
        """
        获取需要添加到sys.path的路径列表
        """
        paths = []
        
        if self.project_root:
            paths.append(str(self.project_root))
        
        if self.ar_backend_dir:
            paths.extend([
                str(self.ar_backend_dir),
                str(self.ar_backend_dir / 'core'),
                str(self.ar_backend_dir / 'services'),
                str(self.ar_backend_dir / 'integrations'),
            ])
        
        if self.user_dir:
            paths.append(str(self.user_dir))
        
        return paths
    
    def setup_paths(self):
        """
        设置Python路径
        """
        paths = self.get_python_paths()
        
        for path in paths:
            if path not in sys.path:
                sys.path.insert(0, path)
                logger.debug(f"添加路径: {path}")
        
        logger.info(f"已设置 {len(paths)} 个路径")
    
    def verify_structure(self) -> Dict[str, bool]:
        """
        验证项目结构完整性
        """
        results = {}
        
        # 检查AR-backend
        if self.ar_backend_dir:
            results['ar_backend_exists'] = self.ar_backend_dir.exists()
            results['ar_backend_core'] = (self.ar_backend_dir / 'core').exists()
            results['ar_backend_services'] = (self.ar_backend_dir / 'services').exists()
        
        # 检查User
        if self.user_dir:
            results['user_exists'] = self.user_dir.exists()
            results['user_gui'] = (self.user_dir / 'gui').exists()
            results['user_services'] = (self.user_dir / 'services').exists()
        
        # 检查YL-monitor
        if self.yl_monitor_dir:
            results['yl_monitor_exists'] = self.yl_monitor_dir.exists()
        
        return results
    
    def find_module(self, module_name: str) -> Optional[Path]:
        """
        查找模块文件
        """
        search_paths = self.get_python_paths()
        
        for path in search_paths:
            path_obj = Path(path)
            
            # 尝试不同的模块位置
            possible_locations = [
                path_obj / f"{module_name}.py",
                path_obj / module_name / '__init__.py',
                path_obj / module_name / f"{module_name}.py",
            ]
            
            for location in possible_locations:
                if location.exists():
                    return location
        
        return None
    
    def create_path_config(self) -> dict:
        """
        创建路径配置
        """
        return {
            'project_root': str(self.project_root),
            'ar_backend_dir': str(self.ar_backend_dir),
            'user_dir': str(self.user_dir),
            'yl_monitor_dir': str(self.yl_monitor_dir) if self.yl_monitor_dir else None,
            'python_paths': self.get_python_paths(),
            'structure_check': self.verify_structure()
        }


# 便捷函数
def setup_project_paths():
    """
    设置项目路径（便捷函数）
    """
    resolver = PathResolver()
    resolver.setup_paths()
    return resolver


def get_project_root() -> Path:
    """
    获取项目根目录
    """
    resolver = PathResolver()
    return resolver.project_root
```

#### 文件2: user/utils/module_loader.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块加载器
处理动态模块加载和导入修复
"""

import sys
import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger('ModuleLoader')


class ModuleLoader:
    """
    模块加载器
    处理复杂的模块导入场景
    """
    
    def __init__(self):
        self.loaded_modules = {}
        self.failed_modules = set()
    
    def load_module_from_file(self, module_name: str, file_path: Path) -> Optional[Any]:
        """
        从文件加载模块
        """
        try:
            if not file_path.exists():
                logger.error(f"模块文件不存在: {file_path}")
                return None
            
            # 创建模块规范
            spec = importlib.util.spec_from_file_location(
                module_name, 
                file_path
            )
            
            if spec is None:
                logger.error(f"无法创建模块规范: {file_path}")
                return None
            
            # 创建模块
            module = importlib.util.module_from_spec(spec)
            
            # 添加到sys.modules
            sys.modules[module_name] = module
            
            # 执行模块
            spec.loader.exec_module(module)
            
            self.loaded_modules[module_name] = module
            logger.info(f"模块加载成功: {module_name} from {file_path}")
            
            return module
            
        except Exception as e:
            logger.error(f"加载模块失败 {module_name}: {e}")
            self.failed_modules.add(module_name)
            return None
    
    def safe_import(self, module_name: str, fallback_module: Optional[str] = None) -> Optional[Any]:
        """
        安全导入模块
        """
        # 检查是否已加载
        if module_name in self.loaded_modules:
            return self.loaded_modules[module_name]
        
        # 检查是否已失败
        if module_name in self.failed_modules:
            if fallback_module:
                return self.safe_import(fallback_module)
            return None
        
        try:
            # 尝试导入
            module = importlib.import_module(module_name)
            self.loaded_modules[module_name] = module
            return module
            
        except ImportError as e:
            logger.warning(f"导入失败 {module_name}: {e}")
            self.failed_modules.add(module_name)
            
            if fallback_module:
                return self.safe_import(fallback_module)
            return None
    
    def import_from_ar_backend(self, module_name: str) -> Optional[Any]:
        """
        从AR-backend导入模块
        """
        # 尝试不同的导入路径
        possible_names = [
            f'AR-backend.{module_name}',
            f'AR-backend.core.{module_name}',
            f'AR-backend.services.{module_name}',
            module_name,
        ]
        
        for name in possible_names:
            module = self.safe_import(name)
            if module:
                return module
        
        logger.error(f"无法从AR-backend导入: {module_name}")
        return None
    
    def get_class_from_module(self, module_name: str, class_name: str) -> Optional[type]:
        """
        从模块获取类
        """
        module = self.safe_import(module_name)
        if not module:
            return None
        
        try:
            return getattr(module, class_name)
        except AttributeError:
            logger.error(f"类不存在: {class_name} in {module_name}")
            return None


# 全局实例
_loader: Optional[ModuleLoader] = None

def get_module_loader() -> ModuleLoader:
    """获取模块加载器实例"""
    global _loader
    if _loader is None:
        _loader = ModuleLoader()
    return _loader


# 便捷函数
def safe_import(module_name: str, fallback: Optional[str] = None):
    """安全导入（便捷函数）"""
    return get_module_loader().safe_import(module_name, fallback)


def import_from_ar_backend(module_name: str):
    """从AR-backend导入（便捷函数）"""
    return get_module_loader().import_from_ar_backend(module_name)
```

#### 文件3: user/utils/dependency_checker.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检查器
检查项目依赖是否完整
"""

import sys
import subprocess
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger('DependencyChecker')


class DependencyChecker:
    """
    依赖检查器
    """
    
    # 核心依赖列表
    CORE_DEPENDENCIES = [
        ('PyQt5', 'PyQt5'),
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
        ('yaml', 'pyyaml'),
        ('requests', 'requests'),
        ('psutil', 'psutil'),
    ]
    
    # AR-backend依赖
    AR_BACKEND_DEPENDENCIES = [
        ('flask', 'flask'),
        ('flask_cors', 'flask-cors'),
    ]
    
    def __init__(self):
        self.missing_deps = []
        self.version_mismatches = []
    
    def check_module(self, module_name: str, package_name: str) -> Tuple[bool, str]:
        """
        检查单个模块
        """
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            return True, version
        except ImportError:
            return False, None
    
    def check_all_dependencies(self) -> Dict[str, any]:
        """
        检查所有依赖
        """
        results = {
            'core': {},
            'ar_backend': {},
            'all_installed': True
        }
        
        # 检查核心依赖
        for module_name, package_name in self.CORE_DEPENDENCIES:
            installed, version = self.check_module(module_name, package_name)
            results['core'][package_name] = {
                'installed': installed,
                'version': version
            }
            if not installed:
                self.missing_deps.append(package_name)
                results['all_installed'] = False
        
        # 检查AR-backend依赖
        for module_name, package_name in self.AR_BACKEND_DEPENDENCIES:
            installed, version = self.check_module(module_name, package_name)
            results['ar_backend'][package_name] = {
                'installed': installed,
                'version': version
            }
            if not installed:
                self.missing_deps.append(package_name)
        
        return results
    
    def install_missing(self) -> bool:
        """
        安装缺失的依赖
        """
        if not self.missing_deps:
            logger.info("所有依赖已安装")
            return True
        
        logger.info(f"安装缺失依赖: {self.missing_deps}")
        
        try:
            subprocess.check_call([
                sys.executable, 
                '-m', 
                'pip', 
                'install'
            ] + self.missing_deps)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"安装依赖失败: {e}")
            return False
    
    def generate_report(self) -> str:
        """
        生成依赖报告
        """
        results = self.check_all_dependencies()
        
        report = []
        report.append("=" * 60)
        report.append("依赖检查报告")
        report.append("=" * 60)
        
        # 核心依赖
        report.append("\n核心依赖:")
        for pkg, info in results['core'].items():
            status = "✓" if info['installed'] else "✗"
            version = info['version'] if info['installed'] else "未安装"
            report.append(f"  {status} {pkg}: {version}")
        
        # AR-backend依赖
        report.append("\nAR-backend依赖:")
        for pkg, info in results['ar_backend'].items():
            status = "✓" if info['installed'] else "✗"
            version = info['version'] if info['installed'] else "未安装"
            report.append(f"  {status} {pkg}: {version}")
        
        # 总结
        report.append("\n" + "=" * 60)
        if results['all_installed']:
            report.append("✓ 所有核心依赖已安装")
        else:
            report.append(f"✗ 缺少 {len(self.missing_deps)} 个依赖")
            report.append(f"  缺失: {', '.join(self.missing_deps)}")
        
        return '\n'.join(report)


# 便捷函数
def check_dependencies():
    """检查依赖（便捷函数）"""
    checker = DependencyChecker()
    print(checker.generate_report())
    return checker.check_all_dependencies()['all_installed']


def install_dependencies():
    """安装缺失依赖（便捷函数）"""
    checker = DependencyChecker()
    checker.check_all_dependencies()
    return checker.install_missing()
```

#### 文件4: user/fix_imports.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入修复脚本
自动修复项目中的导入问题
"""

import os
import sys
import re
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('FixImports')


def fix_file_imports(file_path: Path):
    """
    修复单个文件的导入
    """
    logger.info(f"处理文件: {file_path}")
    
    # 读取文件
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    # 常见导入修复规则
    fixes = [
        # 修复AR-backend导入
        (r'from\s+AR-backend\.core\s+import', 'from core import'),
        (r'from\s+AR-backend\.services\s+import', 'from services import'),
        (r'import\s+AR-backend\.core', 'import core'),
        
        # 修复相对导入
        (r'from\s+\.\.\s+import', '# from .. import'),  # 注释掉不安全的相对导入
        
        # 修复gui导入
        (r'from\s+gui\s+import', 'from gui import'),
    ]
    
    # 应用修复
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)
    
    # 如果有修改，写回文件
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"  已修复导入")
        return True
    else:
        logger.info(f"  无需修复")
        return False


def scan_and_fix(directory: Path):
    """
    扫描并修复目录中的所有Python文件
    """
    fixed_count = 0
    
    for py_file in directory.rglob('*.py'):
        # 跳过__pycache__
        if '__pycache__' in str(py_file):
            continue
        
        if fix_file_imports(py_file):
            fixed_count += 1
    
    logger.info(f"\n修复完成: {fixed_count} 个文件")
    return fixed_count


def main():
    """
    主函数
    """
    # 获取user目录
    user_dir = Path(__file__).parent
    
    print("=" * 60)
    print("导入修复工具")
    print("=" * 60)
    print(f"目标目录: {user_dir}")
    print()
    
    # 扫描并修复
    fixed = scan_and_fix(user_dir)
    
    print()
    if fixed > 0:
        print(f"✓ 已修复 {fixed} 个文件")
    else:
        print("✓ 所有导入已正确")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

## 三、关联内容修复

### 3.1 需要同步修复的文件

| 文件 | 修复内容 | 原因 |
|------|----------|------|
| `user/main.py` | 使用新的路径解析器 | 统一路径管理 |
| `user/gui/gui.py` | 修复导入语句 | 使用修复后的路径 |

### 3.2 详细修复说明

#### 修复1: user/main.py

在开头使用路径解析器：

```python
# 在文件开头添加
from utils.path_resolver import setup_project_paths
setup_project_paths()

# 然后使用模块加载器导入
from utils.module_loader import safe_import, import_from_ar_backend

# 安全导入AR-backend模块
CameraModule = import_from_ar_backend('camera')
AudioModule = import_from_ar_backend('audio_module')
```

## 四、部署执行步骤

### 4.1 执行前检查

```bash
# 1. 检查当前导入问题
cd user
python3 -c "import gui.gui" 2>&1 | head -20

# 2. 检查路径设置
python3 -c "import sys; print('\n'.join(sys.path))"
```

### 4.2 部署执行

```bash
# 1. 创建utils目录
mkdir -p user/utils

# 2. 创建路径修复模块文件
# user/utils/path_resolver.py
# user/utils/module_loader.py
# user/utils/dependency_checker.py
# user/fix_imports.py

# 3. 执行导入修复
cd user
python3 fix_imports.py

# 4. 验证修复
python3 -c "from utils.path_resolver import setup_project_paths; setup_project_paths(); print('路径设置成功')"

# 5. 检查依赖
python3 -c "from utils.dependency_checker import check_dependencies; check_dependencies()"
```

### 4.3 部署验证

```bash
# 1. 验证路径解析器
python3 user/utils/path_resolver.py

# 2. 验证模块加载器
python3 -c "
from utils.module_loader import safe_import
module = safe_import('core.camera')
print('模块加载成功:', module)
"

# 3. 验证依赖检查
python3 user/utils/dependency_checker.py

# 4. 完整测试
cd user
python3 main.py --test
```

## 五、常见问题及解决

### 问题1: 循环导入

**现象:** `ImportError: cannot import name 'X' from partially initialized module`

**解决:**
```python
# 延迟导入
def get_module():
    import module
    return module

# 或在函数内部导入
def function():
    from module import Class
    return Class()
```

### 问题2: 模块找不到

**现象:** `ModuleNotFoundError: No module named 'X'`

**解决:**
```bash
# 检查路径
python3 -c "import sys; [print(p) for p in sys.path]"

# 检查模块位置
find . -name "X.py"

# 使用路径解析器
from utils.path_resolver import setup_project_paths
setup_project_paths()
```

## 六、验证清单

- [ ] 路径解析器创建完成
- [ ] 模块加载器创建完成
- [ ] 依赖检查器创建完成
- [ ] 导入修复脚本创建完成
- [ ] 路径解析正常
- [ ] 模块加载正常
- [ ] 依赖检查正常
- [ ] 导入修复正常

## 七、下一步

完成本任务后，继续执行 **任务2.3: 修复 GUI 导入语句**

查看文档: `部署/任务跟踪-阶段2-User-GUI优化-部署任务2.3-修复GUI导入语句.md`
