# YL-Monitor 项目全局优化建议文档

## 概述

本文档针对YL-Monitor项目的全局关联性、逻辑性、部署优化、自动化脚本运行停止逻辑、浏览器页面功能模块扩展、中文化说明注解、运行过程优化（沉积内容、重复内容、错误中止内容、队列性等）、页面内容呈现优化、仪表盘页面对当前运行内容监控优化、浏览器页面公共功能模块优化、DAG页面优化建议，以及预留后续部署AR项目监控建议等方面提出全面优化建议。

---

## 1. 项目关联性优化建议

### 1.1 模块间依赖关系可视化

**现状问题：**
- 模块间依赖关系不清晰，难以追踪影响范围
- 缺少依赖分析工具，难以发现潜在问题

**优化建议：**
```python
# 创建依赖分析工具 scripts/tools/dependency_analyzer.py
class DependencyAnalyzer:
    """模块依赖关系分析器"""

    def __init__(self):
        self.dependencies = {}
        self.reverse_deps = {}

    def analyze_project(self):
        """分析整个项目的依赖关系"""
        # 分析Python模块导入
        self._analyze_python_imports()
        # 分析模板继承关系
        self._analyze_template_inheritance()
        # 分析静态资源依赖
        self._analyze_static_dependencies()
        # 生成依赖图
        return self._generate_dependency_graph()

    def detect_circular_dependencies(self):
        """检测循环依赖"""
        # 实现循环依赖检测算法
        pass

    def get_affected_modules(self, module_name):
        """获取受影响的模块列表"""
        affected = set()
        to_check = [module_name]

        while to_check:
            current = to_check.pop()
            if current in self.reverse_deps:
                for dep in self.reverse_deps[current]:
                    if dep not in affected:
                        affected.add(dep)
                        to_check.append(dep)

        return affected
```

**实施收益：**
- 清晰了解模块间关系
- 快速定位变更影响范围
- 预防循环依赖问题
- 优化代码重构决策

### 1.2 统一配置管理系统

**现状问题：**
- 配置分散在多个地方
- 缺少配置变更通知机制

**优化建议：**
```python
# 创建统一配置管理 app/core/config_manager.py
class ConfigManager:
    """统一配置管理器"""

    _instance = None
    _config = {}
    _listeners = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def get(self, key, default=None):
        """获取配置"""
        return self._config.get(key, default)

    def set(self, key, value, notify=True):
        """设置配置并可选通知"""
        old_value = self._config.get(key)
        self._config[key] = value

        if notify and old_value != value:
            self._notify_listeners(key, old_value, value)

    def subscribe(self, callback):
        """订阅配置变更"""
        self._listeners.append(callback)

    def _notify_listeners(self, key, old_val, new_val):
        """通知所有监听器"""
        for listener in self._listeners:
            try:
                listener(key, old_val, new_val)
            except Exception as e:
                logger.error(f"配置监听器执行失败: {e}")

    def _load_config(self):
        """加载配置"""
        # 从环境变量、配置文件等加载
        pass
```

---

## 2. 项目逻辑性优化建议

### 2.1 业务流程标准化

**现状问题：**
- 各模块业务逻辑处理不统一
- 缺少标准化的错误处理流程

**优化建议：**
```python
# 创建业务流程管理器 app/core/business_flow.py
class BusinessFlowManager:
    """业务流程管理器"""

    def __init__(self):
        self.flows = {}
        self.middlewares = []

    def register_flow(self, name, steps, error_handler=None):
        """注册业务流程"""
        self.flows[name] = {
            'steps': steps,
            'error_handler': error_handler
        }

    def execute_flow(self, name, context):
        """执行业务流程"""
        if name not in self.flows:
            raise ValueError(f"未找到业务流程: {name}")

        flow = self.flows[name]
        result = context

        try:
            # 执行中间件
            for middleware in self.middlewares:
                result = middleware(result)

            # 执行流程步骤
            for step in flow['steps']:
                result = step(result)

            return result

        except Exception as e:
            if flow['error_handler']:
                return flow['error_handler'](e, result)
            raise

    def add_middleware(self, middleware):
        """添加中间件"""
        self.middlewares.append(middleware)
```

