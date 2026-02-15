# Utilities Scripts
# 工具脚本目录

**版本:** 1.0.0  
**最后更新:** 2026-02-05

本目录包含各种实用工具脚本。

## 📁 目录内容

```
utilities/
├── build_gui_components.py     # GUI组件构建器
├── refactor_rules.py           # 规则重构器
├── check_dependencies.py       # 依赖检查
├── env.sh                      # 环境变量
├── fix_paths_to_local.sh       # 路径修复
├── scripts_manager.py          # 脚本管理器
├── scripts_manager_enhanced.py # 增强脚本管理器
├── verify_start.sh             # 启动验证
└── README.md                   # 本文档
```

## 📖 脚本说明

### build_gui_components.py
**功能:** GUI组件构建器  
**描述:** 自动生成GUI组件代码

**用法:**
```bash
python build_gui_components.py --component COMPONENT_NAME
```

### refactor_rules.py
**功能:** 规则重构器  
**描述:** 重构和优化项目规则

**用法:**
```bash
python refactor_rules.py --input RULES_FILE --output OUTPUT_FILE
```

### check_dependencies.py
**功能:** 依赖检查  
**描述:** 检查项目依赖是否完整

**用法:**
```bash
python check_dependencies.py
```

### env.sh
**功能:** 环境变量脚本  
**描述:** 加载和设置环境变量

**用法:**
```bash
source env.sh
```

### fix_paths_to_local.sh
**功能:** 路径修复脚本  
**描述:** 修复项目中的路径引用

**用法:**
```bash
./fix_paths_to_local.sh
```

### scripts_manager.py / scripts_manager_enhanced.py
**功能:** 脚本管理器  
**描述:** 管理项目中的脚本

**用法:**
```bash
python scripts_manager.py list
python scripts_manager_enhanced.py --verbose
```

### verify_start.sh
**功能:** 启动验证  
**描述:** 验证项目启动环境

**用法:**
```bash
./verify_start.sh
```

---

**版本:** 1.0.0  
**最后更新:** 2026-02-05
