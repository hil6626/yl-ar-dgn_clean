/**
 * YL-Monitor UI组件库
 * 功能：通用UI组件（导航栏、卡片、按钮、表格等）
 * 版本：v1.0.0
 * 创建时间：2026-02-10
 */

class UIComponents {
    constructor() {
        this.components = new Map();
        this.eventListeners = new Map();
    }

    /**
     * 注册自定义组件
     */
    register(name, componentClass) {
        this.components.set(name, componentClass);
        console.log(`[UIComponents] 注册组件: ${name}`);
    }

    /**
     * 创建组件实例
     */
    create(name, props = {}) {
        const Component = this.components.get(name);
        if (!Component) {
            throw new Error(`[UIComponents] 组件 "${name}" 未注册`);
        }
        return new Component(props);
    }

    /**
     * 渲染导航栏
     */
    renderNavbar(mountId, props) {
        const mount = document.getElementById(mountId);
        if (!mount) {
            console.warn(`[UIComponents] 导航栏挂载点 "${mountId}" 不存在`);
            return;
        }

        const {
            logo = '/static/img/logo.svg',
            brandText = '浏览器监控平台',
            items = [],
            theme = 'light',
            user = null
        } = props;

        mount.innerHTML = `
            <nav class="navbar">
                <div class="navbar-brand">
                    <img src="${logo}" alt="Logo" class="logo">
                    <span class="brand-text">${brandText}</span>
                </div>
                <div class="navbar-nav">
                    ${items.map(item => `
                        <a href="${item.href || '#'}" 
                           class="nav-item ${item.active ? 'active' : ''}"
                           data-page="${item.id}"
                           data-action="${item.action || ''}">
                            <span class="nav-icon">${item.icon || ''}</span>
                            <span class="nav-label">${item.label}</span>
                        </a>
                    `).join('')}
                </div>
                ${user ? `
                    <div class="navbar-user">
                        <span class="user-name">${user.name}</span>
                        <button class="btn btn-icon" data-action="logout">
                            <span>🚪</span>
                        </button>
                    </div>
                ` : ''}
            </nav>
        `;

        // 绑定导航点击事件
        this.bindNavEvents(mount);
    }