### 2.2 数据流追踪系统

**现状问题：**
- 数据在系统中的流转过程不透明
- 难以追踪数据处理异常

**优化建议：**
```python
# 创建数据流追踪器 app/core/data_tracker.py
class DataTracker:
    """数据流追踪器"""

    def __init__(self):
        self.traces = {}
        self.current_trace_id = None

    def start_trace(self, name, data=None):
        """开始数据追踪"""
        trace_id = str(uuid.uuid4())
        self.current_trace_id = trace_id

        self.traces[trace_id] = {
            'name': name,
            'start_time': datetime.now(),
            'steps': [],
            'data': data,
            'status': 'running'
        }

        return trace_id

    def add_step(self, step_name, input_data=None, output_data=None, metadata=None):
        """添加处理步骤"""
        if not self.current_trace_id:
            return

        step = {
            'name': step_name,
            'timestamp': datetime.now(),
            'input': input_data,
            'output': output_data,
            'metadata': metadata
        }

        self.traces[self.current_trace_id]['steps'].append(step)

    def end_trace(self, result=None, error=None):
        """结束数据追踪"""
        if not self.current_trace_id:
            return

        trace = self.traces[self.current_trace_id]
        trace['end_time'] = datetime.now()
        trace['duration'] = (trace['end_time'] - trace['start_time']).total_seconds()
        trace['result'] = result
        trace['error'] = error
        trace['status'] = 'error' if error else 'completed'

        self.current_trace_id = None

    def get_trace(self, trace_id):
        """获取追踪信息"""
        return self.traces.get(trace_id)

    def get_active_traces(self):
        """获取活跃追踪"""
        return {k: v for k, v in self.traces.items() if v['status'] == 'running'}
```

---

## 3. 部署优化建议

### 3.1 自动化部署管道

**现状问题：**
- 部署过程依赖手动操作
- 缺少部署验证和回滚机制

**优化建议：**
```python
# 创建部署管道 scripts/deploy/pipeline.py
class DeploymentPipeline:
    """自动化部署管道"""

    def __init__(self):
        self.stages = []
        self.rollback_actions = []

    def add_stage(self, name, action, rollback=None, verify=None):
        """添加部署阶段"""
        self.stages.append({
            'name': name,
            'action': action,
            'rollback': rollback,
            'verify': verify
        })

    async def deploy(self, dry_run=False):
        """执行部署"""
        results = []

        for stage in self.stages:
            try:
                if dry_run:
                    # 模拟执行
                    result = f"DRY RUN: {stage['name']}"
                else:
                    # 实际执行
                    result = await stage['action']()

                # 验证阶段
                if stage.get('verify'):
                    verify_result = await stage['verify']()
                    if not verify_result:
                        raise Exception(f"验证失败: {stage['name']}")

                results.append({
                    'stage': stage['name'],
                    'status': 'success',
                    'result': result
                })

                # 记录回滚点
                if stage.get('rollback'):
                    self.rollback_actions.append(stage['rollback'])

            except Exception as e:
                results.append({
                    'stage': stage['name'],
                    'status': 'failed',
                    'error': str(e)
                })

                # 自动回滚
                await self._rollback()
                raise

        return results

    async def _rollback(self):
        """执行回滚"""
        for rollback_action in reversed(self.rollback_actions):
            try:
                await rollback_action()
            except Exception as e:
                logger.error(f"回滚失败: {e}")
```

### 3.2 部署状态监控

