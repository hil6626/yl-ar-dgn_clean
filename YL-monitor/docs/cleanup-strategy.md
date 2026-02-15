# YL-Monitor 沉积内容清理策略

**版本**: 1.0.0  
**创建时间**: 2026-02-08  
**适用范围**: 全项目沉积内容管理和清理

---

## 一、策略概述

### 1.1 目标

建立系统化的沉积内容识别、清理和管理机制，确保：
- 自动识别率 > 90%
- 清理操作安全可控
- 支持模拟运行预览
- 提供完整的审计日志

### 1.2 沉积内容定义

沉积内容（Stale Content）是指：
- 超过保留期限的文件和数据
- 不再被系统引用的孤立数据
- 内容重复的文件和配置
- 临时生成的中间文件
- 占用空间过大的日志文件

---

## 二、沉积内容分类

### 2.1 按类型分类

| 类型 | 说明 | 典型示例 | 默认保留期 |
|------|------|----------|-----------|
| 临时文件 | 运行期生成的临时数据 | *.tmp, __pycache__ | 1-7天 |
| 日志文件 | 系统和应用日志 | *.log, logs/ | 7-30天 |
| 缓存文件 | 应用缓存数据 | cache/, *.cache | 7天 |
| 备份文件 | 自动生成的备份 | *.bak, *.backup | 14-30天 |
| 归档文件 | 历史数据归档 | archive/, *.zip | 90天 |
| 孤立数据 | 无引用的数据库记录 | 孤儿记录 | 30天 |
| 重复内容 | 内容重复的文件 | 重复脚本、配置 | 即时清理 |

### 2.2 按优先级分类

| 优先级 | 类型 | 清理策略 | 风险等级 |
|--------|------|----------|----------|
| P0 | 临时文件、缓存 | 自动清理 | 低 |
| P1 | 日志文件、备份 | 定期清理 | 低 |
| P2 | 孤立数据、归档 | 审核后清理 | 中 |
| P3 | 重复内容 | 合并后清理 | 中 |

---

## 三、识别策略

### 3.1 时间维度识别

```python
# 【时间识别规则】
TIME_BASED_RULES = {
    "temp_files": {
        "pattern": "**/*.tmp",
        "max_age_days": 1,
        "description": "超过1天的临时文件"
    },
    "python_cache": {
        "pattern": "**/__pycache__",
        "max_age_days": 7,
        "description": "超过7天的Python缓存"
    },
    "log_files": {
        "pattern": "logs/**/*.log",
        "max_age_days": 30,
        "max_size_mb": 100,
        "description": "超过30天或大于100MB的日志"
    },
    "old_logs": {
        "pattern": "logs/**/*.log.*",
        "max_age_days": 7,
        "description": "超过7天的轮转日志"
    },
    "backup_files": {
        "pattern": "**/*.bak",
        "max_age_days": 14,
        "description": "超过14天的备份文件"
    }
}
```

### 3.2 空间维度识别

```python
# 【空间识别规则】
SIZE_BASED_RULES = {
    "large_logs": {
        "pattern": "logs/**/*.log",
        "max_size_mb": 100,
        "description": "大于100MB的日志文件"
    },
    "large_cache": {
        "pattern": "cache/**/*",
        "max_size_mb": 500,
        "description": "大于500MB的缓存目录"
    }
}
```

### 3.3 引用维度识别

```python
# 【孤立数据识别】
ORPHAN_DETECTION = {
    "unused_scripts": {
        "check": "last_execution",
        "threshold_days": 90,
        "description": "90天未执行的脚本"
    },
    "orphan_records": {
        "check": "foreign_key_integrity",
        "description": "无关联引用的数据库记录"
    },
    "dangling_files": {
        "check": "file_reference",
        "description": "数据库记录存在但文件缺失"
    }
}
```

### 3.4 重复内容识别

```python
# 【重复内容识别】
DUPLICATE_DETECTION = {
    "file_hash": {
        "algorithm": "md5",
        "min_size_kb": 1,
        "description": "基于MD5哈希的重复文件检测"
    },
    "config_similarity": {
        "algorithm": "structural_similarity",
        "threshold": 0.9,
        "description": "基于结构相似度的配置检测"
    }
}
```

---

## 四、清理策略

### 4.1 清理模式

