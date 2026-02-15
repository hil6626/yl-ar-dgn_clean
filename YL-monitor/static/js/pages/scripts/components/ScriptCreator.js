/**
 * 脚本创建组件
 * 版本: v1.0.0
 */

export class ScriptCreator {
  constructor(page) {
    this.page = page;
    this.modal = null;
  }

  /**
   * 显示创建脚本弹窗
   */
  show() {
    // 移除已存在的弹窗
    this.close();

    // 创建模态框
    this.modal = document.createElement('div');
    this.modal.className = 'script-modal';
    this.modal.id = 'script-creator-modal';
    this.modal.innerHTML = `
      <div class="script-modal-overlay">
        <div class="script-modal-content">
          <div class="script-modal-header">
            <h3>📜 新建脚本</h3>
            <button class="btn btn-sm btn-ghost" data-action="close-creator">×</button>
          </div>
          
          <div class="script-modal-body">
            <form id="script-create-form" class="script-form">
              <!-- 基本信息 -->
              <div class="form-section">
                <h4 class="form-section-title">基本信息</h4>
                
                <div class="form-group">
                  <label for="script-name">脚本名称 <span class="required">*</span></label>
                  <input type="text" id="script-name" name="name" required
                         placeholder="输入脚本名称，如：数据清理任务"
                         class="form-input">
                  <span class="form-hint">建议使用简洁明了的名称</span>
                </div>
                
                <div class="form-group">
                  <label for="script-description">描述</label>
                  <textarea id="script-description" name="description" rows="3"
                            placeholder="输入脚本描述..."
                            class="form-textarea"></textarea>
                </div>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="script-type">脚本类型 <span class="required">*</span></label>
                    <select id="script-type" name="type" required class="form-select">
                      <option value="">请选择类型</option>
                      <option value="python">Python</option>
                      <option value="shell">Shell</option>
                      <option value="javascript">JavaScript</option>
                      <option value="sql">SQL</option>
                    </select>
                  </div>
                  
                  <div class="form-group">
                    <label for="script-schedule">执行计划</label>
                    <select id="script-schedule" name="schedule" class="form-select">
                      <option value="">手动执行</option>
                      <option value="*/5 * * * *">每5分钟</option>
                      <option value="0 * * * *">每小时</option>
                      <option value="0 0 * * *">每天</option>
                      <option value="0 0 * * 0">每周</option>
                      <option value="custom">自定义</option>
                    </select>
                  </div>
                </div>
                
                <div class="form-group" id="custom-schedule-group" style="display: none;">
                  <label for="script-cron">Cron表达式</label>
                  <input type="text" id="script-cron" name="cron"
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
                      <button type="button" class="btn btn-sm btn-ghost" data-action="load-template">
                        📄 加载模板
                      </button>
                    </div>
                  </div>
                  <textarea id="script-code" name="code" rows="15" required
                            placeholder="# 在此输入脚本代码..."
                            class="form-textarea code-editor"></textarea>
                </div>
              </div>
              
              <!-- 高级选项 -->
              <div class="form-section">
                <h4 class="form-section-title">高级选项</h4>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="script-timeout">超时时间 (秒)</label>
                    <input type="number" id="script-timeout" name="timeout" 
                           value="300" min="10" max="3600"
                           class="form-input">
                  </div>
                  
                  <div class="form-group">
                    <label for="script-retries">重试次数</label>
                    <input type="number" id="script-retries" name="retries" 
                           value="0" min="0" max="5"
                           class="form-input">
                  </div>
                </div>
                
                <div class="form-group checkbox-group">
                  <label class="checkbox-label">
                    <input type="checkbox" id="script-enabled" name="enabled" checked>
                    <span>创建后立即启用</span>
                  </label>
                </div>
              </div>
            </form>
          </div>
          
          <div class="script-modal-footer">
            <button type="button" class="btn btn-secondary" data-action="close-creator">
              取消
            </button>
            <button type="button" class="btn btn-primary" data-action="save-script">
              💾 创建脚本
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
    this.modal.querySelector('[data-action="close-creator"]').addEventListener('click', () => {
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

    // 加载模板
    this.modal.querySelector('[data-action="load-template"]').addEventListener('click', () => {
      this.loadTemplate();
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

    // 简单的格式化（实际项目中可以使用prettier等库）
    let formatted = code;
    
    if (type === 'python') {
      // 基本的Python格式化
      formatted = code
        .split('\n')
        .map(line => line.trimRight())
        .join('\n');
    } else if (type === 'javascript') {
      // 基本的JS格式化
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
   * 加载模板
   */
  loadTemplate() {
    const type = this.modal.querySelector('#script-type')?.value;
    const codeEditor = this.modal.querySelector('#script-code');
    if (!codeEditor || !type) {
      this.page.ui.showToast({
        type: 'warning',
        message: '请先选择脚本类型'
      });
      return;
    }

    const templates = {
      python: `#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        logger.info("脚本开始执行")
        
        # TODO: 在这里添加你的代码
        
        logger.info("脚本执行完成")
        return 0
        
    except Exception as e:
        logger.error(f"脚本执行失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())`,

      shell: `#!/bin/bash

# 脚本名称: 
# 描述: 
# 作者: 
# 日期: $(date +%Y-%m-%d)

set -e  # 遇到错误立即退出

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "脚本开始执行"

# TODO: 在这里添加你的代码

log "脚本执行完成"`,

      javascript: `#!/usr/bin/env node

/**
 * 脚本描述
 */

const fs = require('fs');
const path = require('path');

// 主函数
async function main() {
    console.log('脚本开始执行');
    
    try {
        // TODO: 在这里添加你的代码
        
        console.log('脚本执行完成');
        process.exit(0);
        
    } catch (error) {
        console.error('脚本执行失败:', error);
        process.exit(1);
    }
}

// 执行主函数
main();`,

      sql: `-- 脚本描述
-- 创建日期: ${new Date().toISOString().split('T')[0]}

-- TODO: 在这里添加你的SQL代码

-- 示例:
-- SELECT * FROM table_name WHERE condition;

-- 注意: 请确保SQL语句以分号结尾`
    };

    const template = templates[type];
    if (template) {
      codeEditor.value = template;
      this.page.ui.showToast({
        type: 'success',
        message: '模板已加载'
      });
    }
  }

