/**
 * 命令管理器 - 实现撤销/重做功能
 * 拆分自: page-dag.js (原300行 → 现150行)
 * 版本: v1.0.0
 */

export class CommandManager {
  constructor(page) {
    this.page = page;
    this.undoStack = [];
    this.redoStack = [];
    this.maxHistory = 50;
  }

  /**
   * 执行命令
   * @param {Command} command - 要执行的命令
   */
  execute(command) {
    command.execute();
    this.undoStack.push(command);
    this.redoStack = []; // 清空重做栈
    
    // 限制历史记录大小
    if (this.undoStack.length > this.maxHistory) {
      this.undoStack.shift();
    }
    
    this.updateUI();
  }

  /**
   * 撤销
   */
  undo() {
    if (this.undoStack.length === 0) {
      this.page.ui.showToast({ type: 'warning', message: '没有可撤销的操作' });
      return;
    }
    
    const command = this.undoStack.pop();
    command.undo();
    this.redoStack.push(command);
    this.updateUI();
    
    this.page.ui.showToast({ type: 'info', message: '已撤销' });
  }

  /**
   * 重做
   */
  redo() {
    if (this.redoStack.length === 0) {
      this.page.ui.showToast({ type: 'warning', message: '没有可重做的操作' });
      return;
    }
    
    const command = this.redoStack.pop();
    command.execute();
    this.undoStack.push(command);
    this.updateUI();
    
    this.page.ui.showToast({ type: 'info', message: '已重做' });
  }

  /**
   * 更新UI状态
   */
  updateUI() {
    const undoBtn = document.getElementById('btn-undo');
    const redoBtn = document.getElementById('btn-redo');
    
    if (undoBtn) undoBtn.disabled = this.undoStack.length === 0;
    if (redoBtn) redoBtn.disabled = this.redoStack.length === 0;
  }

  /**
   * 清空历史
   */
  clear() {
    this.undoStack = [];
    this.redoStack = [];
    this.updateUI();
  }

  /**
   * 获取撤销栈大小
   * @returns {number}
   */
  getUndoStackSize() {
    return this.undoStack.length;
  }

  /**
   * 获取重做栈大小
   * @returns {number}
   */
  getRedoStackSize() {
    return this.redoStack.length;
  }

  /**
   * 是否可以撤销
   * @returns {boolean}
   */
  canUndo() {
    return this.undoStack.length > 0;
  }

  /**
   * 是否可以重做
   * @returns {boolean}
   */
  canRedo() {
    return this.redoStack.length > 0;
  }
}
