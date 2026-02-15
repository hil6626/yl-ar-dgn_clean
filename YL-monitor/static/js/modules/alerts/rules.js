/**
 * 规则管理模块
 * 从 alert-rules-manager.js 提取重构
 */

export class RulesModule {
    constructor(alertCenter) {
        this.center = alertCenter;
        this.rules = [];
        this.filteredRules = [];
        this.currentPage = 1;
        this.pageSize = 10;
        this.selectedRules = new Set();
        this.editingRule = null;
        this.initialized = false;
    }

    /**
     * 初始化模块
     */
    async init() {
        if (this.initialized) {
            await this.loadRules();
            return;
        }

        console.log('[RulesModule] 初始化规则管理模块...');
        
        this.bindEvents();
        await this.loadRules();
        
        this.initialized = true;
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 搜索输入
        const searchInput = document.getElementById('rule-search-input');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.applyFilters();
                }, 300);
            });
        }

        // 筛选器
        const metricFilter = document.getElementById('rule-filter-metric');
        const levelFilter = document.getElementById('rule-filter-level');

        if (metricFilter) {
            metricFilter.addEventListener('change', () => this.applyFilters());
        }
        if (levelFilter) {
            levelFilter.addEventListener('change', () => this.applyFilters());
        }

        // 全选复选框
        const selectAll = document.getElementById('select-all-rules');
        if (selectAll) {
            selectAll.addEventListener('change', (e) => {
                this.toggleSelectAll(e.target.checked);
            });
        }
    }

    /**
     * 加载规则数据
     */
    async loadRules() {
        const tbody = document.getElementById('rules-tbody');
        const emptyState = document.getElementById('rules-empty-state');
        
        if (!tbody) return;

        try {
            const response = await fetch(`${this.center.apiBaseUrl}/alert-rules`);
            if (!response.ok) throw new Error('获取规则失败');

            const data = await response.json();
            this.rules = data.items || [];
            
            this.applyFilters();
            this.updateStats();

        } catch (error) {
            console.error('[RulesModule] 加载规则失败:', error);
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-error">
                        加载失败，请稍后重试
                    </td>
                </tr>
            `;
        }
    }

    /**
     * 应用筛选
     */
    applyFilters() {
        const searchValue = document.getElementById('rule-search-input')?.value?.toLowerCase() || '';
        const metricValue = document.getElementById('rule-filter-metric')?.value || '';
        const levelValue = document.getElementById('rule-filter-level')?.value || '';

        this.filteredRules = this.rules.filter(rule => {
            // 搜索筛选
            if (searchValue && !rule.name.toLowerCase().includes(searchValue)) {
                return false;
            }
            
            // 指标筛选
            if (metricValue && rule.metric !== metricValue) {
                return false;
            }
            
            // 级别筛选
            if (levelValue && rule.level !== levelValue) {
                return false;
            }
            
            return true;
        });

        this.currentPage = 1;
        this.renderRules();
    }

    /**
     * 渲染规则列表
     */
    renderRules() {
        const tbody = document.getElementById('rules-tbody');
        const emptyState = document.getElementById('rules-empty-state');
        
        if (!tbody) return;

        // 分页
        const start = (this.currentPage - 1) * this.pageSize;
        const end = start + this.pageSize;
        const pageRules = this.filteredRules.slice(start, end);

        if (pageRules.length === 0) {
            tbody.innerHTML = '';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';

        tbody.innerHTML = pageRules.map(rule => this.renderRuleRow(rule)).join('');
        
        // 恢复选中状态
        this.updateSelectionState();
    }

    /**
     * 渲染单行规则
     */
    renderRuleRow(rule) {
        const isSelected = this.selectedRules.has(rule.id);
        
        return `
            <tr data-rule-id="${rule.id}">
                <td class="checkbox-col">
                    <input type="checkbox" class="rule-checkbox" 
                           ${isSelected ? 'checked' : ''} 
                           onchange="AlertCenter.rules.toggleSelect('${rule.id}')">
                </td>
                <td>${rule.name}</td>
                <td>${this.getMetricLabel(rule.metric)}</td>
                <td>${this.formatCondition(rule)}</td>
                <td>
                    <span class="level-${rule.level}">${this.getLevelLabel(rule.level)}</span>
                </td>
                <td>
                    <span class="status-badge ${rule.enabled ? 'status-enabled' : 'status-disabled'}">
                        ${rule.enabled ? '启用' : '禁用'}
                    </span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-secondary" onclick="AlertCenter.rules.editRule('${rule.id}')">
                            编辑
                        </button>
                        <button class="btn btn-sm btn-icon" onclick="AlertCenter.rules.deleteRule('${rule.id}')">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * 获取指标标签
     */
    getMetricLabel(metric) {
        const labels = {
            cpu: 'CPU',
            memory: '内存',
            disk: '磁盘',
            network: '网络',
            load: '负载',
            process: '进程'
        };
        return labels[metric] || metric;
    }

    /**
     * 获取级别标签
     */
    getLevelLabel(level) {
        const labels = {
            critical: '严重',
            warning: '警告',
            info: '信息'
        };
        return labels[level] || level;
    }

    /**
     * 格式化条件
     */
    formatCondition(rule) {
        const comparisons = {
            gt: '>',
            gte: '≥',
            lt: '<',
            lte: '≤',
            eq: '='
        };
        const comp = comparisons[rule.comparison] || rule.comparison;
        return `${this.getMetricLabel(rule.metric)} ${comp} ${rule.threshold}%`;
    }

    /**
     * 更新统计
     */
    updateStats() {
        const total = this.rules.length;
        const enabled = this.rules.filter(r => r.enabled).length;
        const disabled = total - enabled;
        const critical = this.rules.filter(r => r.level === 'critical').length;

        this.updateStatElement('stat-rule-total', total);
        this.updateStatElement('stat-rule-enabled', enabled);
        this.updateStatElement('stat-rule-disabled', disabled);
        this.updateStatElement('stat-rule-critical', critical);
    }

    /**
     * 更新统计元素
     */
    updateStatElement(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value;
        }
    }

    /**
     * 切换单个选择
     */
    toggleSelect(ruleId) {
        if (this.selectedRules.has(ruleId)) {
            this.selectedRules.delete(ruleId);
        } else {
            this.selectedRules.add(ruleId);
        }
        this.updateSelectAllState();
    }

    /**
     * 切换全选
     */
    toggleSelectAll(checked) {
        const visibleRules = this.getVisibleRuleIds();
        
        if (checked) {
            visibleRules.forEach(id => this.selectedRules.add(id));
        } else {
            visibleRules.forEach(id => this.selectedRules.delete(id));
        }
        
        this.updateSelectionState();
    }

    /**
     * 获取可见规则ID
     */
    getVisibleRuleIds() {
        const start = (this.currentPage - 1) * this.pageSize;
        const end = start + this.pageSize;
        return this.filteredRules.slice(start, end).map(r => r.id);
    }

    /**
     * 更新选择状态
     */
    updateSelectionState() {
        const checkboxes = document.querySelectorAll('.rule-checkbox');
        checkboxes.forEach(cb => {
            const ruleId = cb.closest('tr')?.dataset.ruleId;
            if (ruleId) {
                cb.checked = this.selectedRules.has(ruleId);
            }
        });
        
        this.updateSelectAllState();
    }

    /**
     * 更新全选状态
     */
    updateSelectAllState() {
        const selectAll = document.getElementById('select-all-rules');
        if (!selectAll) return;
        
        const visibleIds = this.getVisibleRuleIds();
        const allSelected = visibleIds.length > 0 && visibleIds.every(id => this.selectedRules.has(id));
        
        selectAll.checked = allSelected;
        selectAll.indeterminate = !allSelected && visibleIds.some(id => this.selectedRules.has(id));
    }

    /**
     * 打开创建模态框
     */
    openCreateModal() {
        this.editingRule = null;
        this.openModal('新建告警规则');
    }

    /**
     * 编辑规则
     */
    editRule(ruleId) {
        const rule = this.rules.find(r => r.id === ruleId);
        if (!rule) return;
        
        this.editingRule = rule;
        this.openModal('编辑告警规则', rule);
    }

    /**
     * 打开模态框
     */
    openModal(title, rule = null) {
        const modal = document.getElementById('rule-modal');
        const modalTitle = document.getElementById('modal-title');
        
        if (modalTitle) modalTitle.textContent = title;
        
        // 填充表单
        if (rule) {
            document.getElementById('rule-id').value = rule.id;
            document.getElementById('rule-name').value = rule.name;
            document.getElementById('rule-description').value = rule.description || '';
            document.getElementById('rule-metric').value = rule.metric;
            document.getElementById('rule-comparison').value = rule.comparison;
            document.getElementById('rule-threshold').value = rule.threshold;
        } else {
            document.getElementById('rule-form')?.reset();
            document.getElementById('rule-id').value = '';
        }
        
        if (modal) modal.style.display = 'flex';
    }

    /**
     * 关闭模态框
     */
    closeModal() {
        const modal = document.getElementById('rule-modal');
        if (modal) modal.style.display = 'none';
        this.editingRule = null;
    }

    /**
     * 保存规则
     */
    async saveRule() {
        const form = document.getElementById('rule-form');
        if (!form) return;
        
        const formData = {
            name: document.getElementById('rule-name')?.value,
            description: document.getElementById('rule-description')?.value,
            metric: document.getElementById('rule-metric')?.value,
            comparison: document.getElementById('rule-comparison')?.value,
            threshold: parseFloat(document.getElementById('rule-threshold')?.value)
        };
        
        // 验证
        if (!formData.name || !formData.metric || isNaN(formData.threshold)) {
            this.center.showToast('请填写完整信息', 'warning');
            return;
        }
        
        try {
            const ruleId = document.getElementById('rule-id')?.value;
            const isEdit = !!ruleId;
            
            const url = isEdit 
                ? `${this.center.apiBaseUrl}/alert-rules/${ruleId}`
                : `${this.center.apiBaseUrl}/alert-rules`;
            
            const response = await fetch(url, {
                method: isEdit ? 'PUT' : 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) throw new Error('保存失败');
            
            this.center.showToast(isEdit ? '规则已更新' : '规则已创建', 'success');
            this.closeModal();
            await this.loadRules();
            
        } catch (error) {
            console.error('[RulesModule] 保存规则失败:', error);
            this.center.showToast('保存失败，请重试', 'error');
        }
    }

    /**
     * 删除规则
     */
    async deleteRule(ruleId) {
        const rule = this.rules.find(r => r.id === ruleId);
        
        this.center.uiComponents.showConfirm({
            title: '删除规则',
            message: `确定要删除规则 "${rule?.name || ruleId}" 吗？`,
            type: 'danger',
            confirmText: '删除',
            onConfirm: async () => {
                try {
                    const response = await fetch(`${this.center.apiBaseUrl}/alert-rules/${ruleId}`, {
                        method: 'DELETE'
                    });
                    
                    if (!response.ok) throw new Error('删除失败');
                    
                    this.center.showToast('规则已删除', 'success');
                    await this.loadRules();
                    
                } catch (error) {
                    console.error('[RulesModule] 删除规则失败:', error);
                    this.center.showToast('删除失败', 'error');
                }
            }
        });
    }

    /**
     * 批量启用
     */
    async batchEnable() {
        if (this.selectedRules.size === 0) {
            this.center.showToast('请先选择规则', 'warning');
            return;
        }
        
        await this.batchUpdate(Array.from(this.selectedRules), { enabled: true });
    }

    /**
     * 批量禁用
     */
    async batchDisable() {
        if (this.selectedRules.size === 0) {
            this.center.showToast('请先选择规则', 'warning');
            return;
        }
        
        await this.batchUpdate(Array.from(this.selectedRules), { enabled: false });
    }

    /**
     * 批量删除
     */
    async batchDelete() {
        if (this.selectedRules.size === 0) {
            this.center.showToast('请先选择规则', 'warning');
            return;
        }
        
        this.center.uiComponents.showConfirm({
            title: '批量删除规则',
            message: `确定要删除选中的 ${this.selectedRules.size} 条规则吗？`,
            type: 'danger',
            confirmText: '删除',
            onConfirm: async () => {
                try {
                    const response = await fetch(`${this.center.apiBaseUrl}/alert-rules/batch-delete`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ids: Array.from(this.selectedRules) })
                    });
                    
                    if (!response.ok) throw new Error('批量删除失败');
                    
                    this.center.showToast('规则已批量删除', 'success');
                    this.selectedRules.clear();
                    await this.loadRules();
                    
                } catch (error) {
                    console.error('[RulesModule] 批量删除失败:', error);
                    this.center.showToast('批量删除失败', 'error');
                }
            }
        });
    }

    /**
     * 批量更新
     */
    async batchUpdate(ids, updates) {
        try {
            const response = await fetch(`${this.center.apiBaseUrl}/alert-rules/batch-update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids, updates })
            });
            
            if (!response.ok) throw new Error('批量更新失败');
            
            this.center.showToast('规则已更新', 'success');
            this.selectedRules.clear();
            await this.loadRules();
            
        } catch (error) {
            console.error('[RulesModule] 批量更新失败:', error);
            this.center.showToast('更新失败', 'error');
        }
    }
}