  /**
   * 保存脚本
   */
  async save() {
    const form = this.modal.querySelector('#script-create-form');
    if (!form) return;

    // 表单验证
    if (!this.validateForm(form)) {
      return;
    }

    // 收集数据
    const formData = new FormData(form);
    const scriptData = {
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
        saveBtn.innerHTML = '⏳ 创建中...';
      }

      // 调用API
      const response = await fetch('/api/v1/scripts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(scriptData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || '创建失败');
      }

      const result = await response.json();

      // 关闭弹窗
      this.close();

      // 显示成功提示
      this.page.ui.showToast({
        type: 'success',
        message: `脚本 "${scriptData.name}" 创建成功`
      });

      // 刷新脚本列表
      this.page.loadScripts();

      // 选中新创建的脚本
      if (result.id) {
        this.page.selectScript(result.id);
      }

    } catch (error) {
      console.error('[ScriptCreator] 创建脚本失败:', error);
      
      // 恢复按钮状态
      const saveBtn = this.modal.querySelector('[data-action="save-script"]');
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '💾 创建脚本';
      }

      // 显示错误提示
      this.page.ui.showToast({
        type: 'error',
        message: `创建失败: ${error.message}`
      });
    }
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

    // 验证代码不为空
    const codeField = form.querySelector('[name="code"]');
    if (codeField && !codeField.value.trim()) {
      errors.push('code');
      codeField.classList.add('error');
    }

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
  }
}
