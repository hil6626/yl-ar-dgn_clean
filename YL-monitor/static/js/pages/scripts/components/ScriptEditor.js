/**
 * 脚本编辑组件
 * 版本: v1.0.0
 */

export class ScriptEditor {
  constructor(page) {
    this.page = page;
    this.modal = null;
    this.currentScript = null;
  }

  /**
   * 显示编辑脚本弹窗
   * @param {Object} script - 脚本数据
   */
  show(script) {
    if (!script) {
      this.page.ui.showToast({
        type: 'warning',
        message: '请先选择一个脚本'
      });
      return;
    }

    this.currentScript = script;

    // 移除已存在的弹窗
    this.close();

    // 创建模态框
    this.modal = document.createElement('div');
    this.modal.className = 'script-modal';
    this.modal.id = 'script-editor-modal';
    this.modal.innerHTML = `
      <div class="script-modal-overlay">
        <div class="script-modal-content">
          <div class="script-modal-header">
            <h3>✏️ 编辑脚本</h3>
            <button class="btn btn-sm btn-ghost" data-action="close-editor">×</button>
          </div>
          
          <div class="script-modal-body">
            <form id="script-edit-form" class="script-form">
              <input type="hidden" id="script-id" name="id" value="${script.id}">
              
              <!-- 基本信息 -->
              <div class="form-section">
                <h4 class="form-section-title">基本信息</h4>
                
                <div class="form-group">
                  <label for="script-name">脚本名称 <span class="required">*</span></label>
                  <input type="text" id="script-name" name="name" required
                         value="${this.escapeHtml(script.name)}"
                         placeholder="输入脚本名称"
                         class="form-input">
                </div>
                
                <div class="form-group">
                  <label for="script-description">描述</label>
                  <textarea id="script-description" name="description" rows="3"
                            placeholder="输入脚本描述..."
                            class="form-textarea">${this.escapeHtml(script.description || '')}</textarea>
                </div>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="script-type">脚本类型 <span class="required">*</span></label>
                    <select id="script-type" name="type" required class="form-select">
                      <option value="python" ${script.type === 'python' ? 'selected' : ''}>Python</option>
                      <option value="shell" ${script.type === 'shell' ? 'selected' : ''}>Shell</option>
                      <option value="javascript" ${script.type === 'javascript' ? 'selected' : ''}>JavaScript</option>
                      <option value="sql" ${script.type === 'sql' ? 'selected' : ''}>SQL</option>
                    </select>
                  </div>
                  
                  <div class="form-group">
                    <label for="script-schedule">执行计划</label>
                    <select id="script-schedule" name="schedule" class="form-select">
                      <option value="" ${!script.schedule ? 'selected' : ''}>手动执行</option>
                      <option value="*/5 * * * *" ${script.schedule === '*/5 * * * *' ? 'selected' : ''}>每5分钟</option>
                      <option value="0 * * * *" ${script.schedule === '0 * * * *' ? 'selected' : ''}>每小时</option>
                      <option value="0 0 * * *" ${script.schedule === '0 0 * * *' ? 'selected' : ''}>每天</option>
                      <option value="0 0 * * 0" ${script.schedule === '0 0 * * 0' ? 'selected' : ''}>每周</option>
                      <option value="custom" ${script.schedule && !['*/5 * * * *', '0 * * * *', '0 0 * * *', '0 0 * * 0'].includes(script.schedule) ? 'selected' : ''}>自定义</option>
                    </select>
                  </div>
                </div>
                
                <div class="form-group" id="custom-schedule-group" 
                     style="display: ${script.schedule && !['*/5 * * * *', '0 * * * *', '0 0 * * *', '0 0 * * 0'].includes(script.schedule) ? 'block' : 'none'};">
                  <label for="script-cron">Cron表达式</label>
                  <input type="text" id="script-cron" name="cron"
                         value="${this.escapeHtml(script.schedule || '')}"
                         placeholder="*/10 * * * *"
                         class="form-input">
                  <span class="form-hint">格式: 分 时 日 月 周</span>
                </div>
              </div>
              
              <!-- 脚本代码 -->
              <div class="form-section">
                <h4 class="form-section-title">脚本代码 <span class="required">*</span></h4>
                
                <div class="form-group">
                  <div class="code-editor-toolbar">
                    <span class="toolbar-label">代码编辑器</span>
                    <div class="toolbar-actions">
                      <button type="button" class="btn btn-sm btn-ghost" data-action="format-code">
                        🎨 格式化
                      </button>
                      <button type="button" class="btn btn-sm btn-ghost" data-action="validate-code">
                        ✅ 验证
                      </button>
                    </div>
                  </div>
                  <textarea id="script-code" name="code" rows="15" required
                            placeholder="# 在此输入脚本代码..."
                            class="form-textarea code-editor">${this.escapeHtml(script.code || '')}</textarea>
                </div>
              </div>
              
              <!-- 高级选项 -->
              <div class="form-section">
                <h4 class="form-section-title">高级选项</h4>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="script-timeout">超时时间 (秒)</label>
                    <input type="number" id="script-timeout" name="timeout" 
                           value="${script.timeout || 300}" min="10" max="3600"
                           class="form-input">
                  </div>
                  
                  <div class="form-group">
                    <label for="script-retries">重试次数</label>
                    <input type="number" id="script-retries" name="retries" 
                           value="${script.retries || 0}" min="0" max="5"
                           class="form-input">
                  </div>
                </div>
                
                <div class="form-group checkbox-group">
                  <label class="checkbox-label">
                    <input type="checkbox" id="script-enabled" name="enabled" 
                           ${script.enabled ? 'checked' : ''}>
                    <span>启用脚本</span>
                  </label>
                </div>
              </div>
              
              <!-- 版本信息 -->
              <div class="form-section">
                <h4 class="form-section-title">版本信息</h4>
                <div class="version-info">
                  <p><strong>版本:</strong> ${script.version || 1}</p>
                  <p><strong>创建时间:</strong> ${script.created_at || '未知'}</p>
                  <p><strong>更新时间:</strong> ${script.updated_at || '未知'}</p>
                  <p><strong>最后执行:</strong> ${script.last_run || '从未执行'}</p>
                </div>
              </div>
            </form>
          </div>
          
          <div class="script-modal-footer">
            <button type="button" class="btn btn-secondary" data-action="close-editor">
              取消
            </button>
            <button type="button" class="btn btn-danger" data-action="delete-script">
              🗑️ 删除
            </button>
            <button type="button" class="btn btn-primary" data-action="save-script">
              💾 保存修改
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(this.modal);

    // 显示动画
    requestAnimationFrame(() => {
      this.modal.classList.add('active');
    });

    // 绑定事件
    this.bindEvents();
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    // 关闭按钮
    this.modal.querySelector('[data-action="close-editor"]').addEventListener('click', () => {
      this.close();
    });

    // 点击遮罩关闭
    this.modal.querySelector('.script-modal-overlay').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) {
        this.close();
      }
    });

    // 保存按钮
    this.modal.querySelector('[data-action="save-script"]').addEventListener('click', () => {
      this.save();
    });

    // 删除按钮
    this.modal.querySelector('[data-action="delete-script"]').addEventListener('click', () => {
      this.delete();
    });

    // 执行计划变化
    const scheduleSelect = this.modal.querySelector('#script-schedule');
    if (scheduleSelect) {
      scheduleSelect.addEventListener('change', (e) => {
        const customGroup = this.modal.querySelector('#custom-schedule-group');
        if (customGroup) {
          customGroup.style.display = e.target.value === 'custom' ? 'block' : 'none';
        }
      });
    }

    // 格式化代码
    this.modal.querySelector('[data-action="format-code"]').addEventListener('click', () => {
      this.formatCode();
    });

    // 验证代码
    this.modal.querySelector('[data-action="validate-code"]').addEventListener('click', () => {
      this.validateCode();
    });

    // ESC键关闭
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        this.close();
        document.removeEventListener('keydown', handleEsc);
      }
    };
    document.addEventListener('keydown', handleEsc);
  }

  /**
   * 格式化代码
   */
  formatCode() {
    const codeEditor = this.modal.querySelector('#script-code');
    if (!codeEditor) return;

    const code = codeEditor.value;
    const type = this.modal.querySelector('#script-type')?.value;

    // 简单的格式化
    let formatted = code;
    
    if (type === 'python') {
      formatted = code
        .split('\n')
        .map(line => line.trimRight())
        .join('\n');
    } else if (type === 'javascript') {
      try {
        formatted = JSON.stringify(JSON.parse(code), null, 2);
      } catch {
        // 如果不是JSON，保持原样
      }
    }

    codeEditor.value = formatted;
    
    this.page.ui.showToast({
      type: 'success',
      message: '代码已格式化'
    });
  }

  /**
   * 验证代码
   */
  validateCode() {
    const codeEditor = this.modal.querySelector('#script-code');
    const type = this.modal.querySelector('#script-type')?.value;
    
    if (!codeEditor || !type) return;

    const code = codeEditor.value;

    // 基本验证
    let isValid = true;
    let message = '代码验证通过';

    if (!code.trim()) {
      isValid = false;
      message = '代码不能为空';
    } else if (type === 'python') {
      // 检查Python基本语法
      if (!code.includes('def ') && !code.includes('import ')) {
        message = '警告: 未检测到函数定义或导入语句';
      }
    } else if (type === 'javascript') {
      // 检查JS语法
      try {
        new Function(code);
      } catch (e) {
        isValid = false;
        message = `语法错误: ${e.message}`;
      }
    }

    this.page.ui.showToast({
      type: isValid ? 'success' : 'error',
      message: message
    });
  }

  /**
   * 保存脚本
   */
  async save() {
    const form = this.modal.querySelector('#script-edit-form');
    if (!form) return;

    // 表单验证
    if (!this.validateForm(form)) {
      return;
    }

    // 收集数据
    const formData = new FormData(form);
    const scriptData = {
      id: formData.get('id'),
      name: formData.get('name'),
      description: formData.get('description'),
      type: formData.get('type'),
      code: formData.get('code'),
      schedule: formData.get('schedule'),
      cron: formData.get('cron'),
      timeout: parseInt(formData.get('timeout')) || 300,
      retries: parseInt(formData.get('retries')) || 0,
      enabled: formData.get('enabled') === 'on'
    };

    // 处理schedule
    if (scriptData.schedule === 'custom') {
      scriptData.schedule = scriptData.cron;
    }

    try {
      // 显示加载状态
      const saveBtn = this.modal.querySelector('[data-action="save-script"]');
      if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '⏳ 保存中...';
      }

      // 调用API
      const response = await fetch(`/api/v1/scripts/${scriptData.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(scriptData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || '保存失败');
      }

      // 关闭弹窗
      this.close();

      // 显示成功提示
      this.page.ui.showToast({
        type: 'success',
        message: `脚本 "${scriptData.name}" 已更新`
      });

      // 刷新脚本列表
      this.page.loadScripts();

    } catch (error) {
      console.error('[ScriptEditor] 保存脚本失败:', error);
      
      // 恢复按钮状态
      const saveBtn = this.modal.querySelector('[data-action="save-script"]');
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '💾 保存修改';
      }