**优化建议：**
```python
# 创建部署监控器 app/services/deployment_monitor.py
class DeploymentMonitor:
    """部署状态监控器"""

    def __init__(self):
        self.deployments = {}
        self.metrics = {}

    def start_deployment(self, deployment_id, config):
        """开始部署监控"""
        self.deployments[deployment_id] = {
            'config': config,
            'start_time': datetime.now(),
            'status': 'running',
            'stages': [],
            'metrics': {}
        }

    def update_stage(self, deployment_id, stage_name, status, data=None):
        """更新部署阶段状态"""
        if deployment_id not in self.deployments:
            return

        deployment = self.deployments[deployment_id]
        stage_info = {
            'name': stage_name,
            'status': status,
            'timestamp': datetime.now(),
            'data': data
        }

        deployment['stages'].append(stage_info)

        # 更新整体状态
        if status == 'failed':
            deployment['status'] = 'failed'
            deployment['end_time'] = datetime.now()
        elif status == 'completed' and all(s['status'] == 'completed' for s in deployment['stages']):
            deployment['status'] = 'completed'
            deployment['end_time'] = datetime.now()

    def get_deployment_status(self, deployment_id):
        """获取部署状态"""
        return self.deployments.get(deployment_id)

    def get_deployment_history(self, limit=10):
        """获取部署历史"""
        deployments = list(self.deployments.values())
        deployments.sort(key=lambda x: x['start_time'], reverse=True)
        return deployments[:limit]
```

---

## 4. 自动化脚本运行停止逻辑优化建议

### 4.1 脚本执行引擎重构

**现状问题：**
- 脚本执行缺乏统一管理
- 缺少执行状态追踪和控制

**优化建议：**
```python
# 重构脚本执行引擎 app/services/script_executor.py
class ScriptExecutor:
    """统一脚本执行引擎"""

    def __init__(self):
        self.running_scripts = {}
        self.script_queue = asyncio.Queue()
        self.max_concurrent = 3
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

    async def execute_script(self, script_id, params=None, timeout=300):
        """执行脚本"""
        execution_id = str(uuid.uuid4())

        execution = {
            'id': execution_id,
            'script_id': script_id,
            'params': params or {},
            'status': 'queued',
            'start_time': datetime.now(),
            'timeout': timeout,
            'process': None,
            'log': []
        }

        self.running_scripts[execution_id] = execution

        # 添加到队列
        await self.script_queue.put(execution_id)

        # 启动执行任务
        asyncio.create_task(self._execute_from_queue())

        return execution_id

    async def _execute_from_queue(self):
        """从队列执行脚本"""
        async with self.semaphore:
            execution_id = await self.script_queue.get()

            try:
                execution = self.running_scripts[execution_id]
                execution['status'] = 'running'

                # 执行脚本
                result = await self._run_script_process(execution)

                execution['status'] = 'completed'
                execution['result'] = result
                execution['end_time'] = datetime.now()

            except Exception as e:
                execution['status'] = 'failed'
                execution['error'] = str(e)
                execution['end_time'] = datetime.now()

            finally:
                self.script_queue.task_done()

    async def stop_script(self, execution_id, force=False):
        """停止脚本执行"""
        if execution_id not in self.running_scripts:
            return False

        execution = self.running_scripts[execution_id]

        if execution['status'] not in ['running', 'queued']:
            return False

        if execution['process']:
            if force:
                execution['process'].kill()
            else:
                execution['process'].terminate()

            # 等待进程结束
            try:
                await asyncio.wait_for(execution['process'].wait(), timeout=10)
            except asyncio.TimeoutError:
                execution['process'].kill()

        execution['status'] = 'stopped'
        execution['end_time'] = datetime.now()

        return True

    def get_execution_status(self, execution_id):
        """获取执行状态"""
        return self.running_scripts.get(execution_id)

    def get_running_executions(self):
        """获取正在运行的执行"""
        return {k: v for k, v in self.running_scripts.items()
                if v['status'] in ['running', 'queued']}
```

### 4.2 脚本生命周期管理