| 模式 | 说明 | 适用场景 | 风险等级 |
|------|------|----------|----------|
| 模拟运行 | 预览清理结果，不实际删除 | 首次清理、定期检查 | 无风险 |
| 安全清理 | 移动到回收站，保留恢复期 | 常规清理 | 低风险 |
| 立即清理 | 直接永久删除 | 确认无用的临时文件 | 中风险 |
| 归档清理 | 压缩归档后删除原文件 | 历史数据 | 低风险 |

### 4.2 清理执行流程

```
【清理流程】
1. 识别阶段
   ├── 扫描所有规则
   ├── 生成候选清理列表
   └── 计算可释放空间

2. 审核阶段（P2/P3优先级）
   ├── 人工审核确认
   ├── 排除重要文件
   └── 确认清理范围

3. 备份阶段（可选）
   ├── 创建清理前快照
   ├── 备份重要数据
   └── 记录清理清单

4. 执行阶段
   ├── 按优先级排序
   ├── 逐个执行清理
   └── 记录操作日志

5. 验证阶段
   ├── 验证清理结果
   ├── 检查系统状态
   └── 生成清理报告
```

### 4.3 安全机制

```python
# 【安全机制配置】
SAFETY_CONFIG = {
    "exclude_patterns": [
        "*.important.tmp",      # 【重要标记】
        "*.critical.log",       # 【关键日志】
        "config/*.json",        # 【配置文件】
        "data/production/*",    # 【生产数据】
    ],
    "protected_paths": [
        "app/",                 # 【应用代码】
        "system/",              # 【系统目录】
        "config/production.yml" # 【生产配置】
    ],
    "max_cleanup_percent": 30,  # 【最大清理比例】单次清理不超过总空间30%
    "require_confirmation": True,  # 【需要确认】P2/P3级别需要确认
    "backup_before_delete": True,  # 【删除前备份】
}
```

---

## 五、重复内容处理

### 5.1 重复检测流程

```python
# 【重复检测流程】
DUPLICATE_WORKFLOW = {
    "scan": {
        "directories": ["scripts/", "config/", "data/"],
        "min_size_kb": 1,
        "algorithm": "md5"
    },
    "group": {
        "by": "file_hash",
        "min_duplicates": 2
    },
    "analyze": {
        "check_content": True,
        "check_metadata": True,
        "similarity_threshold": 0.95
    },
    "merge": {
        "strategy": "keep_newest",  # 保留最新版本
        "create_symlink": True,      # 创建符号链接
        "update_references": True    # 更新引用
    }
}
```

### 5.2 合并策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| keep_first | 保留第一个发现的文件 | 无序集合 |
| keep_newest | 保留修改时间最新的文件 | 配置文件 |
| keep_largest | 保留文件大小最大的文件 | 数据文件 |
| keep_original | 保留原始文件，删除副本 | 源代码 |

---

## 六、错误恢复策略

### 6.1 脚本失败恢复

```python
# 【脚本失败恢复】
SCRIPT_RECOVERY = {
    "retry_policy": {
        "max_retries": 3,
        "backoff_strategy": "exponential",  # 指数退避
        "initial_delay": 1,  # 秒
        "max_delay": 60       # 秒
    },
    "fallback_actions": {
        "on_timeout": "kill_and_restart",
        "on_memory_error": "reduce_batch_size",
        "on_dependency_error": "skip_and_continue",
        "on_critical_error": "rollback_and_alert"
    },
    "state_recovery": {
        "checkpoint_interval": 100,  # 每100条记录检查点
        "resume_from_checkpoint": True,
        "partial_result_handling": "save_and_continue"
    }
}
```

### 6.2 系统错误恢复

```python
# 【系统错误恢复】
SYSTEM_RECOVERY = {
    "service_restart": {
        "max_attempts": 5,
        "health_check_timeout": 30,
        "escalation_delay": 300
    },
    "resource_exhaustion": {
        "cleanup_temp": True,
        "release_connections": True,
        "scale_resources": True
    },
    "corruption_recovery": {
        "validate_checksums": True,
        "restore_from_backup": True,
        "rebuild_indexes": True
    }
}
```

---

## 七、队列监控策略

### 7.1 监控指标

| 指标 | 说明 | 告警阈值 | 采集频率 |
|------|------|----------|----------|
| 队列深度 | 待处理任务数量 | >1000 | 实时 |
| 等待时间 | 任务平均等待时间 | >60s | 实时 |
| 处理速率 | 每秒处理任务数 | <10/s | 10s |
| 失败率 | 任务失败比例 | >5% | 1min |
| 积压趋势 | 队列增长趋势 | >20%/min | 5min |

