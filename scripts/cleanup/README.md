# Cleanup Scripts
# 清理脚本目录

**版本:** 1.1.0  
**最后更新:** 2026-02-05

本目录包含项目清理和维护相关的脚本。

## 📁 目录内容

```
cleanup/
├── cleanup_project.sh       # 项目清理（临时文件、缓存、日志）
├── cleanup_tasks_docs.sh    # 任务文档清理（移动到归档）
├── final_cleanup.sh         # 最终清理（归档所有已完成任务）
├── refactor_directories.sh  # 目录重构
├── clean_cache.sh           # 缓存清理
└── README.md                # 本文档
```

## 📖 脚本说明与区别

### 1. cleanup_project.sh
**功能:** 项目清理脚本  
**描述:** 清理项目中的临时文件、缓存和构建产物

**清理内容:**
- `*.pyc` - Python字节码
- `__pycache__/` - Python缓存
- `.pytest_cache/` - 测试缓存
- `*.egg-info/` - Python包信息
- `*.log` - 日志文件
- `*.tmp` - 临时文件
- `.DS_Store` - macOS文件
- `Thumbs.db` - Windows缩略图

**用法:**
```bash
./cleanup_project.sh [--full]
# --full: 执行完整清理（包含Docker缓存）
```

**特点:** 交互式，会询问是否清理Docker缓存

---

### 2. cleanup_tasks_docs.sh
**功能:** 任务文档清理  
**描述:** 将已完成的**任务文档**移动到归档目录

**移动内容:**
- `docs/tasks/*-task.md` - 任务文档
- `docs/tasks/task-*-deploy-*.md` - 部署跟踪
- `docs/tasks/*-execution-report.md` - 执行报告
- `docs/project/*-docs/` - 模块文档目录

**用法:**
```bash
./cleanup_tasks_docs.sh
```

**特点:** 保留索引文档在原位置，只移动详细内容

---

### 3. final_cleanup.sh
**功能:** 最终清理  
**描述:** 移除**所有已完成的任务文档**到归档

**移动内容:**
- 所有 `*-task.md` 文件
- 所有 `task-*-deploy-*.md` 文件
- 所有 `*-execution-report.md` 文件
- `IMPLEMENTATION_PLAN.md`

**用法:**
```bash
./final_cleanup.sh
```

**特点:** 更激进的清理，移动所有任务相关文档

---

### 4. refactor_directories.sh
**功能:** 目录重构脚本  
**描述:** 重新组织项目目录结构

**用法:**
```bash
./refactor_directories.sh
```

---

### 5. clean_cache.sh
**功能:** 缓存清理脚本  
**描述:** 清理各种缓存文件（轻量级）

**用法:**
```bash
./clean_cache.sh
```

---

## ⚠️ 脚本功能对比

| 功能 | cleanup_project.sh | cleanup_tasks_docs.sh | final_cleanup.sh |
|------|-------------------|----------------------|------------------|
| 清理临时文件 | ✅ | ❌ | ❌ |
| 清理Python缓存 | ✅ | ❌ | ❌ |
| 清理日志 | ✅ | ❌ | ❌ |
| 移动任务文档 | ❌ | ✅ | ✅ |
| 移动部署跟踪 | ❌ | ✅ | ✅ |
| 移动执行报告 | ❌ | ✅ | ✅ |
| 移动模块目录 | ❌ | ✅ | ❌ |
| 归档所有任务 | ❌ | ❌ | ✅ |

## 📝 使用建议

1. **日常清理:** 使用 `cleanup_project.sh`
2. **任务完成后:** 使用 `cleanup_tasks_docs.sh` 归档任务文档
3. **项目整理:** 使用 `final_cleanup.sh` 彻底清理
4. **快速清理:** 使用 `clean_cache.sh`

## 🔗 关联文档

| 文档 | 描述 |
|------|------|
| [cleanup-archive/tasks/README.md](../cleanup-archive/tasks/README.md) | 归档索引 |

---

**版本:** 1.1.0  
**最后更新:** 2026-02-05