**优化建议：**
```python
# 创建脚本生命周期管理器 app/services/script_lifecycle.py
class ScriptLifecycleManager:
    """脚本生命周期管理器"""

    def __init__(self):
        self.lifecycle_hooks = {
            'before_start': [],
            'after_start': [],
            'before_stop': [],
            'after_stop': [],
            'on_error': [],
            'on_timeout': []
        }

    def add_hook(self, event, hook_func):
        """添加生命周期钩子"""
        if event in self.lifecycle_hooks:
            self.lifecycle_hooks[event].append(hook_func)

    async def trigger_hooks(self, event, context):
        """触发生命周期钩子"""
        if event not in self.lifecycle_hooks:
            return

        results = []
        for hook in self.lifecycle_hooks[event]:
            try:
                result = await hook(context)
                results.append(result)
            except Exception as e:
                logger.error(f"生命周期钩子执行失败: {e}")

        return results

    async def start_script(self, script_id, context):
        """启动脚本（带生命周期）"""
        # 前置钩子
        await self.trigger_hooks('before_start', context)

        try:
            # 启动脚本
            execution_id = await script_executor.execute_script(script_id, context)

            # 后置钩子
            context['execution_id'] = execution_id
            await self.trigger_hooks('after_start', context)

            return execution_id

        except Exception as e:
            # 错误钩子
            await self.trigger_hooks('on_error', {'error': e, **context})
            raise

    async def stop_script(self, execution_id, context):
        """停止脚本（带生命周期）"""
        # 前置钩子
        await self.trigger_hooks('before_stop', context)

        try:
            # 停止脚本
            result = await script_executor.stop_script(execution_id)

            # 后置钩子
            context['result'] = result
            await self.trigger_hooks('after_stop', context)

            return result

        except Exception as e:
            # 错误钩子
            await self.trigger_hooks('on_error', {'error': e, **context})
            raise
```

---

## 5. 浏览器页面功能模块扩展建议

### 5.1 模块化前端架构

**现状问题：**
- 前端代码组织不够模块化
- 缺少组件复用机制

**优化建议：**
```javascript
// 创建前端模块系统 static/js/modules/module-system.js
class ModuleSystem {
    constructor() {
        this.modules = new Map();
        this.loadedModules = new Set();
        this.dependencies = new Map();
    }

    define(name, dependencies, factory) {
        """定义模块"""
        this.modules.set(name, {
            dependencies: dependencies || [],
            factory: factory,
            instance: null
        });

        this.dependencies.set(name, dependencies || []);
    }

    async load(name) {
        """加载模块"""
        if (this.loadedModules.has(name)) {
            return this.modules.get(name).instance;
        }

        const module = this.modules.get(name);
        if (!module) {
            throw new Error(`模块未找到: ${name}`);
        }

        // 加载依赖
        const deps = [];
        for (const dep of module.dependencies) {
            deps.push(await this.load(dep));
        }

        // 创建模块实例
        const instance = module.factory(...deps);
        module.instance = instance;
        this.loadedModules.add(name);

        return instance;
    }

    get(name) {
        """获取已加载的模块"""
        const module = this.modules.get(name);
        return module ? module.instance : null;
    }
}

// 全局模块系统实例
window.ModuleSystem = new ModuleSystem();
```

### 5.2 动态组件加载

**优化建议：**
```javascript
// 创建动态组件加载器 static/js/components/dynamic-loader.js
class DynamicComponentLoader {
    constructor() {
        this.componentCache = new Map();
        this.loadingPromises = new Map();
    }

    async loadComponent(name, config = {}) {
        """动态加载组件"""
        if (this.componentCache.has(name)) {
            return this.componentCache.get(name);
        }

        if (this.loadingPromises.has(name)) {
            return this.loadingPromises.get(name);
        }

        const loadPromise = this._loadComponentImpl(name, config);
        this.loadingPromises.set(name, loadPromise);

        try {
            const component = await loadPromise;
            this.componentCache.set(name, component);
            return component;
        } finally {
            this.loadingPromises.delete(name);
        }
    }

    async _loadComponentImpl(name, config) {
        """实际加载组件实现"""
        // 动态加载CSS
        if (config.css) {
            await this._loadCSS(config.css);
        }

        // 动态加载JS
        if (config.js) {
            await this._loadJS(config.js);
        }

        // 动态加载HTML模板
        let template = null;
        if (config.template) {
            template = await this._loadTemplate(config.template);
        }

        // 创建组件类
        const ComponentClass = config.componentClass || this._createDefaultComponent(name);

        return new ComponentClass({
            name: name,
            template: template,
            config: config
        });
    }

    async _loadCSS(url) {
        """加载CSS文件"""
        return new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = url;
            link.onload = resolve;
            link.onerror = reject;
            document.head.appendChild(link);
        });
    }

    async _loadJS(url) {
        """加载JS文件"""
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = url;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    async _loadTemplate(url) {
        """加载HTML模板"""
        const response = await fetch(url);
        return await response.text();
    }
}

// 全局组件加载器实例
window.ComponentLoader = new DynamicComponentLoader();
```