### 7.2 拥塞处理

```python
# 【拥塞处理策略】
CONGESTION_HANDLING = {
    "detection": {
        "queue_depth_threshold": 1000,
        "wait_time_threshold": 60,
        "consecutive_periods": 3
    },
    "mitigation": {
        "scale_workers": True,        # 扩容工作线程
        "prioritize_critical": True,  # 优先处理关键任务
        "throttle_low_priority": True, # 限流低优先级任务
        "alert_operators": True       # 通知运维人员
    },
    "escalation": {
        "auto_scale": True,
        "page_on_critical": True,
        "create_incident": True
    }
}
```

---

## 八、实施计划

### 8.1 阶段划分

| 阶段 | 时间 | 任务 | 交付物 |
|------|------|------|--------|
| 阶段1 | 第1-2天 | 规则配置 | 清理规则配置文件 |
| 阶段2 | 第3-4天 | 检测实现 | 沉积内容检测器 |
| 阶段3 | 第5-6天 | 清理实现 | 自动清理服务 |
| 阶段4 | 第7天 | 恢复机制 | 错误恢复服务 |
| 阶段5 | 第8天 | 队列监控 | 队列监控器 |
| 阶段6 | 第9-10天 | 集成测试 | 测试报告 |

### 8.2 验收标准

- [ ] 可识别5类以上沉积内容
- [ ] 重复检测准确率 > 85%
- [ ] 错误恢复成功率 > 90%
- [ ] 队列监控实时性 < 5s延迟
- [ ] 清理操作零误删

---

## 九、运维指南

### 9.1 日常操作

```bash
# 【手动执行清理】
python -c "from app.services.cleanup_manager import cleanup_manager; import asyncio; print(asyncio.run(cleanup_manager.run_cleanup(dry_run=True)))"

# 【查看清理历史】
python -c "from app.services.cleanup_manager import cleanup_manager; print(cleanup_manager.get_cleanup_history(days=7))"

# 【查看统计信息】
python -c "from app.services.cleanup_manager import cleanup_manager; print(cleanup_manager.get_statistics())"
```

### 9.2 定期检查

| 检查项 | 频率 | 操作 |
|--------|------|------|
| 沉积内容扫描 | 每日 | 自动执行，生成报告 |
| 重复内容检测 | 每周 | 手动触发，审核后处理 |
| 清理效果评估 | 每月 | 分析清理统计，优化规则 |
| 恢复机制测试 | 每季 | 模拟故障，验证恢复 |

### 9.3 应急处理

```python
# 【紧急清理】
async def emergency_cleanup():
    """紧急清理，释放空间"""
    manager = CleanupManager()
    
    # 1. 立即清理临时文件
    await manager.run_cleanup(dry_run=False, priority="P0")
    
    # 2. 清理大日志文件
    await manager.cleanup_large_logs(threshold_mb=50)
    
    # 3. 压缩旧日志
    await manager.compress_old_logs(age_days=3)

# 【误删恢复】
async def recover_deleted_files(snapshot_id: str):
    """从快照恢复误删文件"""
    recovery = ErrorRecoveryService()
    return await recovery.restore_from_snapshot(snapshot_id)
```

---

## 十、附录

### 10.1 配置文件示例

```yaml
# cleanup-config.yml
cleanup_rules:
  - name: temp_files
    pattern: "**/*.tmp"
    max_age_days: 1
    exclude_patterns:
      - "*.important.tmp"
    
  - name: log_files
    pattern: "logs/**/*.log"
    max_age_days: 30
    max_size_mb: 100
    action: archive  # 归档而非删除

safety_settings:
  max_cleanup_percent: 30
  require_confirmation: true
  backup_before_delete: true
  protected_paths:
    - "app/"
    - "config/production.yml"

schedule:
  daily_cleanup: "0 2 * * *"  # 每天凌晨2点
  weekly_report: "0 9 * * 1"  # 每周一上午9点
```

### 10.2 相关文档

- [中文文档编写规范](./chinese-documentation-standard.md)
- [术语表](./terminology-glossary.md)
- [API规范](./api-standard.md)

### 10.3 更新记录

| 版本 | 时间 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2026-02-08 | 初始版本，建立清理策略框架 |

---

**维护者**: AI Assistant  
**审核状态**: 待审核  
**下次审查**: 2026-03-08
