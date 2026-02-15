# dags/ DAG 流水线定义说明

本目录存放所有 DAG（有向无环图）流水线的定义文件。每个 DAG 描述一个多步骤任务的执行依赖关系与调度策略。

## 什么是 DAG？

DAG（Directed Acyclic Graph）是一种有向无环图，用于表示任务之间的依赖关系：

- **节点（Node）**：代表一个可执行的任务单元（脚本、API 调用等）
- **边（Edge）**：代表任务之间的依赖关系（如果 A → B，则 B 依赖 A 完成）
- **无环**：不存在循环依赖（死锁）

**优点**：支持并行执行、自动调度、失败重试、可视化展示。

## DAG 文件格式

每个 DAG 定义为 JSON 文件，命名规则为：`<dag_name>.json`

### JSON 结构示例

```json
{
  "id": "dag_001",
  "name": "每日巡检流水线",
  "description": "执行系统监控、日志扫描、健康检查等任务",
  "version": "1.0",
  "created_at": "2026-02-05",
  "owner": "admin",
  "enabled": true,
  "nodes": [
    {
      "id": "node_001",
      "name": "CPU 使用率监控",
      "type": "script",
      "target": "scripts/01_cpu_usage_monitor.py",
      "timeout": 30,
      "retries": 2,
      "on_failure": "alert"
    },
    {
      "id": "node_002",
      "name": "内存使用率监控",
      "type": "script",
      "target": "scripts/02_memory_usage_monitor.py",
      "timeout": 30,
      "retries": 2,
      "on_failure": "alert"
    },
    {
      "id": "node_003",
      "name": "日志异常扫描",
      "type": "script",
      "target": "scripts/10_log_anomaly_scan.py",
      "timeout": 60,
      "retries": 1,
      "on_failure": "continue",
      "depends_on": ["node_001", "node_002"]
    },
    {
      "id": "node_004",
      "name": "生成巡检报告",
      "type": "script",
      "target": "scripts/15_scheduled_inspection_report.py",
      "timeout": 120,
      "retries": 1,
      "on_failure": "stop",
      "depends_on": ["node_003"]
    }
  ],
  "edges": [
    { "from": "node_001", "to": "node_003" },
    { "from": "node_002", "to": "node_003" },
    { "from": "node_003", "to": "node_004" }
  ],
  "schedule": {
    "type": "cron",
    "expression": "0 2 * * *",
    "description": "每天凌晨 2:00 执行"
  },
  "notifications": {
    "on_success": { "type": "email", "recipients": ["admin@example.com"] },
    "on_failure": { "type": "email", "recipients": ["admin@example.com"] }
  }
}
```

## 字段说明

### 全局字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✓ | DAG 唯一标识符（英文 + 数字） |
| `name` | string | ✓ | DAG 中文名称 |
| `description` | string |  | DAG 功能描述 |
| `version` | string |  | 版本号（用于追踪更新） |
| `created_at` | string |  | 创建日期（ISO 8601 格式） |
| `owner` | string |  | DAG 所有者 / 负责人 |
| `enabled` | boolean |  | 是否启用（默认 true） |
| `nodes` | array | ✓ | 节点列表 |
| `edges` | array |  | 边列表（显式定义依赖关系） |
| `schedule` | object |  | 调度配置 |
| `notifications` | object |  | 告警与通知配置 |

### 节点字段（nodes[]）

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✓ | 节点唯一标识符（在 DAG 内） |
| `name` | string | ✓ | 节点中文名称 |
| `type` | string | ✓ | 节点类型：`script`（脚本）/ `api`（API 调用）/ `http`（HTTP 请求） |
| `target` | string | ✓ | 执行目标（脚本路径或 API 端点） |
| `timeout` | integer |  | 执行超时时间（秒），默认 300 |
| `retries` | integer |  | 失败重试次数，默认 0 |
| `on_failure` | string |  | 失败策略：`stop`（停止整个 DAG）/ `alert`（发送告警但继续）/ `continue`（忽略继续） |
| `depends_on` | array |  | 依赖节点 ID 列表 |
| `params` | object |  | 传入参数（脚本参数或 API 查询参数） |
| `env` | object |  | 环境变量 |

### 边字段（edges[]）

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `from` | string | ✓ | 源节点 ID |
| `to` | string | ✓ | 目标节点 ID |
| `condition` | string |  | 条件执行：`always`（总是执行）/ `on_success`（前驱成功时执行） |

### 调度配置（schedule）

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | 调度类型：`cron`（Cron 表达式）/ `interval`（间隔）/ `once`（一次性）|
| `expression` | string | Cron 表达式或间隔描述 |
| `timezone` | string | 时区（默认 UTC） |
| `description` | string | 人类可读的调度描述 |

### 通知配置（notifications）

```json
{
  "on_success": {
    "type": "email",
    "recipients": ["admin@example.com"],
    "subject": "DAG 执行成功"
  },
  "on_failure": {
    "type": "webhook",
    "url": "https://webhook.example.com/alert",
    "method": "POST"
  }
}
```