---

## 6. 中文化说明注解优化建议

### 6.1 统一注释规范

**现状问题：**
- 代码注释语言不统一
- 缺少标准化的注释格式

**优化建议：**
```python
# 创建注释规范检查工具 scripts/tools/comment_checker.py
class CommentChecker:
    """注释规范检查器"""

    def __init__(self):
        self.rules = {
            'language': 'zh-CN',  # 注释必须使用中文
            'format': {
                'function': '"""函数功能描述"""',
                'class': '"""类功能描述"""',
                'module': '"""模块功能描述"""'
            },
            'completeness': {
                'function': ['purpose', 'params', 'return', 'raises'],
                'class': ['purpose', 'attributes', 'methods']
            }
        }

    def check_file(self, file_path):
        """检查文件注释规范"""
        issues = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查模块级注释
        if not self._has_module_docstring(content):
            issues.append({
                'type': 'missing_module_docstring',
                'line': 1,
                'message': '文件缺少模块级文档字符串'
            })

        # 检查函数注释
        function_issues = self._check_function_comments(content)
        issues.extend(function_issues)

        # 检查类注释
        class_issues = self._check_class_comments(content)
        issues.extend(class_issues)

        return issues

    def _has_module_docstring(self, content):
        """检查是否有模块文档字符串"""
        lines = content.split('\n')
        in_docstring = False
        quote_char = None

        for line in lines[:10]:  # 检查前10行
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                    quote_char = stripped[:3]
                elif stripped.endswith(quote_char):
                    return True

        return False

    def _check_function_comments(self, content):
        """检查函数注释"""
        issues = []
        # 实现函数注释检查逻辑
        return issues

    def _check_class_comments(self, content):
        """检查类注释"""
        issues = []
        # 实现类注释检查逻辑
        return issues
```

### 6.2 自动注释生成工具

**优化建议：**
```python
# 创建自动注释生成器 scripts/tools/auto_comment.py
class AutoCommentGenerator:
    """自动注释生成器"""

    def __init__(self):
        self.templates = {
            'function': '''
    """{function_name}

    {description}

    Args:
        {args}

    Returns:
        {returns}

    Raises:
        {raises}
    """
            ''',
            'class': '''
    """{class_name}

    {description}

    Attributes:
        {attributes}

    Methods:
        {methods}
    """
            ''',
            'module': '''
    """{module_name}

    {description}

    Author: {author}
    Version: {version}
    """
            '''
        }

    def generate_function_comment(self, func_node):
        """生成函数注释"""
        # 解析函数信息
        func_info = self._parse_function(func_node)

        # 填充模板
        comment = self.templates['function'].format(**func_info)

        return comment.strip()

    def generate_class_comment(self, class_node):
        """生成类注释"""
        # 解析类信息
        class_info = self._parse_class(class_node)

        # 填充模板
        comment = self.templates['class'].format(**class_info)

        return comment.strip()

    def _parse_function(self, func_node):
        """解析函数信息"""
        # 实现函数解析逻辑
        return {
            'function_name': func_node.name,
            'description': '函数功能描述',
            'args': self._format_args(func_node.args),
            'returns': '返回值描述',
            'raises': '异常描述'
        }

    def _parse_class(self, class_node):
        """解析类信息"""
        # 实现类解析逻辑
        return {
            'class_name': class_node.name,
            'description': '类功能描述',
            'attributes': '属性列表',
            'methods': '方法列表'
        }

    def _format_args(self, args):
        """格式化参数"""
        formatted = []
        for arg in args:
            formatted.append(f"        {arg.arg} ({arg.annotation or 'Any'}): 参数描述")
        return '\n'.join(formatted)
```

