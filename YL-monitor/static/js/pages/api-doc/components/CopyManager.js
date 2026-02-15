/**
 * API Doc复制管理器（三级降级方案）
 * 版本: v1.0.0
 */

export class CopyManager {
  constructor(page) {
    this.page = page;
    this.fallbackLevel = 0; // 0: 原生API, 1: execCommand, 2: 手动复制弹窗
  }

  /**
   * 复制到剪贴板（三级降级方案）
   * @param {string} text - 要复制的文本
   * @param {string} description - 描述（用于弹窗显示）
   * @returns {Promise<boolean>}
   */
  async copy(text, description = '内容') {
    // 第一级：现代Clipboard API
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        this.showSuccess('已复制到剪贴板');
        return true;
      } catch (err) {
        console.log('[CopyManager] Clipboard API失败，降级到execCommand');
      }
    }

    // 第二级：execCommand降级方案
    try {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.cssText = `
        position: fixed;
        left: -9999px;
        top: 0;
        opacity: 0;
      `;
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();

      const success = document.execCommand('copy');
      document.body.removeChild(textarea);

      if (success) {
        this.showSuccess('已复制到剪贴板');
        return true;
      }
    } catch (err) {
      console.log('[CopyManager] execCommand失败，降级到手动弹窗');
    }

    // 第三级：手动复制弹窗
    this.showManualCopyDialog(text, description);
    return false;
  }

  /**
   * 显示成功提示
   * @param {string} message - 消息内容
   */
  showSuccess(message) {
    this.page.ui.showToast({
      type: 'success',
      message: message
    });
  }

  /**
   * 显示手动复制弹窗
   * @param {string} text - 要复制的文本
   * @param {string} description - 描述
   */
  showManualCopyDialog(text, description) {
    // 创建弹窗
    const modal = document.createElement('div');
    modal.className = 'manual-copy-modal';
    modal.innerHTML = `
      <div class="manual-copy-content">
        <div class="manual-copy-header">
          <h3>📋 手动复制</h3>
          <p>您的浏览器不支持自动复制，请手动复制以下内容：</p>
        </div>
        <div class="manual-copy-body">
          <div class="copy-description">${description}</div>
          <textarea class="copy-textarea" readonly>${this.escapeHtml(text)}</textarea>
          <div class="copy-hint">点击上方文本框，按 Ctrl+C (或 Cmd+C) 复制</div>
        </div>
        <div class="manual-copy-footer">
          <button class="btn btn-primary" data-action="close-manual-copy">关闭</button>
        </div>
      </div>
    `;

    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
      .manual-copy-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.2s ease;
      }
      .manual-copy-content {
        background: var(--bg-primary);
        border-radius: 12px;
        width: 90%;
        max-width: 600px;
        max-height: 80vh;
        overflow: hidden;
        animation: slideUp 0.3s ease;
      }
      .manual-copy-header {
        padding: 20px;
        border-bottom: 1px solid var(--border);
      }
      .manual-copy-header h3 {
        margin: 0 0 8px 0;
        color: var(--text-primary);
      }
      .manual-copy-header p {
        margin: 0;
        color: var(--text-secondary);
        font-size: 14px;
      }
      .manual-copy-body {
        padding: 20px;
      }
      .copy-description {
        font-weight: 500;
        margin-bottom: 12px;
        color: var(--text-primary);
      }
      .copy-textarea {
        width: 100%;
        min-height: 120px;
        padding: 12px;
        border: 2px solid var(--border);
        border-radius: 8px;
        background: var(--bg-secondary);
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        resize: vertical;
        outline: none;
      }
      .copy-textarea:focus {
        border-color: var(--primary);
      }
      .copy-hint {
        margin-top: 12px;
        padding: 8px 12px;
        background: var(--info-bg);
        border-radius: 6px;
        font-size: 13px;
        color: var(--info);
      }
      .manual-copy-footer {
        padding: 16px 20px;
        border-top: 1px solid var(--border);
        display: flex;
        justify-content: flex-end;
      }
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes slideUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
      }
    `;
    document.head.appendChild(style);

    document.body.appendChild(modal);

    // 自动选中文本
    const textarea = modal.querySelector('.copy-textarea');
    textarea.focus();
    textarea.select();

    // 绑定关闭事件
    modal.querySelector('[data-action="close-manual-copy"]').addEventListener('click', () => {
      modal.remove();
    });

    // 点击遮罩关闭
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });
  }

  /**
   * HTML转义
   * @param {string} text - 原始文本
   * @returns {string}
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}