    /**
     * 绑定导航事件
     */
    bindNavEvents(container) {
        const navItems = container.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const action = item.dataset.action;
                const page = item.dataset.page;
                
                if (action) {
                    e.preventDefault();
                    this.emit('navAction', { action, page, element: item });
                }
            });
        });
    }

    /**
     * 渲染概览卡片
     */
    renderOverviewCards(mountId, props) {
        const mount = document.getElementById(mountId);
        if (!mount) return;

        const {
            layout = 'grid-4',
            cards = []
        } = props;

        mount.className = `overview-section layout-${layout}`;
        
        mount.innerHTML = cards.map(card => `
            <div class="overview-card ${card.theme || ''}" data-card-id="${card.id || ''}">
                <div class="card-header">
                    <div class="card-icon">${card.icon || '📊'}</div>
                    <div class="card-menu">
                        <button class="btn-icon" data-action="card-menu">⋮</button>
                    </div>
                </div>
                <div class="card-title">${card.title || '未命名'}</div>
                <div class="card-value" data-value="${card.value || 0}">${card.value || 0}</div>
                ${card.trend ? `
                    <div class="card-trend ${card.trend.direction}">
                        <span>${card.trend.direction === 'up' ? '↑' : '↓'}</span>
                        <span>${card.trend.value}%</span>
                    </div>
                ` : ''}
            </div>
        `).join('');

        // 绑定卡片事件
        this.bindCardEvents(mount);
    }

    /**
     * 绑定卡片事件
     */
    bindCardEvents(container) {
        const cards = container.querySelectorAll('.overview-card');
        cards.forEach(card => {
            // 点击卡片
            card.addEventListener('click', () => {
                const cardId = card.dataset.cardId;
                this.emit('cardClick', { cardId, element: card });
            });

            // 菜单按钮
            const menuBtn = card.querySelector('[data-action="card-menu"]');
            if (menuBtn) {
                menuBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const cardId = card.dataset.cardId;
                    this.emit('cardMenu', { cardId, element: card });
                });
            }
        });
    }

    /**
     * 渲染按钮
     */
    renderButton(props) {
        const {
            variant = 'primary',
            size = 'md',
            icon = null,
            label = '',
            disabled = false,
            loading = false,
            glow = false,
            onClick = null
        } = props;

        const btn = document.createElement('button');
        btn.className = `btn btn-${variant} btn-${size} ${glow ? 'btn-glow' : ''} ${loading ? 'loading' : ''}`;
        btn.disabled = disabled || loading;

        btn.innerHTML = `
            ${icon ? `<span class="btn-icon">${icon}</span>` : ''}
            <span class="btn-text">${loading ? '加载中...' : label}</span>
            ${loading ? '<span class="btn-spinner"></span>' : ''}
        `;

        if (onClick && !disabled && !loading) {
            btn.addEventListener('click', onClick);
        }

        return btn;
    }

    /**
     * 渲染表格
     */
    renderTable(mountId, props) {
        const mount = document.getElementById(mountId);
        if (!mount) return;

        const {
            columns = [],
            data = [],
            striped = true,
            hover = true,
            selectable = false
        } = props;

        mount.innerHTML = `
            <table class="data-table ${striped ? 'striped' : ''} ${hover ? 'hover' : ''}">
                <thead>
                    <tr>
                        ${selectable ? '<th class="col-select"><input type="checkbox" class="select-all"></th>' : ''}
                        ${columns.map(col => `
                            <th class="col-${col.key} ${col.sortable ? 'sortable' : ''}" 
                                data-key="${col.key}">
                                ${col.label}
                                ${col.sortable ? '<span class="sort-icon">↕</span>' : ''}
                            </th>
                        `).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${data.map((row, index) => `
                        <tr data-index="${index}">
                            ${selectable ? `<td class="col-select"><input type="checkbox" class="select-row"></td>` : ''}
                            ${columns.map(col => `
                                <td class="col-${col.key}">
                                    ${col.render ? col.render(row[col.key], row) : row[col.key]}
                                </td>
                            `).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        // 绑定表格事件
        this.bindTableEvents(mount, props);
    }

    /**
     * 绑定表格事件
     */
    bindTableEvents(container, props) {
        const { sortable = false, selectable = false } = props;

        // 排序
        if (sortable) {
            const headers = container.querySelectorAll('th.sortable');
            headers.forEach(header => {
                header.addEventListener('click', () => {
                    const key = header.dataset.key;
                    this.emit('tableSort', { key, element: header });
                });
            });
        }

        // 选择
        if (selectable) {
            const selectAll = container.querySelector('.select-all');
            const selectRows = container.querySelectorAll('.select-row');

            if (selectAll) {
                selectAll.addEventListener('change', (e) => {
                    selectRows.forEach(row => row.checked = e.target.checked);
                    this.emit('tableSelectAll', { checked: e.target.checked });
                });
            }

            selectRows.forEach((row, index) => {
                row.addEventListener('change', () => {
                    this.emit('tableSelectRow', { index, checked: row.checked });
                });
            });
        }
    }

    /**
     * 渲染模态框
     */
    renderModal(props) {
        const {
            title = '',
            content = '',
            size = 'md',
            closable = true,
            buttons = []
        } = props;

        const modalId = 'modal-' + Date.now();
        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = `modal modal-${size}`;
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-container">
                <div class="modal-header">
                    <h3 class="modal-title">${title}</h3>
                    ${closable ? '<button class="modal-close" data-action="close">×</button>' : ''}
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                ${buttons.length > 0 ? `
                    <div class="modal-footer">
                        ${buttons.map(btn => `
                            <button class="btn btn-${btn.variant || 'secondary'}" 
                                    data-action="${btn.action || ''}">
                                ${btn.label}
                            </button>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;

        // 绑定关闭事件
        if (closable) {
            const closeBtn = modal.querySelector('[data-action="close"]');
            const overlay = modal.querySelector('.modal-overlay');
            
            closeBtn?.addEventListener('click', () => this.closeModal(modalId));
            overlay?.addEventListener('click', () => this.closeModal(modalId));
        }

        // 绑定按钮事件
        buttons.forEach(btn => {
            const btnEl = modal.querySelector(`[data-action="${btn.action}"]`);
            if (btnEl && btn.onClick) {
                btnEl.addEventListener('click', () => {
                    btn.onClick();
                    if (btn.closeOnClick !== false) {
                        this.closeModal(modalId);
                    }
                });
            }
        });

        document.body.appendChild(modal);
        
        // 动画显示
        requestAnimationFrame(() => {
            modal.classList.add('show');
        });

        return modalId;
    }

    /**
     * 关闭模态框
     */
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300);
        }
    }

    /**
     * 显示Toast通知
     */
    showToast(props) {
        const {
            message = '',
            type = 'info', // info, success, warning, error
            duration = 3000,
            closable = true
        } = props;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${this.getToastIcon(type)}</span>
            <span class="toast-message">${message}</span>
            ${closable ? '<button class="toast-close">×</button>' : ''}
        `;

        const container = document.getElementById('toast-mount') || document.body;
        container.appendChild(toast);

        // 动画显示
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // 自动关闭
        if (duration > 0) {
            setTimeout(() => this.closeToast(toast), duration);
        }

        // 手动关闭
        if (closable) {
            toast.querySelector('.toast-close')?.addEventListener('click', () => {
                this.closeToast(toast);
            });
        }

        return toast;
    }

    /**
     * 获取Toast图标
     */
    getToastIcon(type) {
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            error: '❌'
        };
        return icons[type] || icons.info;
    }

    /**
     * 关闭Toast
     */
    closeToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }

    /**
     * 渲染加载状态
     */
    renderLoading(mountId, props = {}) {
        const mount = document.getElementById(mountId);
        if (!mount) return;

        const { text = '加载中...', size = 'md' } = props;

        mount.innerHTML = `
            <div class="loading-container loading-${size}">
                <div class="loading-spinner"></div>
                <span class="loading-text">${text}</span>
            </div>
        `;
    }

    /**
     * 渲染空状态
     */
    renderEmpty(mountId, props = {}) {
        const mount = document.getElementById(mountId);
        if (!mount) return;

        const {
            icon = '📭',
            title = '暂无数据',
            description = '',
            action = null
        } = props;

        mount.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">${icon}</span>
                <h4 class="empty-title">${title}</h4>
                ${description ? `<p class="empty-description">${description}</p>` : ''}
                ${action ? `
                    <button class="btn btn-primary" data-action="${action.name}">
                        ${action.label}
                    </button>
                ` : ''}
            </div>
        `;

        if (action) {
            const btn = mount.querySelector(`[data-action="${action.name}"]`);
            btn?.addEventListener('click', action.onClick);
        }
    }

    /**
     * 渲染错误状态
     */
    renderError(mountId, props = {}) {
        const mount = document.getElementById(mountId);
        if (!mount) return;

        const {
            icon = '❌',
            title = '出错了',
            message = '',
            retry = null
        } = props;

        mount.innerHTML = `
            <div class="error-state">
                <span class="error-icon">${icon}</span>
                <h4 class="error-title">${title}</h4>
                ${message ? `<p class="error-message">${message}</p>` : ''}
                ${retry ? `
                    <button class="btn btn-primary" data-action="retry">
                        <span>🔄</span> ${retry.label || '重试'}
                    </button>
                ` : ''}
            </div>
        `;

        if (retry) {
            const btn = mount.querySelector('[data-action="retry"]');
            btn?.addEventListener('click', retry.onClick);
        }
    }

    /**
     * 事件发射
     */
    emit(eventName, data) {
        const event = new CustomEvent(`ui:${eventName}`, { detail: data });
        document.dispatchEvent(event);
        
        // 也调用直接注册的监听器
        const listeners = this.eventListeners.get(eventName);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`[UIComponents] 事件处理错误: ${eventName}`, error);
                }
            });
        }
    }

    /**
     * 事件监听
     */
    on(eventName, callback) {
        if (!this.eventListeners.has(eventName)) {
            this.eventListeners.set(eventName, new Set());
        }
        this.eventListeners.get(eventName).add(callback);

        // 返回取消订阅函数
        return () => {
            this.eventListeners.get(eventName)?.delete(callback);
        };
    }

    /**
     * 一次性事件监听
     */
    once(eventName, callback) {
        const unsubscribe = this.on(eventName, (data) => {
            unsubscribe();
            callback(data);
        });
    }

    /**
     * 显示确认弹窗（删除确认机制）
     */
    showConfirm(props) {
        const {
            title = '确认操作',
            message = '您确定要执行此操作吗？',
            confirmText = '确认',
            cancelText = '取消',
            type = 'warning', // warning, danger, info
            onConfirm = () => {},
            onCancel = () => {}
        } = props;

        const icons = {
            warning: '⚠️',
            danger: '🗑️',
            info: 'ℹ️'
        };

        const modalId = 'confirm-modal-' + Date.now();
        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'modal modal-sm modal-confirm';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-container">
                <div class="modal-body text-center">
                    <div class="confirm-icon" style="font-size: 3rem; margin-bottom: 1rem;">${icons[type]}</div>
                    <h3 class="modal-title" style="margin-bottom: 0.5rem;">${title}</h3>
                    <p class="confirm-message" style="color: var(--text-secondary); margin-bottom: 1.5rem;">${message}</p>
                    <div class="confirm-actions" style="display: flex; gap: 1rem; justify-content: center;">
                        <button class="btn btn-secondary" data-action="cancel">${cancelText}</button>
                        <button class="btn btn-${type === 'danger' ? 'danger' : 'primary'}" data-action="confirm">${confirmText}</button>
                    </div>
                </div>
            </div>
        `;

        // 绑定事件
        const confirmBtn = modal.querySelector('[data-action="confirm"]');
        const cancelBtn = modal.querySelector('[data-action="cancel"]');
        const overlay = modal.querySelector('.modal-overlay');

        confirmBtn.addEventListener('click', () => {
            onConfirm();
            this.closeModal(modalId);
        });

        cancelBtn.addEventListener('click', () => {
            onCancel();
            this.closeModal(modalId);
        });

        overlay.addEventListener('click', () => {
            onCancel();
            this.closeModal(modalId);
        });

        document.body.appendChild(modal);
        requestAnimationFrame(() => modal.classList.add('show'));

        return modalId;
    }

    /**
     * 创建表单验证器
     */
    createFormValidator(formSelector) {
        const form = document.querySelector(formSelector);
        if (!form) return null;

        return new FormValidator(form);
    }
}

/**
 * 表单验证器类
 */
class FormValidator {
    constructor(form) {
        this.form = form;
        this.debounceTimer = null;
        this.fields = new Map();
        this.init();
    }

    init() {
        // 获取所有需要验证的字段
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(field => {
            if (field.dataset.validate) {
                this.fields.set(field.name || field.id, {
                    element: field,
                    rules: this.parseRules(field.dataset.validate),
                    touched: false
                });

                // 绑定事件
                field.addEventListener('input', (e) => this.validateField(e.target));
                field.addEventListener('blur', (e) => this.validateField(e.target, true));
            }
        });

        // 表单提交验证
        this.form.addEventListener('submit', (e) => {
            if (!this.validateAll()) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    }

    parseRules(validateAttr) {
        const rules = [];
        const ruleStrings = validateAttr.split('|');
        
        ruleStrings.forEach(ruleStr => {
            const [ruleName, ...params] = ruleStr.split(':');
            rules.push({ name: ruleName, params });
        });

        return rules;
    }

    validateField(field, markTouched = false) {
        const fieldName = field.name || field.id;
        const fieldData = this.fields.get(fieldName);
        if (!fieldData) return true;

        if (markTouched) {
            fieldData.touched = true;
        }

        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            const errors = [];
            
            fieldData.rules.forEach(rule => {
                const error = this.checkRule(field, rule);
                if (error) errors.push(error);
            });

            this.showFeedback(field, errors.length === 0, errors[0]);
            return errors.length === 0;
        }, 300);
    }

    checkRule(field, rule) {
        const value = field.value.trim();
        
        switch (rule.name) {
            case 'required':
                if (!value) return '此字段为必填项';
                break;
            case 'email':
                if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                    return '请输入有效的邮箱地址';
                }
                break;
            case 'min':
                if (value.length < parseInt(rule.params[0])) {
                    return `最少需要 ${rule.params[0]} 个字符`;
                }
                break;
            case 'max':
                if (value.length > parseInt(rule.params[0])) {
                    return `最多允许 ${rule.params[0]} 个字符`;
                }
                break;
            case 'number':
                if (value && isNaN(value)) {
                    return '请输入数字';
                }
                break;
            case 'url':
                if (value && !/^https?:\/\/.+/.test(value)) {
                    return '请输入有效的URL';
                }
                break;
        }
        
        return null;
    }

    showFeedback(field, isValid, errorMessage) {
        // 移除旧的反馈
        const oldFeedback = field.parentElement.querySelector('.field-feedback');
        if (oldFeedback) oldFeedback.remove();

        // 添加新的反馈
        const feedback = document.createElement('div');
        feedback.className = `field-feedback ${isValid ? 'success' : 'error'}`;
        feedback.style.cssText = `
            font-size: 0.75rem;
            margin-top: 0.25rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        `;
        
        if (isValid) {
            feedback.innerHTML = `<span style="color: var(--success);">✓</span>`;
            field.style.borderColor = 'var(--success)';
        } else {
            feedback.innerHTML = `<span style="color: var(--danger);">✗ ${errorMessage}</span>`;
            field.style.borderColor = 'var(--danger)';
        }

        field.parentElement.appendChild(feedback);
    }

    validateAll() {
        let isValid = true;
        this.fields.forEach((fieldData, fieldName) => {
            fieldData.touched = true;
            const fieldValid = this.validateField(fieldData.element, true);
            if (!fieldValid) isValid = false;
        });
        return isValid;
    }

    reset() {
        this.fields.forEach((fieldData) => {
            fieldData.touched = false;
            fieldData.element.style.borderColor = '';
            const feedback = fieldData.element.parentElement.querySelector('.field-feedback');
            if (feedback) feedback.remove();
        });
    }
}

// ES6 模块导出
export { UIComponents, FormValidator };

// 也支持全局访问（用于非模块环境）
if (typeof window !== 'undefined') {
    window.UIComponents = UIComponents;
    window.FormValidator = FormValidator;
}
