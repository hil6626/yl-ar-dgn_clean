# templates/ 前端页面模板说明

本目录包含 YL-Monitor 平台的所有 HTML 页面模板（Jinja2 格式），由 FastAPI 的 `TemplateResponse` 渲染并返回到浏览器。

## 页面架构

```
templates/
├─ base.html          # 通用基础模板（导航 / 布局 / 脚本加载）
├─ platform.html      # 平台主入口（重定向到 Dashboard）
├─ dashboard.html     # 主仪表板（系统健康监控）
├─ scripts.html       # 自动化脚本管理与执行
├─ api_doc.html       # API 文档与表单化调用
├─ dag.html           # DAG 流水线可视化与控制
└─ ar.html            # AR 合成项目监控与渲染
```

## 各页面功能说明

### 1. base.html（基础布局模板）

**用途**：作为其他页面的父模板，定义通用的 HTML 结构、导航栏、脚本加载等。

**关键区块**：
- `{% block title %}`：页面标题
- `{% block content %}`：页面内容区
- `{% block scripts %}`：页面专用脚本

**包含内容**：
- 导航栏导航列表（5 个主页面入口）
- 公共 CSS 加载（Bootstrap 等）
- 公共 JS 加载（fetch、WebSocket 等工具）
- 页脚信息

**开发建议**：
- 不应在 base.html 中硬编码具体业务逻辑
- 通过 `{{ }}` 变量接收后端传递的数据

---

### 2. platform.html（平台主入口）

**用途**：访问根路径 `/` 的 SPA 平台入口。

**功能**：
- 平台品牌展示
- 快速导航到各子页面
- 系统整体状态概览

**后端接口**：
- `GET /`：返回 platform.html
- `GET /api/summary`：获取系统概览数据（可选）

---

### 3. dashboard.html（主仪表板）

**用途**：系统健康监控的主界面，展示 CPU、内存、磁盘等实时数据。

**访问路径**：`/dashboard`

**页面元素**：
- 系统资源使用率（仪表盘 / 折线图）
- 服务运行状态（上线 / 离线 / 异常）
- 快速告警面板
- 推荐操作卡片

**后端接口**：
- `GET /api/dashboard/summary`：系统整体概览
- `GET /api/summary`：系统整体概览（兼容路径）
- `GET /api/scripts/list`：脚本列表（快速执行）
- `WS /ws/dashboard`：实时推送资源数据（可选）

**前端技术**：
- 图表库：Chart.js 或 ECharts
- 实时更新：WebSocket 或轮询

---

### 4. scripts.html（自动化脚本页面）

**用途**：管理和执行 `scripts/` 目录中的自动化脚本。

**页面元素**：
- 脚本列表（名称、类型、执行频率、状态）
- 脚本执行按钮
- 执行历史与日志展示
- 搜索与过滤

**后端接口**：
- `GET /api/scripts/list`：脚本清单与元数据
- `POST /api/scripts/run`：触发脚本运行
- `GET /api/scripts/status?script_id=NN`：获取执行状态
- `GET /api/scripts/logs?script_id=NN`：获取脚本日志
- `WS /ws/scripts`：实时推送脚本执行进度

**前端交互**：
- 点击脚本行展开「执行」按钮
- 支持自定义参数输入（后续扩展）
- 执行结果实时展示（JSON / 日志 / 图表）

---

### 5. api_doc.html（API 文档与调试）

**用途**：展示平台所有 API 端点，支持表单化调用（便于运维调试）。

**页面元素**：
- API 端点树状导航
- 请求方法 / 路径 / 参数说明
- 表单化请求构造
- 响应预览与格式化

**后端接口**：
- `GET /openapi.json`：返回 OpenAPI 规范
- `GET /api/meta`：基于 OpenAPI 自动生成的 API Meta（保留 function_registry 扩展）
- 其他已注册的 API 端点

**前端技术**：
- 不使用默认 Swagger UI
- 自定义表单构造与发送
- 支持 JSON / XML / 纯文本响应展示

**开发建议**：
- 页面可由后端 `/openapi.json` 动态生成
- 考虑添加"收藏"和"快速执行"功能