---

## 7. 运行过程优化建议

### 7.1 队列管理系统

**现状问题：**
- 任务队列缺乏优先级管理
- 缺少队列状态监控

**优化建议：**
```python
# 创建高级队列管理器 app/services/queue_manager.py
class AdvancedQueueManager:
    """高级队列管理器"""

    def __init__(self):
        self.queues = {}
        self.processing_tasks = {}
        self.metrics = {
            'enqueued': 0,
            'processed': 0,
            'failed': 0,
            'retries': 0
        }

    def create_queue(self, name, config=None):
        """创建队列"""
        config = config or {}
        self.queues[name] = {
            'items': [],
            'config': {
                'max_size': config.get('max_size', 1000),
                'priority_levels': config.get('priority_levels', 3),
                'retry_policy': config.get('retry_policy', {'max_retries': 3, 'backoff': 1.5}),
                **config
            },
            'stats': {
                'enqueued': 0,
                'processed': 0,
                'failed': 0,
                'avg_processing_time': 0
            }
        }

    def enqueue(self, queue_name, item, priority=1, delay=0):
        """添加任务到队列"""
        if queue_name not in self.queues:
            raise ValueError(f"队列不存在: {queue_name}")

        queue = self.queues[queue_name]

        # 检查队列大小限制
        if len(queue['items']) >= queue['config']['max_size']:
            raise Exception(f"队列已满: {queue_name}")

        task = {
            'id': str(uuid.uuid4()),
            'item': item,
            'priority': priority,
            'enqueue_time': datetime.now(),
            'delay_until': datetime.now() + timedelta(seconds=delay),
            'retry_count': 0,
            'status': 'queued'
        }

        # 按优先级插入
        self._insert_by_priority(queue['items'], task)

        queue['stats']['enqueued'] += 1
        self.metrics['enqueued'] += 1

        return task['id']

    def dequeue(self, queue_name):
        """从队列获取任务"""
        if queue_name not in self.queues:
            return None

        queue = self.queues[queue_name]
        now = datetime.now()

        # 查找可执行的任务（考虑延迟）
        for i, task in enumerate(queue['items']):
            if task['delay_until'] <= now:
                task['dequeue_time'] = now
                task['status'] = 'processing'
                self.processing_tasks[task['id']] = task
                del queue['items'][i]
                return task

        return None

    def complete_task(self, task_id, result=None):
        """完成任务"""
        if task_id not in self.processing_tasks:
            return False

        task = self.processing_tasks[task_id]
        task['status'] = 'completed'
        task['result'] = result
        task['complete_time'] = datetime.now()

        # 计算处理时间
        processing_time = (task['complete_time'] - task['dequeue_time']).total_seconds()

        # 更新统计
        queue_name = self._find_queue_by_task(task_id)
        if queue_name:
            queue = self.queues[queue_name]
            queue['stats']['processed'] += 1

            # 更新平均处理时间
            total_time = queue['stats']['avg_processing_time'] * (queue['stats']['processed'] - 1)
            queue['stats']['avg_processing_time'] = (total_time + processing_time) / queue['stats']['processed']

        self.metrics['processed'] += 1
        del self.processing_tasks[task_id]

        return True

    def fail_task(self, task_id, error=None, retry=True):
        """任务失败"""
        if task_id not in self.processing_tasks:
            return False

        task = self.processing_tasks[task_id]
        task['status'] = 'failed'
        task['error'] = error
        task['fail_time'] = datetime.now()

        queue_name = self._find_queue_by_task(task_id)
        if queue_name and retry:
            queue = self.queues[queue_name]
            retry_policy = queue['config']['retry_policy']

            if task['retry_count'] < retry_policy['max_retries']:
                # 重新入队（带退避延迟）
                delay = retry_policy['backoff'] ** task['retry_count']
                task['retry_count'] += 1
                task['status'] = 'retrying'

                self.enqueue(queue_name, task['item'], task['priority'], delay)
                self.metrics['retries'] += 1
            else:
                # 超过重试次数
                queue['stats']['failed'] += 1
                self.metrics['failed'] += 1

        del self.processing_tasks[task_id]
        return True

    def _insert_by_priority(self, items, task):
        """按优先级插入任务"""
        # 实现优先级队列插入逻辑
        pass

    def _find_queue_by_task(self, task_id):
        """根据任务ID找到队列"""
        for name, queue in self.queues.items():
            if any(t['id'] == task_id for t in queue['items']):
                return name
        return None

    def get_queue_stats(self, queue_name=None):
        """获取队列统计信息"""
        if queue_name:
            return self.queues.get(queue_name, {}).get('stats')
        else:
            return {name: queue['stats'] for name, queue in self.queues.items()}

    def get_system_stats(self):
        """获取系统级统计"""
        return {
            **self.metrics,
            'active_queues': len(self.queues),
            'processing_tasks': len(self.processing_tasks),
            'total_queued': sum(len(q['items']) for q in self.queues.values())
        }
```

