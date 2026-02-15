# 任务005：项目清理与优化执行计划

**任务ID:** cleanup-005  
**创建日期:** 2026-02-04  
**负责人:** AI 编程代理

---

## 1. 真实意图与边界澄清

### 1.1 任务目标
整理并清理项目中的沉积内容，包括：
- 缓存文件清理
- 日志文件清理
- 多余环境清理
- 旧任务文档归档
- 更新说明文档
- 遵守 .blackboxrules 规则进行优化部署

### 1.2 边界与影响范围

**修改范围:**
- 根目录 PID 文件
- docs/tasks/ 目录的执行报告文件
- 各类缓存和临时文件
- 归档目录结构优化

**不修改范围:**
- 源代码文件 (AR-backend/, YL-monitor/app/)
- 配置文件 (config/, infrastructure/)
- 有效日志结构
- 已部署的服务状态

### 1.3 清理内容清单

| 类别 | 目标 | 位置 | 操作 |
|------|------|------|------|
| PID文件 | 过期进程文件 | YL-monitor/server.pid | 删除 |
| 执行报告 | 已完成任务文档 | docs/tasks/*-execution-report.md | 归档 |
| 临时文件 | 缓存和临时数据 | 全局 | 清理 |
| Python缓存 | __pycache__, *.pyc | 全局 | 清理 |
| 测试缓存 | .pytest_cache | test/ | 清理 |
| 归档目录 | 归档索引更新 | docs/cleanup-archive/tasks/ | 优化 |

---

## 2. 影响范围分析

### 2.1 受影响模块
- **YL-monitor:** PID文件清理
- **docs/tasks:** 文档归档
- **docs/cleanup-archive:** 归档索引

### 2.2 风险评估

| 风险项 | 级别 | 预防措施 |
|--------|------|----------|
| 误删有效文件 | 中 | 严格匹配文件名模式 |
| PID文件误删 | 低 | 检查进程状态后删除 |
| 文档误归档 | 低 | 仅归档指定模式文件 |

### 2.3 预防方案
- 执行前创建文件清单
- 使用安全删除命令
- 保留删除记录

---

## 3. 详细执行步骤

### 步骤1: 清理PID文件
```bash
# 检查并清理 YL-monitor/server.pid
if [ -f "YL-monitor/server.pid" ]; then
    PID=$(cat YL-monitor/server.pid 2>/dev/null)
    if ! ps -p "$PID" > /dev/null 2>&1; then
        rm -v YL-monitor/server.pid
    fi
fi
```

### 步骤2: 归档执行报告
```bash
# 归档 docs/tasks/ 下的执行报告
mv docs/tasks/task-002-deploy-rules-execution-report.md docs/cleanup-archive/tasks/
mv docs/tasks/task-003-deploy-ar-backend-performance-execution-report.md docs/cleanup-archive/tasks/
mv docs/tasks/task-004-deploy-scripts-cicd-execution-report.md docs/cleanup-archive/tasks/
```

### 步骤3: 清理Python缓存
```bash
# 清理全局 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
```

### 步骤4: 清理测试缓存
```bash
# 清理测试相关缓存
rm -rf test/.pytest_cache 2>/dev/null
rm -rf .pytest_cache 2>/dev/null
```

### 步骤5: 更新归档索引
```bash
# 更新 docs/cleanup-archive/tasks/README.md
```

---

## 4. 验证命令与成功标准

### 4.1 验证命令
```bash
# 检查PID文件
test -f YL-monitor/server.pid && echo "PID存在" || echo "PID已清理"

# 检查执行报告
ls docs/tasks/*-execution-report.md 2>/dev/null | wc -l

# 检查缓存
find . -type d -name "__pycache__" | wc -l

# 检查磁盘使用
du -sh .
```

### 4.2 成功标准
- [ ] YL-monitor/server.pid 已删除
- [ ] 3个执行报告已归档
- [ ] Python 缓存已清理
- [ ] 归档索引已更新
- [ ] 项目结构清晰

---

## 5. 收尾工作

### 5.1 文档更新
- 更新 docs/tasks/README.md
- 更新项目 README.md

### 5.2 任务记录
- 在 TODO.md 中标记任务完成
- 记录完成时间与说明

---

**计划版本:** 1.0.0  
**创建时间:** 2026-02-04  
**待用户确认后执行**

