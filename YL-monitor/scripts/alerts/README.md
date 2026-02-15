# 告警类脚本 (Alert)

> 阈值告警与通知机制

## 脚本列表

| ID | 名称 | 文件 | 描述 |
|----|------|------|------|
| 14 | 阈值告警通知 | `14_threshold_alert_notify.py` | 基于阈值触发告警和通知 |

## 告警规则配置

告警脚本支持以下阈值配置：

| 指标 | 默认阈值 | 说明 |
|------|---------|------|
| CPU使用率 | > 80% | 持续30秒触发 |
| 内存使用率 | > 85% | 持续60秒触发 |
| 磁盘使用率 | > 90% | 立即触发 |
| 服务不可用 | 任意 | 立即触发 |

## 使用方式

```bash
# 直接运行脚本
python3 scripts/alert/14_threshold_alert_notify.py --pretty

# 通过API调用
POST /api/scripts/run
{"script_id": "14"}
```

## 告警输出格式

```json
{
  "id": "14",
  "name": "阈值告警通知",
  "type": "alert",
  "status": "ok",
  "metrics": {
    "checks_performed": 8,
    "alerts_triggered": 1,
    "notifications_sent": 1
  },
  "detail": {
    "alerts": [
      {
        "metric": "cpu_percent",
        "value": 92.5,
        "threshold": 80,
        "severity": "warning",
        "message": "CPU使用率过高"
      }
    ]
  },
  "message": "已触发1个告警并发送通知"
}
```

## 告警级别

| 级别 | 值 | 说明 |
|------|-----|------|
| info | 1 | 信息提示 |
| warning | 2 | 警告 |
| error | 3 | 错误 |
| critical | 4 | 严重 |

## 返回顶部

[返回 scripts 目录](../README.md)