## 内置示例 DAG

### example_dag.json（示例 DAG）

```json
{
  "id": "example_dag",
  "name": "示例流水线",
  "description": "演示 DAG 的基本功能",
  "nodes": [
    {
      "id": "task_a",
      "name": "任务 A",
      "type": "script",
      "target": "scripts/01_cpu_usage_monitor.py",
      "timeout": 30
    },
    {
      "id": "task_b",
      "name": "任务 B",
      "type": "script",
      "target": "scripts/02_memory_usage_monitor.py",
      "depends_on": ["task_a"],
      "timeout": 30
    }
  ],
  "edges": [
    { "from": "task_a", "to": "task_b" }
  ]
}
```

## DAG 执行流程

1. **加载 DAG**：从 JSON 文件读取定义
2. **验证 DAG**：检查无环性、节点有效性
3. **拓扑排序**：按依赖关系计算执行顺序
4. **执行节点**：
   - 依赖满足的节点立即开始
   - 支持并行执行
   - 记录每个节点的输入 / 输出 / 耗时
5. **故障处理**：根据 `on_failure` 策略决定是否继续
6. **生成报告**：执行结束后输出完整的执行报告

## 并行执行示例

以下 DAG 中，`node_001` 和 `node_002` 会并行执行：

```json
{
  "nodes": [
    { "id": "node_001", "name": "CPU 监控", "type": "script", "target": "scripts/01_cpu_usage_monitor.py" },
    { "id": "node_002", "name": "内存监控", "type": "script", "target": "scripts/02_memory_usage_monitor.py" },
    { "id": "node_003", "name": "汇总", "type": "script", "target": "scripts/15_scheduled_inspection_report.py", "depends_on": ["node_001", "node_002"] }
  ],
  "edges": [
    { "from": "node_001", "to": "node_003" },
    { "from": "node_002", "to": "node_003" }
  ]
}
```

**执行时序**：
```
时间 0：启动 node_001, node_002（并行）
时间 30：node_001, node_002 完成
时间 30：启动 node_003
时间 90：node_003 完成，整个 DAG 完成
```

## 后端接口

### 获取 DAG 列表

```http
GET /api/dag/list
```

**响应**：
```json
[
  {
    "id": "dag_001",
    "name": "每日巡检流水线",
    "status": "enabled",
    "last_run": "2026-02-05T10:30:00Z",
    "last_status": "success"
  }
]
```

### 获取 DAG 详情

```http
GET /api/dag/detail?dag_id=dag_001
```

### 运行 DAG

```http
POST /api/dag/run
Content-Type: application/json

{
  "dag_id": "dag_001"
}
```

### 查看 DAG 执行状态

```http
GET /api/dag/status?dag_id=dag_001&run_id=run_xxx
```

**响应**：
```json
{
  "run_id": "run_2026020510300001",
  "dag_id": "dag_001",
  "status": "running",
  "start_time": "2026-02-05T10:30:00Z",
  "nodes": [
    {
      "id": "node_001",
      "status": "completed",
      "start_time": "2026-02-05T10:30:00Z",
      "end_time": "2026-02-05T10:30:30Z",
      "output": { "status": "ok", "metrics": {...} }
    }
  ]
}
```

### WebSocket 实时推送

```javascript
const ws = new WebSocket("ws://localhost:5500/ws/dag?dag_id=dag_001&run_id=run_xxx");

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(msg.node_id, msg.status);
  // 更新前端可视化
};
```

## 创建新 DAG 的步骤

1. **编写 JSON 定义**：在 `dags/` 目录创建新文件 `my_dag.json`
2. **验证格式**：使用 JSON 验证工具检查结构
3. **测试加载**：通过后端接口 `GET /api/dag/detail?dag_id=my_dag` 验证
4. **手动运行**：通过前端 `/dag` 页面或 API 手动触发
5. **设置调度**：如需定时运行，配置 `schedule` 字段
6. **监控执行**：通过 `/dag` 页面观察节点状态

## 最佳实践

### DAG 设计原则

- ✅ 保持节点粒度适中（不过细也不过粗）
- ✅ 明确定义依赖关系（避免隐式依赖）
- ✅ 为长耗时任务设置 `timeout` 和 `retries`
- ✅ 合理使用 `on_failure` 策略（避免连锁失败）
- ✅ 为关键任务配置告警通知

### 常见错误

- ❌ 循环依赖（会被验证器拒绝）
- ❌ 节点 ID 重复
- ❌ 引用不存在的依赖节点
- ❌ 脚本路径错误

## 后续扩展

- [ ] 支持条件分支（if-else）
- [ ] 支持循环节点（for 循环）
- [ ] 支持动态节点生成
- [ ] Web UI 拖拽式 DAG 编辑器
- [ ] DAG 版本管理与回滚
- [ ] DAG 模板库
