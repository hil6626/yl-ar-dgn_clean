/**
 * 批量工具栏组件
 * 拆分自: page-scripts.js renderBatchToolbar() 和批量操作方法
 * 版本: v1.0.0
 */

export class BatchToolbar {
  /**
   * @param {ScriptsPage} page - Scripts页面实例
   */
  constructor(page) {
    this.page = page;
    this.mount = document.getElementById('scripts-batch-toolbar');
  }

  /**
   * 渲染批量工具栏
   */
  render() {
    if (!this.mount) {
      console.warn('[BatchToolbar] 挂载点不存在: #scripts-batch-toolbar');
      return;
    }

    this.mount.innerHTML = `
      <div class="batch-info">
        已选择 <strong id="selected-count">0</strong> 个脚本
      </div>
      <div class="batch-actions">
        <button class="btn btn-success btn-sm" id="batch-run">▶ 运行</button>
        <button class="btn btn-warning btn-sm" id="batch-stop">⏹ 停止</button>
        <button class="btn btn-secondary btn-sm" id="batch-clear">清除选择</button>
      </div>
    `;

    this.bindEvents();
    this.updateVisibility();
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    document.getElementById('batch-run')?.addEventListener('click', () => this.batchRun());
    document.getElementById('batch-stop')?.addEventListener('click', () => this.batchStop());
    document.getElementById('batch-clear')?.addEventListener('click', () => this.page.clearSelection());
  }

  /**
   * 更新可见性
   */
  updateVisibility() {
    const count = this.page.selectedScripts.size;
    const countEl = document.getElementById('selected-count');
    
    if (count > 0) {
      this.mount?.classList.remove('hidden');
      if (countEl) countEl.textContent = count;
    } else {
      this.mount?.classList.add('hidden');
    }
  }

  /**
   * 批量运行
   */
  async batchRun() {
    if (this.page.selectedScripts.size === 0) return;
    
    this.page.showToast('info', `正在运行 ${this.page.selectedScripts.size} 个脚本...`);
    
    // 实现批量运行逻辑
    const promises = Array.from(this.page.selectedScripts).map(scriptId => 
      this.runScript(scriptId)
    );
    
    try {
      await Promise.all(promises);
      this.page.showToast('success', '批量运行完成');
      this.page.loadScripts();
    } catch (error) {
      this.page.showToast('error', '部分脚本运行失败');
    }
  }

  /**
   * 批量停止
   */
  async batchStop() {
    if (this.page.selectedScripts.size === 0) return;
    
    this.page.showToast('info', `正在停止 ${this.page.selectedScripts.size} 个脚本...`);
    
    // 实现批量停止逻辑
    const promises = Array.from(this.page.selectedScripts).map(scriptId => 
      this.stopScript(scriptId)
    );
    
    try {
      await Promise.all(promises);
      this.page.showToast('success', '批量停止完成');
      this.page.loadScripts();
    } catch (error) {
      this.page.showToast('error', '部分脚本停止失败');
    }
  }

  /**
   * 运行单个脚本
   * @param {string} scriptId - 脚本ID
   */
  async runScript(scriptId) {
    try {
      const response = await fetch(`${this.page.apiBaseUrl}/scripts/${scriptId}/run`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('启动失败');
      return true;
    } catch (error) {
      console.error(`[BatchToolbar] 启动脚本 ${scriptId} 失败:`, error);
      throw error;
    }
  }

  /**
   * 停止单个脚本
   * @param {string} scriptId - 脚本ID
   */
  async stopScript(scriptId) {
    try {
      const response = await fetch(`${this.page.apiBaseUrl}/scripts/${scriptId}/stop`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('停止失败');
      return true;
    } catch (error) {
      console.error(`[BatchToolbar] 停止脚本 ${scriptId} 失败:`, error);
      throw error;
    }
  }
}
