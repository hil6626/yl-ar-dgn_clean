/**
 * 自动保存管理器 - 实现DAG自动保存和草稿恢复
 * 拆分自: page-dag.js (原180行)
 * 版本: v1.0.0
 */

export class AutoSaveManager {
  /**
   * @param {DAGPage} page - DAG页面实例
   */
  constructor(page) {
    this.page = page;
    this.autoSaveInterval = null;
    this.AUTO_SAVE_DELAY = 30000; // 30秒自动保存
    this.DRAFT_EXPIRY = 24 * 60 * 60 * 1000; // 24小时过期
    this.STORAGE_KEY = 'yl_dag_draft';
    this.lastSaveTime = null;
    this.hasUnsavedChanges = false;
  }

  /**
   * 初始化自动保存
   */
  init() {
    // 检查是否有未恢复的草稿
    this.checkDraftRecovery();
    
    // 启动自动保存定时器
    this.startAutoSave();
    
    // 监听页面关闭事件
    window.addEventListener('beforeunload', (e) => this.handleBeforeUnload(e));
    
    console.log('[AutoSaveManager] 自动保存管理器已初始化');
  }

  /**
   * 启动自动保存
   */
  startAutoSave() {
    // 清除现有定时器
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
    }
    
    // 每30秒自动保存
    this.autoSaveInterval = setInterval(() => {
      this.autoSave();
    }, this.AUTO_SAVE_DELAY);
  }

  /**
   * 停止自动保存
   */
  stopAutoSave() {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
      this.autoSaveInterval = null;
    }
  }

  /**
   * 执行自动保存
   */
  async autoSave() {
    if (!this.hasUnsavedChanges) {
      return; // 没有变更，跳过保存
    }
    
    try {
      const draftData = {
        nodes: this.page.nodes,
        edges: this.page.edges,
        timestamp: Date.now(),
        version: '1.0.0'
      };
      
      // 保存到localStorage
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(draftData));
      this.lastSaveTime = Date.now();
      this.hasUnsavedChanges = false;
      
      console.log('[AutoSaveManager] 草稿已自动保存');
      
      // 显示保存提示（每5分钟显示一次）
      if (this.shouldShowSaveNotification()) {
        this.page.ui.showToast({ 
          type: 'info', 
          message: 'DAG草稿已自动保存' 
        });
      }
      
    } catch (error) {
      console.error('[AutoSaveManager] 自动保存失败:', error);
    }
  }

  /**
   * 标记有未保存的变更
   */
  markUnsaved() {
    this.hasUnsavedChanges = true;
  }

  /**
   * 检查是否需要显示保存通知
   * @returns {boolean}
   */
  shouldShowSaveNotification() {
    if (!this.lastSaveTime) return true;
    
    const fiveMinutes = 5 * 60 * 1000;
    return (Date.now() - this.lastSaveTime) >= fiveMinutes;
  }

  /**
   * 检查草稿恢复
   */
  checkDraftRecovery() {
    try {
      const draftJson = localStorage.getItem(this.STORAGE_KEY);
      if (!draftJson) return;
      
      const draft = JSON.parse(draftJson);
      
      // 检查草稿是否过期
      if (Date.now() - draft.timestamp > this.DRAFT_EXPIRY) {
        console.log('[AutoSaveManager] 草稿已过期，清除');
        localStorage.removeItem(this.STORAGE_KEY);
        return;
      }
      
      // 显示恢复提示
      this.showDraftRecoveryDialog(draft);
      
    } catch (error) {
      console.error('[AutoSaveManager] 检查草稿失败:', error);
    }
  }

  /**
   * 显示草稿恢复对话框
   * @param {Object} draft - 草稿数据
   */
  showDraftRecoveryDialog(draft) {
    const saveTime = new Date(draft.timestamp).toLocaleString('zh-CN');
    
    this.page.ui.showConfirm({
      title: '恢复DAG草稿',
      message: `检测到未保存的DAG草稿（${saveTime}），是否恢复？`,
      type: 'info',
      confirmText: '恢复草稿',
      cancelText: '丢弃',
      onConfirm: () => {
        this.restoreDraft(draft);
      },
      onCancel: () => {
        this.clearDraft();
      }
    });
  }

  /**
   * 恢复草稿
   * @param {Object} draft - 草稿数据
   */
  restoreDraft(draft) {
    try {
      this.page.nodes = draft.nodes || [];
      this.page.edges = draft.edges || [];
      
      this.page.renderNodes();
      this.page.renderEdges();
      
      this.page.ui.showToast({ 
        type: 'success', 
        message: 'DAG草稿已恢复' 
      });
      
      console.log('[AutoSaveManager] 草稿已恢复');
      
    } catch (error) {
      console.error('[AutoSaveManager] 恢复草稿失败:', error);
      this.page.ui.showToast({ 
        type: 'error', 
        message: '恢复草稿失败' 
      });
    }
  }

  /**
   * 清除草稿
   */
  clearDraft() {
    localStorage.removeItem(this.STORAGE_KEY);
    console.log('[AutoSaveManager] 草稿已清除');
  }

  /**
   * 处理页面关闭
   * @param {Event} e - beforeunload事件
   */
  handleBeforeUnload(e) {
    if (this.hasUnsavedChanges) {
      // 立即保存
      this.autoSave();
      
      // 显示确认提示
      e.preventDefault();
      e.returnValue = '有未保存的变更，确定要离开吗？';
      return e.returnValue;
    }
  }

  /**
   * 手动保存触发
   */
  onManualSave() {
    this.hasUnsavedChanges = false;
    this.clearDraft(); // 清除草稿，因为已正式保存
  }

  /**
   * 获取最后保存时间
   * @returns {number|null} 时间戳
   */
  getLastSaveTime() {
    return this.lastSaveTime;
  }

  /**
   * 是否有未保存的变更
   * @returns {boolean}
   */
  hasUnsavedData() {
    return this.hasUnsavedChanges;
  }
}
