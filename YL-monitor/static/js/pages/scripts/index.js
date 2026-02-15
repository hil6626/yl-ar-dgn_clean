/**
 * Scripts页面入口
 * 重构自: page-scripts.js (600+行 → 模块化拆分)
 * 版本: v9.0.0 (模块化版本)
 */

// 导入组件
import {
  ScriptList,
  ScriptCard,
  FilterBar,
  BatchToolbar,
  StatsPanel
} from './components/index.js';

// 导入管理器
import { ScriptRunner, LogViewer } from './managers/index.js';

/**
 * Scripts页面主类
 */
export default class ScriptsPage {
  /**
   * @param {Object} deps - 依赖项（可选）
   * @param {Object} deps.themeManager - 主题管理器（可选）
   * @param {Object} deps.uiComponents - UI组件库（可选）
   */
  constructor(deps = {}) {
    this.apiBaseUrl = '/api/v1';
    this.deps = deps;
    
    // 初始化管理器
    this.scriptRunner = new ScriptRunner(this);
    this.logViewer = new LogViewer(this);
    
    // 初始化组件
    this.scriptList = new ScriptList(this);
    this.filterBar = new FilterBar(this);
    this.batchToolbar = new BatchToolbar(this);
    this.statsPanel = new StatsPanel(this);
    
    // 数据状态
    this.scripts = [];
    this.filteredScripts = [];
    this.currentFilter = 'all';
    this.selectedScripts = new Set();
    this.sortBy = 'name';
    this.searchQuery = '';
    this.draggedScript = null;
    
    // 挂载点引用
    this.mounts = {
      header: document.getElementById('scripts-header'),
      filterBar: document.getElementById('scripts-filter-bar'),
      batchToolbar: document.getElementById('scripts-batch-toolbar'),
      grid: document.getElementById('scripts-grid'),
      stats: document.getElementById('scripts-stats')
    };
  }

  /**
   * 初始化页面
   */
  async init() {
    console.log('[ScriptsPage] 初始化脚本管理页面 v9.0.0 (模块化)...');
    
    // 1. 渲染页面头部
    this.renderHeader();
    
    // 2. 渲染筛选栏
    this.filterBar.render();
    
    // 3. 渲染批量工具栏
    this.batchToolbar.render();
    
    // 4. 加载脚本数据
    await this.loadScripts();
    
    // 5. 渲染性能统计
    this.statsPanel.render();
    
    // 6. 绑定全局事件
    this.bindEvents();
    
    console.log('[ScriptsPage] 脚本管理页面初始化完成 ✅');
  }

  /**
   * 渲染页面头部
   */
  renderHeader() {
    if (!this.mounts.header) return;
    
    this.mounts.header.innerHTML = `
      <div class="scripts-title-section">
        <div>
          <h2>📜 脚本管理</h2>
          <p class="scripts-subtitle">管理和监控自动化脚本 (${this.scripts.length}个脚本)</p>
        </div>
      </div>
      <div class="scripts-actions">
        <button class="btn btn-primary" id="btn-create-script">
          <span>+</span>
          <span>新建脚本</span>
        </button>
        <button class="btn btn-secondary" id="btn-import-script">
          <span>📥</span>
          <span>导入</span>
        </button>
        <div class="dropdown">
          <button class="btn btn-secondary" id="btn-batch-menu">
            <span>批量操作</span>
            <span>▼</span>
          </button>
          <div class="dropdown-menu hidden" id="batch-menu">
            <button class="dropdown-item" id="batch-enable">✅ 批量启用</button>
            <button class="dropdown-item" id="batch-disable">⏸️ 批量禁用</button>
            <button class="dropdown-item text-danger" id="batch-delete">🗑️ 批量删除</button>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * 加载脚本数据
   */
  async loadScripts() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/scripts`);
      if (!response.ok) throw new Error('获取脚本列表失败');
      
