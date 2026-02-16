# YL-Monitor 运维手册

**版本**: 1.0.0  
**适用对象**: 运维工程师、系统管理员  
**最后更新**: 2026-02-10

---

## 📚 目录

1. [运维概述](#一运维概述)
2. [日常运维](#二日常运维)
3. [监控告警](#三监控告警)
4. [故障处理](#四故障处理)
5. [性能优化](#五性能优化)
6. [安全管理](#六安全管理)
7. [备份恢复](#七备份恢复)
8. [升级维护](#八升级维护)

---

## 一、运维概述

### 1.1 运维目标

- **可用性**: 系统可用性 > 99.9%
- **性能**: API P95响应时间 < 200ms
- **安全**: 无高危安全漏洞
- **数据**: 数据完整性 100%

### 1.2 运维职责

| 职责 | 频率 | 说明 |
|------|------|------|
| 系统巡检 | 每日 | 检查系统状态和资源使用 |
| 日志审计 | 每日 | 检查异常日志和安全事件 |
| 备份验证 | 每周 | 验证备份完整性和可恢复性 |
| 性能分析 | 每周 | 分析性能指标和趋势 |
| 安全扫描 | 每月 | 执行安全漏洞扫描 |
| 容量规划 | 每月 | 评估资源使用和扩容需求 |

### 1.3 运维工具

**内置工具**:
- 健康检查: `/health`
- 性能监控: `/metrics`
- API文档: `/api/docs`

**外部工具**:
- Prometheus + Grafana (监控)
- ELK Stack (日志分析)
- PagerDuty/OpsGenie (告警管理)

---

## 二、日常运维

### 2.1 每日巡检清单

**系统状态检查**:
```bash
#!/bin/bash
# daily_check.sh

echo "=== YL-Monitor 每日巡检 ==="
echo "巡检时间: $(date)"

# 1. 检查服务状态
echo -e "\n[1/8] 服务状态检查"
sudo systemctl is-active yl-monitor && echo "✅ 服务运行正常" || echo "❌ 服务未运行"

# 2. 检查资源使用
echo -e "\n[2/8] 资源使用检查"
echo "CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "内存使用率: $(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')%"
echo "磁盘使用率: $(df -h / | tail -1 | awk '{print $5}')"

# 3. 检查日志
echo -e "\n[3/8] 日志检查"
ERROR_COUNT=$(grep -c "ERROR" /var/log/yl-monitor/app.log 2>/dev/null || echo "0")
echo "今日错误数: $ERROR_COUNT"
if [ "$ERROR_COUNT" -gt 10 ]; then
    echo "⚠️ 错误数超过阈值，需要关注"
fi

# 4. 检查数据库
echo -e "\n[4/8] 数据库检查"
# 检查数据库连接
# 检查表空间使用

# 5. 检查缓存
echo -e "\n[5/8] 缓存检查"
# 检查缓存命中率
# 检查缓存大小

# 6. 检查告警
echo -e "\n[6/8] 告警检查"
# 检查未处理告警数
# 检查告警通知状态

# 7. 检查备份
echo -e "\n[7/8] 备份检查"
LATEST_BACKUP=$(ls -t /opt/backups/yl-monitor/ | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    echo "✅ 最新备份: $LATEST_BACKUP"
else
    echo "❌ 未找到备份"
fi

# 8. 检查安全
echo -e "\n[8/8] 安全检查"
# 检查登录失败次数
# 检查异常访问IP

echo -e "\n=== 巡检完成 ==="
```

**执行巡检**:
```bash
# 手动执行
./daily_check.sh

# 添加到crontab
echo "0 9 * * * /opt/yl-monitor/scripts/daily_check.sh >> /var/log/yl-monitor/daily_check.log 2>&1" | sudo crontab -
```

### 2.2 日志管理

**日志查看**:
```bash
# 实时查看应用日志
tail -f /var/log/yl-monitor/app.log

# 查看错误日志
tail -f /var/log/yl-monitor/error.log

# 查看特定时间段的日志
grep "2026-02-10" /var/log/yl-monitor/app.log

# 查看特定级别的日志
grep "ERROR" /var/log/yl-monitor/app.log
```

**日志分析**:
```bash
# 统计错误数量
grep -c "ERROR" /var/log/yl-monitor/app.log

# 查找最频繁的错误
grep "ERROR" /var/log/yl-monitor/app.log | cut -d' ' -f4- | sort | uniq -c | sort -rn | head -10

# 分析响应时间
grep "response_time" /var/log/yl-monitor/app.log | awk '{print $NF}' | sort -n | tail -10
```

**日志清理**:
```bash
# 手动清理旧日志
find /var/log/yl-monitor/ -name "*.log" -mtime +30 -delete

# 压缩旧日志
find /var/log/yl-monitor/ -name "*.log" -mtime +7 -exec gzip {} \;
```

### 2.3 性能监控

**关键指标监控**:

| 指标 | 正常范围 | 告警阈值 | 严重阈值 |
|------|----------|----------|----------|
| CPU使用率 | < 70% | > 70% | > 90% |
| 内存使用率 | < 80% | > 80% | > 95% |
| 磁盘使用率 | < 80% | > 80% | > 95% |
| API P95响应 | < 200ms | > 200ms | > 500ms |
| 错误率 | < 1% | > 1% | > 5% |
| 并发连接数 | < 100 | > 100 | > 200 |

**性能数据收集**:
```bash
#!/bin/bash
# collect_metrics.sh

TIMESTAMP=$(date +%s)
DATE=$(date +%Y-%m-%d)

# 收集系统指标
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEM_USAGE=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)

# 收集应用指标
# 从应用API获取
APP_METRICS=$(curl -s http://0.0.0.0:8000/metrics)

# 保存到文件
echo "$DATE,$TIMESTAMP,$CPU_USAGE,$MEM_USAGE,$DISK_USAGE" >> /var/log/yl-monitor/metrics.csv
```

### 2.4 用户管理

**查看用户列表**:
```bash
# 通过API查看
curl http://0.0.0.0:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN"
```

**添加用户**:
```bash
curl -X POST http://0.0.0.0:8000/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "role": "operator",
    "password": "temp_password"
  }'
```

**禁用用户**:
```bash
curl -X PATCH http://0.0.0.0:8000/api/v1/users/user_id \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

---

## 三、监控告警

### 3.1 内置监控

**健康检查端点**:
```bash
# 系统健康
curl http://0.0.0.0:8000/health

# 详细健康信息
curl http://0.0.0.0:8000/health/detailed

# 依赖服务状态
curl http://0.0.0.0:8000/health/dependencies
```

**指标端点**:
```bash
# Prometheus格式指标
curl http://0.0.0.0:8000/metrics

# 自定义指标
curl http://0.0.0.0:8000/metrics/custom
```

### 3.2 告警规则配置

**系统告警规则**:
```yaml
# alert_rules.yml
groups:
  - name: system_alerts
    rules:
      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU使用率过高"
          description: "CPU使用率超过80%，当前值: {{ $value }}%"
      
      - alert: HighMemoryUsage
        expr: memory_usage_percent > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率过高"
          description: "内存使用率超过85%，当前值: {{ $value }}%"
      
      - alert: DiskSpaceLow
        expr: disk_usage_percent > 90
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "磁盘空间不足"
          description: "磁盘使用率超过90%，当前值: {{ $value }}%"
      
      - alert: ServiceDown
        expr: up{job="yl-monitor"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "服务不可用"
          description: "YL-Monitor服务已停止"
      
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "错误率过高"
          description: "5xx错误率超过5%"
```

### 3.3 告警通知配置

**邮件通知**:
```bash
# 配置邮件告警
curl -X POST http://0.0.0.0:8000/api/v1/alert-channels \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "运维团队邮件",
    "type": "email",
    "config": {
      "smtp_host": "smtp.company.com",
      "smtp_port": 587,
      "username": "alerts@company.com",
      "password": "app_password",
      "recipients": ["ops@company.com", "admin@company.com"]
    }
  }'
```

**Webhook通知**:
```bash
# 配置Webhook告警
curl -X POST http://0.0.0.0:8000/api/v1/alert-channels \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PagerDuty",
    "type": "webhook",
    "config": {
      "url": "https://events.pagerduty.com/v2/enqueue",
      "method": "POST",
      "headers": {
        "Authorization": "Token token=your_integration_key"
      }
    }
  }'
```

**短信通知**:
```bash
# 配置短信告警
curl -X POST http://0.0.0.0:8000/api/v1/alert-channels \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "紧急短信",
    "type": "sms",
    "config": {
      "provider": "twilio",
      "account_sid": "your_account_sid",
      "auth_token": "your_auth_token",
      "from_number": "+1234567890",
      "to_numbers": ["+8613800138000"]
    }
  }'
```

### 3.4 告警处理流程

**告警分级**:

| 级别 | 响应时间 | 处理方式 | 通知渠道 |
|------|----------|----------|----------|
| P0 (紧急) | 5分钟 | 立即处理 | 电话+短信+邮件 |
| P1 (高) | 15分钟 | 优先处理 | 短信+邮件 |
| P2 (中) | 1小时 | 计划处理 | 邮件 |
| P3 (低) | 1天 | 观察处理 | 邮件 |

**告警处理步骤**:
1. **确认告警**: 查看告警详情，确认问题真实性
2. **评估影响**: 评估影响范围和严重程度
3. **采取措施**: 执行修复操作或启动应急预案
4. **验证恢复**: 确认问题已解决，系统恢复正常
5. **记录总结**: 记录处理过程和根本原因

---

## 四、故障处理

### 4.1 故障分级

| 级别 | 定义 | 示例 | 响应时间 |
|------|------|------|----------|
| P0 | 系统完全不可用 | 服务崩溃、数据库故障 | 5分钟 |
| P1 | 核心功能受损 | 告警不触发、数据丢失 | 15分钟 |
| P2 | 非核心功能异常 | 报表生成慢、UI显示异常 | 1小时 |
| P3 | 轻微问题 | 日志冗余、性能下降 | 1天 |

### 4.2 故障处理流程

```mermaid
graph TD
    A[发现故障] --> B[确认故障]
    B --> C[评估影响]
    C --> D{是否需要升级?}
    D -->|是| E[启动应急预案]
    D -->|否| F[尝试修复]
    E --> G[通知相关人员]
    F --> H{修复成功?}
    H -->|是| I[验证恢复]
    H -->|否| E
    I --> J[记录故障]
    J --> K[复盘总结]
```

### 4.3 常见故障处理

**服务无法启动**:
```bash
# 1. 检查日志
journalctl -u yl-monitor -n 100 --no-pager

# 2. 检查配置
cat /opt/yl-monitor/.env | grep -v PASSWORD

# 3. 检查端口占用
netstat -tlnp | grep 8000

# 4. 检查权限
ls -la /opt/yl-monitor/

# 5. 尝试手动启动
cd /opt/yl-monitor && docker-compose up
```

**数据库连接失败**:
```bash
# 1. 检查数据库服务
sudo systemctl status postgresql

# 2. 测试连接
psql $DATABASE_URL -c "SELECT 1"

# 3. 检查连接池
# 查看应用日志中的连接错误

# 4. 重启数据库
sudo systemctl restart postgresql

# 5. 重启应用
sudo systemctl restart yl-monitor
```

**性能下降**:
```bash
# 1. 检查资源使用
top -bn1 | head -20

# 2. 检查慢查询
grep "slow query" /var/log/yl-monitor/app.log

# 3. 检查缓存命中率
# 通过应用API获取

# 4. 清理缓存
curl -X POST http://0.0.0.0:8000/api/v1/admin/cache/clear \
  -H "Authorization: Bearer $TOKEN"

# 5. 重启服务
sudo systemctl restart yl-monitor
```

**磁盘空间不足**:
```bash
# 1. 查看磁盘使用
df -h

# 2. 查找大文件
du -sh /opt/yl-monitor/* | sort -hr | head -10

# 3. 清理日志
find /var/log/yl-monitor/ -name "*.log" -mtime +7 -delete

# 4. 清理备份
ls -t /opt/backups/yl-monitor/ | tail -n +11 | xargs rm -rf

# 5. 扩展磁盘
# 联系云服务商扩展磁盘
```

### 4.4 应急预案

**服务完全不可用**:
1. 立即通知团队负责人
2. 检查基础设施状态（网络、服务器）
3. 尝试重启服务
4. 如无法恢复，启动备用实例
5. 通知用户服务中断

**数据丢失**:
1. 立即停止写入操作
2. 评估丢失数据范围
3. 从备份恢复数据
4. 验证数据完整性
5. 分析丢失原因，防止再次发生

**安全事件**:
1. 立即隔离受影响系统
2. 保留证据（日志、快照）
3. 通知安全团队
4. 评估影响范围
5. 执行安全加固措施

---

## 五、性能优化

### 5.1 性能分析

**识别性能瓶颈**:
```bash
# 1. 收集性能数据
python tests/performance/performance_benchmark.py

# 2. 分析慢请求
grep "slow_request" /var/log/yl-monitor/app.log | \
  awk '{print $NF}' | sort -n | tail -20

# 3. 分析数据库慢查询
# 查看数据库慢查询日志

# 4. 分析缓存命中率
# 通过应用API获取
```

**性能报告生成**:
```bash
#!/bin/bash
# generate_performance_report.sh

REPORT_FILE="/var/log/yl-monitor/performance_report_$(date +%Y%m%d).md"

echo "# 性能报告 $(date)" > $REPORT_FILE
echo "" >> $REPORT_FILE

# 系统资源
echo "## 系统资源" >> $REPORT_FILE
echo "- CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')" >> $REPORT_FILE
echo "- 内存使用率: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')" >> $REPORT_FILE
echo "- 磁盘使用率: $(df -h / | tail -1 | awk '{print $5}')" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 应用性能
echo "## 应用性能" >> $REPORT_FILE
# 从应用API获取性能指标
echo "" >> $REPORT_FILE

# 数据库性能
echo "## 数据库性能" >> $REPORT_FILE
# 分析数据库性能
echo "" >> $REPORT_FILE

echo "报告已生成: $REPORT_FILE"
```

### 5.2 优化措施

**数据库优化**:
```sql
-- 1. 添加索引
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
CREATE INDEX idx_metrics_name_timestamp ON metrics(name, timestamp);

-- 2. 分析表
ANALYZE alerts;
ANALYZE metrics;

-- 3. 清理旧数据
DELETE FROM alerts WHERE created_at < NOW() - INTERVAL '90 days';
DELETE FROM metrics WHERE timestamp < NOW() - INTERVAL '30 days';

-- 4. 优化配置
-- 调整shared_buffers, work_mem等参数
```

**缓存优化**:
```bash
# 1. 增加缓存TTL
# 修改环境变量 CACHE_TTL=600

# 2. 启用Redis缓存
# 修改环境变量 CACHE_BACKEND=redis

# 3. 清理缓存
curl -X POST http://0.0.0.0:8000/api/v1/admin/cache/clear \
  -H "Authorization: Bearer $TOKEN"

# 4. 预热缓存
curl -X POST http://0.0.0.0:8000/api/v1/admin/cache/warmup \
  -H "Authorization: Bearer $TOKEN"
```

**应用优化**:
```bash
# 1. 增加工作进程
# 修改docker-compose.yml中的workers配置

# 2. 启用压缩
# 确认ENABLE_COMPRESSION=true

# 3. 优化连接池
# 调整DB_POOL_SIZE和DB_MAX_OVERFLOW

# 4. 限制并发
# 调整MAX_CONCURRENT_TASKS
```

---

## 六、安全管理

### 6.1 安全审计

**每日安全审计**:
```bash
#!/bin/bash
# security_audit.sh

echo "=== 安全审计 $(date) ==="

# 1. 检查登录失败
FAILED_LOGINS=$(grep -c "Failed login" /var/log/yl-monitor/audit.log 2>/dev/null || echo "0")
echo "登录失败次数: $FAILED_LOGINS"

# 2. 检查异常IP
grep "Failed login" /var/log/yl-monitor/audit.log | \
  awk '{print $NF}' | sort | uniq -c | sort -rn | head -5

# 3. 检查权限变更
grep "Permission changed" /var/log/yl-monitor/audit.log

# 4. 检查数据访问
grep "Data access" /var/log/yl-monitor/audit.log | tail -10

# 5. 检查配置变更
grep "Config changed" /var/log/yl-monitor/audit.log
```

**定期安全扫描**:
```bash
# 运行安全渗透测试
python tests/security/security_penetration_test.py

# 检查依赖漏洞
pip-audit

# 扫描容器漏洞
docker scan yl-monitor:latest
```

### 6.2 访问控制

**用户权限管理**:
```bash
# 查看用户权限
curl http://0.0.0.0:8000/api/v1/users/permissions \
  -H "Authorization: Bearer $TOKEN"

# 修改用户角色
curl -X PATCH http://0.0.0.0:8000/api/v1/users/user_id \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "viewer"}'
```

**API密钥管理**:
```bash
# 生成新API密钥
curl -X POST http://0.0.0.0:8000/api/v1/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "第三方集成",
    "permissions": ["read:metrics", "read:alerts"],
    "expires_in_days": 90
  }'

# 撤销API密钥
curl -X DELETE http://0.0.0.0:8000/api/v1/api-keys/key_id \
  -H "Authorization: Bearer $TOKEN"
```

### 6.3 安全加固

**定期更新**:
```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 更新Python依赖
pip install --upgrade -r requirements.txt

# 更新Docker镜像
docker pull python:3.9-slim
docker-compose build --no-cache
docker-compose up -d
```

**密钥轮换**:
```bash
# 1. 生成新JWT密钥
NEW_SECRET=$(openssl rand -hex 32)

# 2. 更新配置
echo "JWT_SECRET_KEY=$NEW_SECRET" >> /opt/yl-monitor/.env

# 3. 重启服务
sudo systemctl restart yl-monitor

# 4. 通知用户重新登录
# 所有现有Token将失效
```

---

## 七、备份恢复

### 7.1 备份策略

**备份类型**:

| 类型 | 频率 | 保留期 | 存储位置 |
|------|------|--------|----------|
| 全量备份 | 每日 | 30天 | 本地+远程 |
| 增量备份 | 每小时 | 7天 | 本地 |
| 配置备份 | 每次变更 | 永久 | Git仓库 |
| 日志备份 | 实时 | 90天 | 远程存储 |

**自动备份脚本**:
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/yl-monitor"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_$DATE"

mkdir -p $BACKUP_DIR/$BACKUP_NAME

# 1. 备份数据库
cp /opt/yl-monitor/data/yl_monitor.db $BACKUP_DIR/$BACKUP_NAME/

# 2. 备份配置文件
cp /opt/yl-monitor/.env $BACKUP_DIR/$BACKUP_NAME/
cp -r /opt/yl-monitor/config $BACKUP_DIR/$BACKUP_NAME/

# 3. 备份日志
tar -czf $BACKUP_DIR/$BACKUP_NAME/logs.tar.gz /var/log/yl-monitor/

# 4. 创建备份信息
cat > $BACKUP_DIR/$BACKUP_NAME/backup_info.txt << EOF
备份时间: $(date)
备份版本: $(cat /opt/yl-monitor/version.txt)
系统信息: $(uname -a)
EOF

# 5. 压缩备份
tar -czf $BACKUP_DIR/${BACKUP_NAME}.tar.gz -C $BACKUP_DIR $BACKUP_NAME
rm -rf $BACKUP_DIR/$BACKUP_NAME

# 6. 上传到远程存储
# aws s3 cp $BACKUP_DIR/${BACKUP_NAME}.tar.gz s3://yl-monitor-backups/

# 7. 清理旧备份
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete

echo "备份完成: ${BACKUP_NAME}.tar.gz"
```

### 7.2 恢复流程

**数据恢复**:
```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: ./restore.sh <备份文件>"
    exit 1
fi

# 1. 停止服务
sudo systemctl stop yl-monitor

# 2. 备份当前数据
mv /opt/yl-monitor/data /opt/yl-monitor/data_backup_$(date +%Y%m%d)

# 3. 解压备份
tar -xzf $BACKUP_FILE -C /tmp/

# 4. 恢复数据库
cp /tmp/backup_*/yl_monitor.db /opt/yl-monitor/data/

# 5. 恢复配置
cp /tmp/backup_*/.env /opt/yl-monitor/

# 6. 设置权限
chown -R www-data:www-data /opt/yl-monitor/data/
chmod 644 /opt/yl-monitor/data/yl_monitor.db

# 7. 启动服务
sudo systemctl start yl-monitor

# 8. 验证恢复
curl http://0.0.0.0:8000/health

echo "恢复完成"
```

### 7.3 灾难恢复

**灾难恢复计划 (DRP)**:

1. **RTO (恢复时间目标)**: 4小时
2. **RPO (恢复点目标)**: 1小时

**恢复步骤**:
1. 评估灾难影响范围
2. 启动备用基础设施
3. 从远程备份恢复数据
4. 验证系统完整性
5. 切换流量到恢复的系统
6. 通知用户服务恢复

---

## 八、升级维护

### 8.1 版本升级

**升级前准备**:
```bash
# 1. 查看当前版本
cat /opt/yl-monitor/version.txt

# 2. 查看新版本变更日志
curl https://api.github.com/repos/your-org/yl-monitor/releases/latest

# 3. 创建完整备份
./scripts/backup.sh

# 4. 在测试环境验证
# 部署新版本到测试环境
# 执行完整测试
```

**升级步骤**:
```bash
#!/bin/bash
# upgrade.sh

NEW_VERSION=$1

echo "开始升级到版本 $NEW_VERSION"

# 1. 停止服务
sudo systemctl stop yl-monitor

# 2. 备份当前版本
mv /opt/yl-monitor /opt/yl-monitor_backup_$(date +%Y%m%d)

# 3. 下载新版本
wget https://github.com/your-org/yl-monitor/releases/download/v$NEW_VERSION/yl-monitor-v$NEW_VERSION.tar.gz
tar -xzf yl-monitor-v$NEW_VERSION.tar.gz -C /opt/

# 4. 恢复配置
cp /opt/yl-monitor_backup_*/.env /opt/yl-monitor/
cp -r /opt/yl-monitor_backup_*/data /opt/yl-monitor/

# 5. 执行数据库迁移
cd /opt/yl-monitor && python -m alembic upgrade head

# 6. 启动服务
sudo systemctl start yl-monitor

# 7. 验证升级
curl http://0.0.0.0:8000/health
curl http://0.0.0.0:8000/api/v1/meta | grep version

echo "升级完成"
```

**回滚方案**:
```bash
# 如果升级失败，快速回滚
sudo systemctl stop yl-monitor
rm -rf /opt/yl-monitor
mv /opt/yl-monitor_backup_* /opt/yl-monitor
sudo systemctl start yl-monitor
```

### 8.2 维护窗口

**计划维护**:
- 时间: 每周日凌晨 2:00-4:00
- 内容: 系统更新、性能优化、安全补丁
- 通知: 提前24小时通知用户

**紧急维护**:
- 时间: 立即执行
- 内容: 安全漏洞修复、严重Bug修复
- 通知: 立即通知用户

### 8.3 维护检查清单

**维护前**:
- [ ] 创建完整备份
- [ ] 通知相关用户
- [ ] 准备回滚方案
- [ ] 检查维护时间窗口

**维护中**:
- [ ] 停止服务
- [ ] 执行维护操作
- [ ] 验证维护结果
- [ ] 启动服务

**维护后**:
- [ ] 验证系统功能
- [ ] 检查日志无异常
- [ ] 通知用户维护完成
- [ ] 更新维护记录

---

## 📞 运维支持

**运维热线**: +86-xxx-xxxx-xxxx  
**紧急邮箱**: ops-urgent@yl-monitor.com  
**值班安排**: https://wiki.company.com/yl-monitor/oncall  
**运维文档**: https://wiki.company.com/yl-monitor/ops

---

**文档版本**: 1.0.0  
**最后更新**: 2026-02-10  
**维护团队**: YL-Monitor DevOps Team