      // 显示错误提示
      this.page.ui.showToast({
        type: 'error',
        message: `保存失败: ${error.message}`
      });
    }
  }

  /**
   * 删除脚本
   */
  delete() {
    if (!this.currentScript) return;

    this.page.ui.showConfirm({
      title: '删除脚本',
      message: `确定要删除脚本 "${this.currentScript.name}" 吗？此操作不可恢复。`,
      type: 'danger',
      confirmText: '删除',
      onConfirm: async () => {
        try {
          const response = await fetch(`/api/v1/scripts/${this.currentScript.id}`, {
            method: 'DELETE'
          });

          if (!response.ok) {
            throw new Error('删除失败');
          }

          this.close();

          this.page.ui.showToast({
            type: 'success',
            message: '脚本已删除'
          });

          this.page.loadScripts();

        } catch (error) {
          this.page.ui.showToast({
            type: 'error',
            message: `删除失败: ${error.message}`
          });
        }
      }
    });
  }

  /**
   * 验证表单
   * @param {HTMLFormElement} form - 表单元素
   * @returns {boolean}
   */
  validateForm(form) {
    const requiredFields = ['name', 'type', 'code'];
    const errors = [];

    requiredFields.forEach(fieldName => {
      const field = form.querySelector(`[name="${fieldName}"]`);
      if (!field || !field.value.trim()) {
        errors.push(fieldName);
        field?.classList.add('error');
      } else {
        field?.classList.remove('error');
      }
    });

    if (errors.length > 0) {
      this.page.ui.showToast({
        type: 'error',
        message: `请填写必填字段: ${errors.join(', ')}`
      });
      return false;
    }

    return true;
  }

  /**
   * HTML转义
   * @param {string} text - 文本
   * @returns {string}
   */
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * 关闭弹窗
   */
  close() {
    if (this.modal) {
      this.modal.classList.remove('active');
      setTimeout(() => {
        if (this.modal) {
          this.modal.remove();
          this.modal = null;
        }
      }, 300);
    }
    this.currentScript = null;
  }
}