      const data = await response.json();
      // API 返回直接数组或 {scripts: [...]} 格式
      this.scripts = Array.isArray(data) ? data : (data.scripts || this.getSampleScripts());
      
    } catch (error) {
      console.warn('[ScriptsPage] 使用示例数据:', error);
      this.scripts = this.getSampleScripts();
    }
    
    this.applyFilters();
    this.scriptList.render();
    this.updateHeaderCount();
  }

  /**
   * 获取示例脚本数据
   * @returns {Array}
   */
  getSampleScripts() {
    return [
      {
        id: 'script-1',
        name: 'script_monitor.py',
        description: '系统监控脚本 - 监控CPU、内存、磁盘使用情况',
        type: 'Python',
        status: 'running',
        schedule: '*/5 * * * *',
        lastRun: new Date(Date.now() - 120000).toISOString(),
        successCount: 156,
        errorCount: 2,
        path: 'scripts/monitors/script_monitor.py'
      },
      {
        id: 'script-2',
        name: 'script_backup.py',
        description: '数据备份脚本 - 自动备份数据库和配置文件',
        type: 'Python',
        status: 'stopped',
        schedule: '0 0 * * *',
        lastRun: new Date(Date.now() - 86400000).toISOString(),
        successCount: 30,
        errorCount: 0,
        path: 'scripts/maintenance/script_backup.py'
      },
      {
        id: 'script-3',
        name: 'script_cleanup.py',
        description: '清理脚本 - 清理临时文件和日志',
        type: 'Python',
        status: 'error',
        schedule: '0 2 * * 0',
        lastRun: new Date(Date.now() - 172800000).toISOString(),
        successCount: 12,
        errorCount: 3,
        path: 'scripts/maintenance/script_cleanup.py'
      },
      {
        id: 'script-4',
        name: 'script_report.py',
        description: '报告生成脚本 - 生成系统运行报告',
        type: 'Python',
        status: 'pending',
        schedule: '0 9 * * 1',
        lastRun: null,
        successCount: 0,
        errorCount: 0,
        path: 'scripts/core/script_report.py'
      },
      {
        id: 'script-5',
        name: 'script_alert.py',
        description: '告警处理脚本 - 处理系统告警通知',
        type: 'Python',
        status: 'running',
        schedule: '*/2 * * * *',
        lastRun: new Date(Date.now() - 60000).toISOString(),
        successCount: 432,
        errorCount: 5,
        path: 'scripts/alerts/script_alert.py'
      }
    ];
  }

  /**
   * 应用筛选和排序
   */
  applyFilters() {
    let filtered = [...this.scripts];
    
    // 状态筛选
    if (this.currentFilter !== 'all') {
      filtered = filtered.filter(s => s.status === this.currentFilter);
    }
    
    // 搜索筛选
    if (this.searchQuery) {
      const query = this.searchQuery.toLowerCase();
      filtered = filtered.filter(s => 
        s.name.toLowerCase().includes(query) ||
        s.description.toLowerCase().includes(query)
      );
    }
    
    // 排序
    filtered.sort((a, b) => {
      switch(this.sortBy) {
        case 'name': return a.name.localeCompare(b.name);
        case 'status': return a.status.localeCompare(b.status);
        case 'lastRun': 
          if (!a.lastRun) return 1;
          if (!b.lastRun) return -1;
          return new Date(b.lastRun) - new Date(a.lastRun);
        case 'created': return b.id.localeCompare(a.id);
        default: return 0;
      }
    });
    
    this.filteredScripts = filtered;
  }

  /**
   * 更新头部计数
   */
  updateHeaderCount() {
    const subtitle = this.mounts.header?.querySelector('.scripts-subtitle');
    if (subtitle) {
      subtitle.textContent = `管理和监控自动化脚本 (${this.scripts.length}个脚本)`;
    }
  }

  /**
   * 绑定全局事件
   */
  bindEvents() {
    // 创建脚本
    document.getElementById('btn-create-script')?.addEventListener('click', () => this.createScript());
    
    // 导入脚本
    document.getElementById('btn-import-script')?.addEventListener('click', () => this.importScript());
    
    // 批量菜单
    document.getElementById('btn-batch-menu')?.addEventListener('click', () => this.toggleBatchMenu());
    
    // 批量操作
    document.getElementById('batch-enable')?.addEventListener('click', () => this.batchEnable());
    document.getElementById('batch-disable')?.addEventListener('click', () => this.batchDisable());
    document.getElementById('batch-delete')?.addEventListener('click', () => this.batchDelete());
    
    // 关闭日志模态框
    document.getElementById('close-logs-modal')?.addEventListener('click', () => {
      this.logViewer.close();
    });
    
    // 点击模态框背景关闭
    document.getElementById('logs-modal')?.addEventListener('click', (e) => {
      if (e.target.id === 'logs-modal') {
        this.logViewer.close();
      }
    });
  }

  /**
   * 设置筛选条件
   * @param {string} filter - 筛选条件
   */
  setFilter(filter) {
    this.currentFilter = filter;
    this.filterBar.render();
    this.applyFilters();
    this.scriptList.render();
  }

  /**
   * 更新批量工具栏
   */
  updateBatchToolbar() {
    this.batchToolbar.updateVisibility();
  }

  /**
   * 清除选择
   */
  clearSelection() {
    this.selectedScripts.clear();
    this.updateBatchToolbar();
    this.scriptList.render();
  }

  /**
   * 切换批量菜单
   */
  toggleBatchMenu() {
    const menu = document.getElementById('batch-menu');
    menu?.classList.toggle('hidden');
  }

  /**
   * 批量启用
   */
  async batchEnable() {
    if (this.selectedScripts.size === 0) return;
    this.showToast('info', `正在启用 ${this.selectedScripts.size} 个脚本...`);
    // 实现批量启用逻辑
    this.clearSelection();
  }

  /**
   * 批量禁用
   */
  async batchDisable() {
    if (this.selectedScripts.size === 0) return;
    this.showToast('info', `正在禁用 ${this.selectedScripts.size} 个脚本...`);
    // 实现批量禁用逻辑
    this.clearSelection();
  }

  /**
   * 批量删除
   */
  async batchDelete() {
    if (this.selectedScripts.size === 0) return;
    
    this.deps.uiComponents.showConfirm({
      title: '批量删除脚本',
      message: `确定要删除选中的 ${this.selectedScripts.size} 个脚本吗？`,
      type: 'danger',
      confirmText: '删除',
      onConfirm: async () => {
        this.showToast('info', `正在删除 ${this.selectedScripts.size} 个脚本...`);
        // 实现批量删除逻辑
        this.clearSelection();
        this.loadScripts();
      }
    });
  }

  /**
   * 处理卡片操作
   * @param {string} action - 操作类型
   * @param {string} scriptId - 脚本ID
   */
  handleCardAction(action, scriptId) {
    switch(action) {
      case 'view-logs': this.logViewer.view(scriptId); break;
      case 'edit-script': this.editScript(scriptId); break;
      case 'run-script': this.scriptRunner.run(scriptId); break;
      case 'stop-script': this.scriptRunner.stop(scriptId); break;
      case 'delete-script': this.deleteScript(scriptId); break;
    }
  }

  /**
   * 创建脚本
   */
  createScript() {
    this.showToast('info', '创建脚本功能开发中...');
  }

  /**
   * 导入脚本
   */
  importScript() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.py,.sh,.js';
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        this.showToast('success', `已选择文件: ${file.name}`);
      }
    };
    input.click();
  }

  /**
   * 编辑脚本
   * @param {string} scriptId - 脚本ID
   */
  editScript(scriptId) {
    const script = this.scripts.find(s => s.id === scriptId);
    this.showToast('info', `编辑脚本: ${script?.name || scriptId}`);
  }

  /**
   * 删除脚本
   * @param {string} scriptId - 脚本ID
   */
  async deleteScript(scriptId) {
    const script = this.scripts.find(s => s.id === scriptId);
    
    this.deps.uiComponents.showConfirm({
      title: '删除脚本',
      message: `确定要删除脚本 "${script?.name || scriptId}" 吗？`,
      type: 'danger',
      confirmText: '删除',
      onConfirm: async () => {
        try {
          const response = await fetch(`${this.apiBaseUrl}/scripts/${scriptId}`, {
            method: 'DELETE'
          });
          
          if (response.ok) {
            this.showToast('success', '脚本已删除');
            this.loadScripts();
          } else {
            throw new Error('删除失败');
          }
        } catch (error) {
          this.showToast('error', '删除脚本失败');
        }
      }
    });
  }

  /**
   * 保存脚本排序到后端
   * @returns {Promise<boolean>}
   */
  async saveScriptOrder() {
    try {
      // 构建排序数据
      const orderData = this.scripts.map((script, index) => ({
        id: script.id,
        order: index
      }));
      
      const response = await fetch(`${this.apiBaseUrl}/scripts/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scripts: orderData })
      });
      
      if (!response.ok) {
        throw new Error('保存排序失败');
      }
      
      console.log('[ScriptsPage] 脚本排序已保存到后端');
      return true;
    } catch (error) {
      console.error('[ScriptsPage] 保存排序失败:', error);
      // 显示错误但不阻止UI更新
      this.showToast('warning', '排序已更新，但保存到服务器失败');
      return false;
    }
  }

  /**
   * 显示提示
   * @param {string} type - 提示类型
   * @param {string} message - 提示消息
   */
  showToast(type, message) {
    if (this.deps?.uiComponents?.showToast) {
      this.deps.uiComponents.showToast({ type, message });
    } else {
      console.log(`[Toast ${type}] ${message}`);
    }
  }

  /**
   * 处理动作
   * @param {string} action - 动作名称
   * @param {Object} context - 上下文
   * @param {Event} event - 事件
   */
  handleAction(action, context, event) {
    switch(action) {
      case 'refresh-scripts':
        this.loadScripts();
        break;
      default:
        console.log('[ScriptsPage] 未处理的动作:', action);
    }
  }
}
