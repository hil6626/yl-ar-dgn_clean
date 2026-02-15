/**
 * 脚本列表组件
 * 拆分自: page-scripts.js renderGrid() 和 renderScriptCard()
 * 版本: v1.0.0
 */

import { ScriptCard } from './ScriptCard.js';

export class ScriptList {
  /**
   * @param {ScriptsPage} page - Scripts页面实例
   */
  constructor(page) {
    this.page = page;
    this.mount = document.getElementById('scripts-grid');
    this.scriptCard = new ScriptCard(page);
  }

  /**
   * 渲染脚本列表
   */
  render() {
    if (!this.mount) {
      console.warn('[ScriptList] 挂载点不存在: #scripts-grid');
      return;
    }

    if (this.page.filteredScripts.length === 0) {
      this.renderEmpty();
      return;
    }

    this.mount.innerHTML = `
      <div class="scripts-grid-container">
        ${this.page.filteredScripts.map((script, index) => 
          this.scriptCard.render(script, index, this.page.selectedScripts.has(script.id))
        ).join('')}
      </div>
    `;

    // 绑定卡片事件
    this.bindCardEvents();
  }

  /**
   * 渲染空状态
   */
  renderEmpty() {
    this.mount.innerHTML = `
      <div class="scripts-empty-state">
        <div class="empty-icon">📜</div>
        <div class="empty-title">暂无脚本</div>
        <div class="empty-description">没有找到符合条件的脚本</div>
        <button class="btn btn-primary" id="btn-create-empty">新建脚本</button>
      </div>
    `;

    // 绑定创建按钮
    document.getElementById('btn-create-empty')?.addEventListener('click', () => {
      this.page.createScript();
    });
  }

  /**
   * 绑定卡片事件
   */
  bindCardEvents() {
    // 复选框
    document.querySelectorAll('.script-checkbox').forEach(checkbox => {
      checkbox.addEventListener('change', (e) => {
        const scriptId = e.target.dataset.scriptId;
        if (e.target.checked) {
          this.page.selectedScripts.add(scriptId);
        } else {
          this.page.selectedScripts.delete(scriptId);
        }
        this.page.updateBatchToolbar();
        this.render(); // 重新渲染以更新选中状态
      });
    });

    // 卡片操作按钮
    document.querySelectorAll('.script-actions .btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const action = btn.dataset.action;
        const scriptId = btn.dataset.scriptId;
        this.page.handleCardAction(action, scriptId);
      });
    });

    // 拖拽事件
    document.querySelectorAll('.script-card').forEach(card => {
      card.addEventListener('dragstart', (e) => this.handleDragStart(e, card));
      card.addEventListener('dragover', (e) => this.handleDragOver(e, card));
      card.addEventListener('drop', (e) => this.handleDrop(e, card));
      card.addEventListener('dragend', () => this.handleDragEnd());
    });
  }

  /**
   * 拖拽开始
   * @param {DragEvent} e - 拖拽事件
   * @param {HTMLElement} card - 卡片元素
   */
  handleDragStart(e, card) {
    this.page.draggedScript = card.dataset.scriptId;
    card.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
  }

  /**
   * 拖拽经过
   * @param {DragEvent} e - 拖拽事件
   * @param {HTMLElement} card - 卡片元素
   */
  handleDragOver(e, card) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }

  /**
   * 拖拽放下
   * @param {DragEvent} e - 拖拽事件
   * @param {HTMLElement} card - 卡片元素
   */
  async handleDrop(e, card) {
    e.preventDefault();
    const targetId = card.dataset.scriptId;

    if (this.page.draggedScript && this.page.draggedScript !== targetId) {
      // 交换位置
      const fromIndex = this.page.scripts.findIndex(s => s.id === this.page.draggedScript);
      const toIndex = this.page.scripts.findIndex(s => s.id === targetId);

      if (fromIndex !== -1 && toIndex !== -1) {
        const [moved] = this.page.scripts.splice(fromIndex, 1);
        this.page.scripts.splice(toIndex, 0, moved);

        // 保存排序到后端
        await this.page.saveScriptOrder();

        this.page.applyFilters();
        this.render();
        this.page.showToast('success', '脚本顺序已更新并保存');
      }
    }
  }

  /**
   * 拖拽结束
   */
  handleDragEnd() {
    document.querySelectorAll('.script-card').forEach(card => {
      card.classList.remove('dragging');
    });
    this.page.draggedScript = null;
  }
}
