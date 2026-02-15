# Documentation Scripts
# 文档脚本目录

**版本:** 1.0.0  
**最后更新:** 2026-02-05

本目录包含文档生成和验证相关的脚本。

## 📁 目录内容

```
docs/
├── docs_generator.py          # 文档生成器
├── verify_yl-monitor_docs.sh  # YL-monitor文档验证
└── README.md                  # 本文档
```

## 📖 脚本说明

### docs_generator.py
**功能:** 文档生成器  
**描述:** 自动生成项目文档，包括：
- API文档
- 模块文档
- 任务文档
- 索引文档

**用法:**
```bash
python docs_generator.py [--output OUTPUT_DIR]
# --output: 指定输出目录（默认: docs/docs.json）
```

**输出格式:** JSON

### verify_yl-monitor_docs.sh
**功能:** YL-monitor文档验证  
**描述:** 验证YL-monitor模块的文档完整性

**用法:**
```bash
./verify_yl-monitor_docs.sh
```

**检查项目:**
- 文档覆盖率
- 链接有效性
- 格式规范性

---

**版本:** 1.0.0  
**最后更新:** 2026-02-05
