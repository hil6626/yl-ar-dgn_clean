/**
 * YL-Monitor API文档页面逻辑
 * 版本: v8.0.0
 * 特性: 两栏布局、代码高亮、在线测试、curl复制
 */

export default class APIDocPage {
    constructor(deps) {
        this.themeManager = deps.themeManager;
        this.ui = deps.uiComponents;
        this.apiBaseUrl = '/api/v1';
        this.apiData = [];
        this.currentEndpoint = null;
        this.sidebarCollapsed = false;
        this.testPanelOpen = false;
    }

    /**
     * 初始化页面
     */
    async init() {
        console.log('[APIDocPage] 初始化API文档页面...');

        // 1. 渲染头部
        this.renderHeader();

        // 2. 渲染侧边栏
        this.renderSidebar();

        // 3. 加载API数据
        await this.loadAPIData();

        // 4. 渲染主内容区
        this.renderMainContent();

        // 5. 绑定事件
        this.bindEvents();

        // 6. 初始化代码高亮
        this.initCodeHighlight();

        console.log('[APIDocPage] API文档页面初始化完成 ✅');
    }

    /**
     * 渲染头部
     */
    renderHeader() {
        const mount = document.getElementById('api-header-mount');
        if (!mount) return;

        mount.innerHTML = `
            <div class="api-header-content">
                <div class="api-header-title">
                    <span class="icon">📚</span>
                    <div>
                        <h1>API文档中心</h1>
                        <p class="api-header-subtitle">交互式API文档 - 支持在线测试</p>
                    </div>
                </div>
                <div class="api-header-actions">
                    <div class="api-search-box" style="position: relative; margin-right: 12px;">
                        <span class="search-icon" style="position: absolute; left: 12px; top: 50%; transform: translateY(-50%);">🔍</span>
                        <input type="text" id="api-search-input" placeholder="搜索API..." 
                               style="padding: 8px 12px 8px 36px; border: 1px solid rgba(255,255,255,0.3); 
                                      background: rgba(255,255,255,0.1); color: white; border-radius: 6px; width: 240px;">
                    </div>
                    <button class="btn" id="export-api-doc">
                        <span>📥</span> 导出文档
                    </button>
                </div>
            </div>
        `;

        // 绑定搜索事件
        const searchInput = document.getElementById('api-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        }

        // 绑定导出事件
        const exportBtn = document.getElementById('export-api-doc');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportAPIDoc());
        }
    }

    /**
     * 渲染侧边栏
     */
    renderSidebar() {
        const mount = document.getElementById('api-sidebar-mount');
        if (!mount) return;

        mount.innerHTML = `
            <div class="api-sidebar-header">
                <h3>API模块</h3>
                <button class="api-sidebar-toggle" id="sidebar-toggle" title="折叠/展开">
                    <span>◀</span>
                </button>
            </div>
            <div class="api-search-box">
                <span class="search-icon">🔍</span>
                <input type="text" id="sidebar-search" placeholder="筛选模块...">
            </div>
            <ul class="api-modules-list" id="api-modules-list">
                <!-- 动态加载 -->
            </ul>
        `;

        // 绑定折叠按钮
        const toggleBtn = document.getElementById('sidebar-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleSidebar());
        }

        // 绑定侧边栏搜索
        const sidebarSearch = document.getElementById('sidebar-search');
        if (sidebarSearch) {
            sidebarSearch.addEventListener('input', (e) => this.filterSidebar(e.target.value));
        }
    }

    /**
     * 加载API数据
     */
    async loadAPIData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api-doc/endpoints`);
            if (!response.ok) throw new Error('获取API数据失败');
            
            this.apiData = await response.json();
        } catch (error) {
            console.error('[APIDocPage] 获取API数据失败:', error);
            // 使用示例数据
            this.apiData = this.getSampleAPIData();
        }

        // 渲染侧边栏模块列表
        this.renderModulesList();
        
        // 默认选中第一个端点
        if (this.apiData.length > 0 && this.apiData[0].endpoints.length > 0) {
            this.selectEndpoint(this.apiData[0].endpoints[0]);
        }
    }

    /**
     * 获取示例API数据
     */
    getSampleAPIData() {
        return [
            {
                module: '用户管理',
                icon: '👤',
                expanded: true,
                endpoints: [
                    {
                        id: 'user-list',
                        method: 'GET',
                        path: '/api/v1/users',
                        name: '获取用户列表',
                        description: '获取所有用户的列表，支持分页和筛选',
                        params: [
                            { name: 'page', type: 'integer', required: false, description: '页码，默认1' },
                            { name: 'size', type: 'integer', required: false, description: '每页数量，默认20' }
                        ],
                        response: {
                            status: 200,
                            example: {
                                code: 0,
                                data: {
                                    items: [{ id: 1, name: '张三', email: 'zhangsan@example.com' }],
                                    total: 100,
                                    page: 1,
                                    size: 20
                                },
                                message: 'success'
                            }
                        }
                    },
                    {
                        id: 'user-create',
                        method: 'POST',
                        path: '/api/v1/users',
                        name: '创建用户',
                        description: '创建新用户账号',
                        params: [
                            { name: 'name', type: 'string', required: true, description: '用户姓名' },
                            { name: 'email', type: 'string', required: true, description: '邮箱地址' },
                            { name: 'role', type: 'string', required: false, description: '用户角色' }
                        ],
                        body: {
                            name: 'John Doe',
                            email: 'john@example.com',
                            role: 'user'
                        },
                        response: {
                            status: 201,
                            example: {
                                code: 0,
                                data: { id: 1, name: 'John Doe', email: 'john@example.com' },
                                message: '创建成功'
                            }
                        }
                    }
                ]
            },
            {
                module: '告警管理',
                icon: '🚨',
                expanded: false,
                endpoints: [
                    {
                        id: 'alert-list',
                        method: 'GET',
                        path: '/api/v1/alerts',
                        name: '获取告警列表',
                        description: '获取系统告警列表',
                        params: [
                            { name: 'level', type: 'string', required: false, description: '告警级别' },
                            { name: 'status', type: 'string', required: false, description: '告警状态' }
                        ],
                        response: {
                            status: 200,
                            example: {
                                code: 0,
                                data: {
                                    items: [{ id: 1, level: 'critical', message: 'CPU使用率过高' }],
                                    total: 10
                                }
                            }
                        }
                    },
                    {
                        id: 'alert-ack',
                        method: 'POST',
                        path: '/api/v1/alerts/{id}/acknowledge',
                        name: '确认告警',
                        description: '确认指定告警',
                        params: [
                            { name: 'id', type: 'string', required: true, description: '告警ID', in: 'path' }
                        ],
                        response: {
                            status: 200,
                            example: { code: 0, message: '确认成功' }
                        }
                    }
                ]
            },
            {
                module: '系统监控',
                icon: '📊',
                expanded: false,
                endpoints: [
                    {
                        id: 'metrics',
                        method: 'GET',
                        path: '/api/v1/metrics',
                        name: '获取系统指标',
                        description: '获取系统性能指标',
                        params: [],
                        response: {
                            status: 200,
                            example: {
                                code: 0,
                                data: {
                                    cpu: 45.2,
                                    memory: 67.8,
                                    disk: 82.1
                                }
                            }
                        }
                    }
                ]
            }
        ];
    }

    /**
     * 渲染模块列表
     */
    renderModulesList() {
        const list = document.getElementById('api-modules-list');
        if (!list) return;

        list.innerHTML = this.apiData.map((module, moduleIndex) => `
            <li class="api-module-group">
                <div class="api-module-header ${module.expanded ? 'expanded' : ''}" data-module="${moduleIndex}">
                    <span class="toggle-icon">▶</span>
                    <span class="module-icon">${module.icon}</span>
                    <span class="module-name">${module.module}</span>
                </div>
                <ul class="api-module-children ${module.expanded ? 'expanded' : ''}" id="module-${moduleIndex}">
                    ${module.endpoints.map(endpoint => `
                        <li class="api-endpoint-link" 
                            data-endpoint-id="${endpoint.id}"
                            data-module="${moduleIndex}"
                            data-action="select-endpoint">
                            <span class="method-badge http-method ${endpoint.method.toLowerCase()}">${endpoint.method}</span>
                            <span class="endpoint-path">${endpoint.name}</span>
                        </li>
                    `).join('')}
                </ul>
            </li>
        `).join('');

        // 绑定模块展开/折叠
        list.querySelectorAll('.api-module-header').forEach(header => {
            header.addEventListener('click', (e) => {
                const moduleIndex = header.dataset.module;
                const children = document.getElementById(`module-${moduleIndex}`);
                const isExpanded = header.classList.contains('expanded');
                
                header.classList.toggle('expanded', !isExpanded);
                children.classList.toggle('expanded', !isExpanded);
            });
        });
    }

    /**
     * 通过ID选择端点
     */
    selectEndpointById(endpointId) {
        for (const module of this.apiData) {
            const endpoint = module.endpoints.find(e => e.id === endpointId);
            if (endpoint) {
                this.selectEndpoint(endpoint);
                break;
            }
        }
    }

    /**
     * 选择端点
     */
    selectEndpoint(endpoint) {
        this.currentEndpoint = endpoint;

        // 更新侧边栏激活状态
        document.querySelectorAll('.api-endpoint-link').forEach(link => {
            link.classList.toggle('active', link.dataset.endpointId === endpoint.id);
        });

        // 渲染端点详情
        this.renderEndpointDetail(endpoint);
    }

    /**
     * 渲染端点详情
     */
    renderEndpointDetail(endpoint) {
        const mount = document.getElementById('api-content-mount');
        if (!mount) return;

        const curlCommand = this.generateCurlCommand(endpoint);

        mount.innerHTML = `
            <div class="api-endpoint-card">
                <div class="api-endpoint-header">
                    <span class="http-method ${endpoint.method.toLowerCase()}">${endpoint.method}</span>
                    <div class="api-endpoint-title">
                        <h2>${endpoint.name}</h2>
                        <p class="endpoint-description">${endpoint.description}</p>
                    </div>
                </div>
                
                <div class="api-endpoint-body">
                    <!-- API路径 -->
                    <div class="api-section">
                        <h3 class="api-section-title">📍 请求地址</h3>
                        <div class="api-path-full">
                            <code>${endpoint.path}</code>
                            <button class="copy-btn" data-action="copy-to-clipboard" data-text="${endpoint.path}" title="复制路径">
                                📋
                            </button>
                        </div>
                    </div>

                    <!-- 请求参数 -->
                    ${endpoint.params && endpoint.params.length > 0 ? `
                        <div class="api-section">
                            <h3 class="api-section-title">📋 请求参数</h3>
                            <table class="api-params-table">
                                <thead>
                                    <tr>
                                        <th>参数名</th>
                                        <th>类型</th>
                                        <th>必填</th>
                                        <th>说明</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${endpoint.params.map(param => `
                                        <tr>
                                            <td><code class="param-name">${param.name}</code></td>
                                            <td><span class="param-type">${param.type}</span></td>
                                            <td>${param.required ? 
                                                '<span class="param-required">必填</span>' : 
                                                '<span class="param-optional">可选</span>'}</td>
                                            <td>${param.description || '-'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    ` : ''}

                    <!-- 请求体示例 -->
                    ${endpoint.body ? `
                        <div class="api-section">
                            <h3 class="api-section-title">📤 请求体示例</h3>
                            <div class="api-code-block">
                                <div class="api-code-header">
                                    <span>JSON</span>
                                    <button class="copy-btn" data-action="copy-to-clipboard" data-text="${this.escapeJson(endpoint.body)}">
                                        📋 复制
                                    </button>
                                </div>
                                <pre><code class="language-json">${JSON.stringify(endpoint.body, null, 2)}</code></pre>
                            </div>
                        </div>
                    ` : ''}

                    <!-- cURL命令 -->
                    <div class="api-section">
                        <h3 class="api-section-title">🖥️ cURL命令</h3>
                        <div class="api-code-block">
                            <div class="api-code-header">
                                <span>Bash</span>
                                <button class="copy-btn" data-action="copy-to-clipboard" data-text="${this.escapeHtml(curlCommand)}">
                                    📋 复制curl命令
                                </button>
                            </div>
                            <pre><code class="language-bash">${curlCommand}</code></pre>
                        </div>
                    </div>

                    <!-- 响应示例 -->
                    ${endpoint.response ? `
                        <div class="api-section">
                            <h3 class="api-section-title">📥 响应示例</h3>
                            <div class="api-response-status">
                                <span class="status-code ${endpoint.response.status < 400 ? 'success' : 'error'}">
                                    ${endpoint.response.status}
                                </span>
                                <span class="status-message">${endpoint.response.status < 400 ? 'OK' : 'Error'}</span>
                            </div>
                            <div class="api-code-block">
                                <div class="api-code-header">
                                    <span>JSON</span>
                                    <button class="copy-btn" data-action="copy-to-clipboard" data-text="${this.escapeJson(endpoint.response.example)}">
                                        📋 复制
                                    </button>
                                </div>
                                <pre><code class="language-json">${JSON.stringify(endpoint.response.example, null, 2)}</code></pre>
                            </div>
                        </div>
                    ` : ''}

                    <!-- 在线测试按钮 -->
                    <button class="api-test-btn" data-action="open-test-panel">
                        <span>🧪</span> 在线测试API
                    </button>
                </div>
            </div>
        `;

        // 重新初始化代码高亮
        this.initCodeHighlight();
    }

    /**
     * 生成cURL命令
     */
    generateCurlCommand(endpoint) {
        let curl = `curl -X ${endpoint.method} "${window.location.origin}${endpoint.path}"`;

        if (endpoint.method !== 'GET') {
            curl += ' \\\n  -H "Content-Type: application/json"';
        }

        curl += ' \\\n  -H "Authorization: Bearer YOUR_TOKEN_HERE"';

        if (endpoint.body) {
            curl += ` \\\n  -d '${JSON.stringify(endpoint.body)}'`;
        }

        return curl;
    }

    /**
     * 渲染主内容区（空状态）
     */
    renderMainContent() {
        const mount = document.getElementById('api-content-mount');
        if (!mount) return;

        mount.innerHTML = `
            <div class="api-empty-state">
                <div class="api-empty-state-icon">📚</div>
                <div class="api-empty-state-title">选择API端点</div>
                <div class="api-empty-state-desc">从左侧导航栏选择一个API端点查看详情</div>
            </div>
        `;
    }

    /**
     * 打开测试面板
     */
    openTestPanel() {
        if (!this.currentEndpoint) return;

        const endpoint = this.currentEndpoint;
        const panel = document.getElementById('api-test-panel-mount');
        const overlay = document.createElement('div');
        overlay.className = 'api-test-overlay';
        overlay.id = 'api-test-overlay';
        
        document.body.appendChild(overlay);

        panel.innerHTML = `
            <div class="api-test-panel-header">
                <h3>🧪 测试 ${endpoint.name}</h3>
                <button class="api-test-panel-close" data-action="close-test-panel">×</button>
            </div>
            <div class="api-test-panel-body">
                <div class="api-test-form-group">
                    <label>请求方法</label>
                    <input type="text" value="${endpoint.method}" readonly>
                </div>
                <div class="api-test-form-group">
                    <label>请求地址</label>
                    <input type="text" value="${window.location.origin}${endpoint.path}" readonly>
                </div>
                ${endpoint.params && endpoint.params.filter(p => p.in === 'path').map(p => `
                    <div class="api-test-form-group">
                        <label>路径参数: ${p.name}</label>
                        <input type="text" id="param-${p.name}" placeholder="${p.description || ''}">
                    </div>
                `).join('')}
                ${endpoint.method !== 'GET' ? `
                    <div class="api-test-form-group">
                        <label>请求体 (JSON)</label>
                        <textarea id="test-request-body">${endpoint.body ? JSON.stringify(endpoint.body, null, 2) : '{}'}</textarea>
                    </div>
                ` : ''}
                <button class="api-test-submit" data-action="send-test-request">
                    发送请求
                </button>
                <div id="test-result" class="api-test-result" style="display: none;">
                    <h4>响应结果</h4>
                    <pre id="test-response"></pre>
                </div>
            </div>
        `;

        setTimeout(() => {
            panel.classList.add('open');
            overlay.classList.add('open');
        }, 10);

        this.testPanelOpen = true;
    }

    /**
     * 关闭测试面板
     */
    closeTestPanel() {
        const panel = document.getElementById('api-test-panel-mount');
        const overlay = document.getElementById('api-test-overlay');
        
        if (panel) panel.classList.remove('open');
        if (overlay) overlay.classList.remove('open');
        
        setTimeout(() => {
            if (overlay) overlay.remove();
        }, 300);
        
        this.testPanelOpen = false;
    }

    /**
     * 发送测试请求
     */
    async sendTestRequest() {
        if (!this.currentEndpoint) return;

        const endpoint = this.currentEndpoint;
        const resultDiv = document.getElementById('test-result');
        const responsePre = document.getElementById('test-response');
        
        // 构建URL
        let url = `${window.location.origin}${endpoint.path}`;
        endpoint.params?.filter(p => p.in === 'path').forEach(p => {
            const value = document.getElementById(`param-${p.name}`)?.value || '';
            url = url.replace(`{${p.name}}`, value);
        });

        // 构建请求体
        let body = null;
        if (endpoint.method !== 'GET') {
            const bodyText = document.getElementById('test-request-body')?.value || '{}';
            try {
                body = JSON.parse(bodyText);
            } catch (e) {
                responsePre.textContent = '请求体JSON格式错误: ' + e.message;
                resultDiv.style.display = 'block';
                return;
            }
        }

        resultDiv.style.display = 'block';
        responsePre.textContent = '发送请求中...';

        try {
            const response = await fetch(url, {
                method: endpoint.method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer YOUR_TOKEN_HERE'
                },
                body: body ? JSON.stringify(body) : null
            });

            const data = await response.json();
            responsePre.textContent = `状态码: ${response.status}\n\n${JSON.stringify(data, null, 2)}`;
        } catch (error) {
            responsePre.textContent = '请求失败: ' + error.message;
        }
    }

    /**
     * 切换侧边栏
     */
    toggleSidebar() {
        const sidebar = document.getElementById('api-sidebar-mount');
        const toggle = document.getElementById('sidebar-toggle');
        
        this.sidebarCollapsed = !this.sidebarCollapsed;
        sidebar.classList.toggle('collapsed', this.sidebarCollapsed);
        toggle.innerHTML = this.sidebarCollapsed ? '<span>▶</span>' : '<span>◀</span>';
    }

    /**
     * 筛选侧边栏
     */
    filterSidebar(keyword) {
        const links = document.querySelectorAll('.api-endpoint-link');
        const modules = document.querySelectorAll('.api-module-group');
        
        if (!keyword) {
            links.forEach(link => link.style.display = 'flex');
            modules.forEach(m => m.style.display = 'block');
            return;
        }

        const lowerKeyword = keyword.toLowerCase();
        
        links.forEach(link => {
            const text = link.textContent.toLowerCase();
            link.style.display = text.includes(lowerKeyword) ? 'flex' : 'none';
        });

        // 隐藏没有匹配端点的模块
        modules.forEach(module => {
            const visibleLinks = module.querySelectorAll('.api-endpoint-link[style*="flex"]');
            module.style.display = visibleLinks.length > 0 ? 'block' : 'none';
        });
    }

    /**
     * 搜索处理
     */
    handleSearch(keyword) {
        this.filterSidebar(keyword);
    }

    /**
     * 导出API文档
     */
    exportAPIDoc() {
        const doc = {
            title: 'YL-Monitor API文档',
            version: 'v1.0.0',
            generatedAt: new Date().toISOString(),
            modules: this.apiData
        };

        const blob = new Blob([JSON.stringify(doc, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'yl-monitor-api-doc.json';
        a.click();
        URL.revokeObjectURL(url);

        this.ui.showToast({
            type: 'success',
            message: 'API文档已导出'
        });
    }

    /**
     * 复制到剪贴板
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.ui.showToast({
                type: 'success',
                message: '已复制到剪贴板'
            });
        } catch (err) {
            // 降级方案
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            
            this.ui.showToast({
                type: 'success',
                message: '已复制到剪贴板'
            });
        }
    }

    /**
     * 初始化代码高亮
     */
    initCodeHighlight() {
        if (window.hljs) {
            window.hljs.highlightAll();
        }
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 点击遮罩关闭测试面板
        document.addEventListener('click', (e) => {
            if (e.target.id === 'api-test-overlay') {
                this.closeTestPanel();
            }
        });

        // ESC键关闭测试面板
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.testPanelOpen) {
                this.closeTestPanel();
            }
        });
    }

    /**
     * 处理全局动作
     */
    handleAction(action, context, event) {
        switch(action) {
            case 'refresh-api-doc':
                this.loadAPIData();
                break;
            case 'select-endpoint':
                const endpointId = context.dataset.endpointId;
                if (endpointId) this.selectEndpointById(endpointId);
                break;
            case 'copy-to-clipboard':
                const text = context.dataset.text;
                if (text) this.copyToClipboard(text);
                break;
            case 'open-test-panel':
                this.openTestPanel();
                break;
            case 'close-test-panel':
                this.closeTestPanel();
                break;
            case 'send-test-request':
                this.sendTestRequest();
                break;
            default:
                console.log('[APIDocPage] 未处理的动作:', action);
        }
    }

    /**
     * 转义HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 转义JSON
     */
    escapeJson(obj) {
        return this.escapeHtml(JSON.stringify(obj));
    }
}

// 全局引用 - 将在初始化后设置