### 7.2 错误处理和恢复机制

**优化建议：**
```python
# 创建错误处理和恢复系统 app/services/error_handler.py
class ErrorHandler:
    """错误处理和恢复系统"""

    def __init__(self):
        self.error_patterns = {}
        self.recovery_actions = {}
        self.error_history = deque(maxlen=1000)

    def register_error_pattern(self, pattern, handler, recovery_action=None):
        """注册错误模式"""
        self.error_patterns[pattern] = {
            'handler': handler,
            'recovery': recovery_action
        }

    def handle_error(self, error, context=None):
        """处理错误"""
        error_info = {
            'error': str(error),
            'type': type(error).__name__,
            'context': context or {},
            'timestamp': datetime.now(),
            'traceback': traceback.format_exc()
        }

        # 记录错误历史
        self.error_history.append(error_info)

        # 匹配错误模式
        for pattern, config in self.error_patterns.items():
            if self._matches_pattern(error, pattern):
                try:
                    # 执行错误处理器
                    result = config['handler'](error, context)

                    # 执行恢复动作
                    if config['recovery'] and result.get('should_recover', False):
                        recovery_result = config['recovery'](error, context)
                        error_info['recovery'] = recovery_result

                    return result

                except Exception as recovery_error:
                    logger.error(f"错误恢复失败: {recovery_error}")
                    error_info['recovery_failed'] = str(recovery_error)

        # 默认错误处理
        return self._default_error_handler(error, context)

    def _matches_pattern(self, error, pattern):
        """检查错误是否匹配模式"""
        error_str = str(error).lower()
        pattern_str = pattern.lower()

        # 支持正则表达式匹配
        if pattern.startswith('regex:'):
            import re
            regex = pattern[6:]
            return bool(re.search(regex, error_str))

        # 简单字符串匹配
        return pattern_str in error_str

    def _default_error_handler(self, error, context):
        """默认错误处理器"""
        logger.error(f"未处理的错误: {error}", extra={'context': context})

        return {
            'handled': False,
            'level': 'error',
            'message': f'系统错误: {str(error)}',
            'should_recover': False
        }

    def get_error_stats(self):
        """获取错误统计"""
        stats = {
            'total_errors': len(self.error_history),
            'error_types': {},
            'recent_errors': list(self.error_history)[-10:]
        }

        for error in self.error_history:
            error_type = error['type']
            stats['error_types'][error_type] = stats['error_types'].get(error_type, 0) + 1

        return stats

    def export_error_report(self, start_time=None, end_time=None):
        """导出错误报告"""
        errors = list(self.error_history)

        if start_time:
            errors = [e for e in errors if e['timestamp'] >= start_time]
        if end_time:
            errors = [e for e in errors if e['timestamp'] <= end_time]

        return {
            'period': {
                'start': start_time,
                'end': end_time
            },
            'errors': errors,
            'stats': self.get_error_stats()
        }
```