---

### 6. dag.html（DAG 流水线页面）

**用途**：DAG 流水线的可视化定义、执行与监控。

**页面元素**：
- DAG 节点拓扑图（有向无环图展示）
- 节点依赖关系
- 节点状态指示（待执行 / 执行中 / 成功 / 失败）
- DAG 运行 / 停止 / 暂停按钮
- 执行日志与节点详情

**后端接口**：
- `GET /api/dag/list`：DAG 清单
- `GET /api/dag/detail?dag_id=xxx`：DAG 详细定义
- `POST /api/dag/run`：触发 DAG 运行
- `POST /api/dag/stop?dag_id=xxx`：停止 DAG
- `GET /api/dag/status?dag_id=xxx`：获取执行状态
- `WS /ws/dag`：实时推送节点状态变化

**前端技术**：
- 图可视化库：VisJS / Cytoscape.js / D3.js
- 节点拖拽 / 缩放 / 平移
- 实时状态更新（WebSocket）

**开发建议**：
- 后端 DAG 定义存放在 `dags/` JSON 文件
- 前端应支持放大 / 缩小 / 全屏展示

---

### 7. ar.html（AR 合成项目监控页面）

**用途**：AR 用户界面展示与合成节点监控。

**页面元素**：
- AR 场景 3D 展示（Three.js / WebGL）
- 节点对象列表（名称 / 状态 / 资源占用）
- 渲染进度与性能指标
- 实时节点状态推送

**后端接口**：
- `GET /api/ar/nodes`：节点对象清单
- `GET /api/ar/status?node_id=xxx`：节点详细状态
- `GET /api/ar/performance`：渲染性能数据
- `WS /ws/ar`：实时推送节点与渲染状态

**前端技术**：
- 3D 渲染：Three.js / Babylon.js
- 物理引擎：Cannon.js（可选）
- 性能监控：stats.js / Chrome DevTools

**开发建议**：
- 后端仅提供数据和状态
- 前端负责 3D 场景构建与渲染
- 支持场景导出 / 录制功能（后续扩展）

---

## 开发规范

### HTML 结构

```html
{% extends "base.html" %}

{% block title %}
页面标题 - YL-Monitor
{% endblock %}

{% block content %}
<div class="container-fluid">
    <!-- 页面内容 -->
</div>
{% endblock %}

{% block scripts %}
<script>
    // 页面专用 JavaScript
</script>
{% endblock %}
```

### CSS 命名约定

- 使用 BEM 命名法：`.block__element--modifier`
- 类名使用英文小写与连字符
- 避免深层级嵌套 CSS

### JavaScript 交互约定

- 使用 `fetch()` 与后端通信
- WebSocket 使用统一的工具函数（`static/js/_ws.js`）
- 错误处理：统一的 toast / 弹窗组件
- 数据绑定：可考虑 Vue.js / React（长期规划）

### 数据绑定与更新

- 初始加载：`DOMContentLoaded` 事件触发数据获取
- 实时更新：WebSocket 推送
- 定时轮询：如不支持 WebSocket，设置 `setInterval()` 定时器

---

## 后端渲染传值示例

```python
# app/routes/dashboard.py
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard - YL-Monitor",
        "version": "1.0.0"
    })
```

---

## 页面间导航

所有页面通过 `base.html` 的导航栏相互连接：

```html
<nav class="navbar">
    <a href="/">Dashboard</a>
    <a href="/scripts">Scripts</a>
    <a href="/api-doc">API Doc</a>
    <a href="/dag">DAG Console</a>
    <a href="/ar">AR Monitor</a>
</nav>
```

---

## 前端静态资源加载

- CSS：`/static/css/style.css`
- JavaScript：`/static/js/app.js`
- 第三方库：CDN 或本地 `node_modules` 引入

详见 [static/README.md](../static/README.md)。n
---

## 后续扩展方向

- [ ] 将模板改为完全 SPA（Vue.js / React）
- [ ] 支持暗黑模式
- [ ] 国际化 (i18n) 支持
- [ ] 响应式设计优化（移动端）
- [ ] 页面权限管理（需前后端配合）