### 7.3 沉积内容清理机制

**优化建议：**
```python
# 创建内容清理系统 app/services/content_cleaner.py
class ContentCleaner:
    """内容清理系统"""

    def __init__(self):
        self.cleanup_rules = {}
        self.cleanup_history = []

    def register_cleanup_rule(self, name, detector, cleaner, schedule=None):
        """注册清理规则"""
        self.cleanup_rules[name] = {
            'detector': detector,  # 检测函数
            'cleaner': cleaner,    # 清理函数
            'schedule': schedule,  # 清理计划
            'last_run': None,
            'stats': {
                'detected': 0,
                'cleaned': 0,
                'errors': 0
            }
        }

    async def run_cleanup(self, rule_name=None, dry_run=False):
        """执行清理"""
        if rule_name:
            rules = [rule_name] if rule_name in self.cleanup_rules else []
        else:
            rules = list(self.cleanup_rules.keys())

        results = {}

        for name in rules:
            rule = self.cleanup_rules[name]

            try:
                # 检测需要清理的内容
                detected_items = await rule['detector']()

                if not detected_items:
                    results[name] = {'status': 'no_items', 'count': 0}
                    continue

                rule['stats']['detected'] += len(detected_items)

                if dry_run:
                    results[name] = {
                        'status': 'dry_run',
                        'detected': len(detected_items),
                        'items': detected_items[:10]  # 只显示前10个
                    }
                else:
                    # 执行清理
                    cleaned_count = 0
                    for item in detected_items:
                        try:
                            await rule['cleaner'](item)
                            cleaned_count += 1
                        except Exception as e:
                            logger.error(f"清理项目失败: {item}, 错误: {e}")
                            rule['stats']['errors'] += 1

                    rule['stats']['cleaned'] += cleaned_count
                    results[name] = {
                        'status': 'completed',
                        'detected': len(detected_items),
                        'cleaned': cleaned_count
                    }

                rule['last_run'] = datetime.now()

            except Exception as e:
                results[name] = {'status': 'error', 'error': str(e)}
                rule['stats']['errors'] += 1

        self.cleanup_history.append({
            'timestamp': datetime.now(),
            'rule_name': rule_name,
            'results': results,
            'dry_run': dry_run
        })

        return results

    def get_cleanup_stats(self):
        """获取清理统计"""
        return {name: rule['stats'] for name, rule in self.cleanup_rules.items()}

    def get_cleanup_history(self, limit=20):
        """获取清理历史"""
        return list(self.cleanup_history)[-limit:]
```

---

## 8. 页面内容呈现优化建议

### 8.1 响应式布局增强

**现状问题：**
- 页面在不同设备上显示效果不佳
- 缺少自适应布局机制

**优化建议：**
```css
/* 创建响应式布局系统 static/css/responsive-layout.css */
/* 断点定义 */
:root {
    --breakpoint-xs: 480px;
    --breakpoint-sm: 768px;
    --breakpoint-md: 1024px;
    --breakpoint-lg: 1200px;
    --breakpoint-xl: 1440px;
}

/* 响应式工具类 */
.d-none { display: none !important; }
.d-block { display: block !important; }
.d-flex { display: flex !important; }
.d-grid { display: grid !important; }

@media (min-width: 768px) {
    .d-sm-none { display: none !important; }
    .d-sm-block { display: block !important; }
    .d-sm-flex { display: flex !important; }
    .d-sm-grid { display: grid !important; }
}

@media (min-width: 1024px) {
    .d-md-none { display: none !important; }
    .d-md-block { display: block !important; }
    .d-md-flex { display: flex !important; }
    .d-md-grid { display: grid !important; }
}

/* 响应式网格系统 */
.grid-responsive {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
}

@media (min-width: 768px) {
    .grid-responsive {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (min-width: 1024px) {
    .grid-responsive {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (min-width:

---

**文档版本**: 1.0.6  
**创建日期**: 2025年1月  
**最后更新**: 2025-02-08  
**适用范围**: YL-Monitor 项目优化
