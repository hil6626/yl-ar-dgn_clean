/**
 * API Doc参数验证组件
 * 版本: v1.0.0
 */

export class ParamValidator {
  constructor() {
    this.errors = [];
  }

  /**
   * 验证端点参数
   * @param {Object} endpoint - 端点数据
   * @param {Object} values - 参数值
   * @returns {Object} - { valid: boolean, errors: Array }
   */
  validate(endpoint, values) {
    this.errors = [];
    
    if (!endpoint.params || endpoint.params.length === 0) {
      return { valid: true, errors: [] };
    }

    for (const param of endpoint.params) {
      const value = values[param.name];
      
      // 必填验证
      if (param.required && (value === undefined || value === '')) {
        this.addError(param.name, `参数 "${param.name}" 为必填项`);
        continue;
      }

      // 如果有值，进行类型验证
      if (value !== undefined && value !== '') {
        this.validateType(param, value);
      }
    }

    // 验证请求体（对于POST/PUT/PATCH）
    if (['POST', 'PUT', 'PATCH'].includes(endpoint.method)) {
      this.validateRequestBody(values._body);
    }

    return {
      valid: this.errors.length === 0,
      errors: this.errors
    };
  }

  /**
   * 验证参数类型
   * @param {Object} param - 参数定义
   * @param {any} value - 参数值
   */
  validateType(param, value) {
    const type = param.type || 'string';
    
    switch (type) {
      case 'integer':
      case 'number':
        if (!/^-?\d+(\.\d+)?$/.test(value)) {
          this.addError(param.name, `参数 "${param.name}" 必须是数字`);
        }
        break;
        
      case 'boolean':
        if (!['true', 'false', '0', '1', true, false].includes(value)) {
          this.addError(param.name, `参数 "${param.name}" 必须是布尔值`);
        }
        break;
        
      case 'array':
        try {
          const arr = typeof value === 'string' ? JSON.parse(value) : value;
          if (!Array.isArray(arr)) {
            this.addError(param.name, `参数 "${param.name}" 必须是数组`);
          }
        } catch (e) {
          this.addError(param.name, `参数 "${param.name}" 格式错误，必须是有效的JSON数组`);
        }
        break;
        
      case 'object':
        try {
          if (typeof value === 'string') {
            JSON.parse(value);
          }
        } catch (e) {
          this.addError(param.name, `参数 "${param.name}" 格式错误，必须是有效的JSON对象`);
        }
        break;
        
      case 'email':
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          this.addError(param.name, `参数 "${param.name}" 必须是有效的邮箱地址`);
        }
        break;
        
      case 'url':
        try {
          new URL(value);
        } catch (e) {
          this.addError(param.name, `参数 "${param.name}" 必须是有效的URL`);
        }
        break;
    }

    // 验证枚举值
    if (param.enum && !param.enum.includes(value)) {
      this.addError(param.name, `参数 "${param.name}" 必须是以下值之一: ${param.enum.join(', ')}`);
    }

    // 验证最小长度
    if (param.minLength !== undefined && value.length < param.minLength) {
      this.addError(param.name, `参数 "${param.name}" 最少需要 ${param.minLength} 个字符`);
    }

    // 验证最大长度
    if (param.maxLength !== undefined && value.length > param.maxLength) {
      this.addError(param.name, `参数 "${param.name}" 最多允许 ${param.maxLength} 个字符`);
    }

    // 验证最小值
    if (param.minimum !== undefined && Number(value) < param.minimum) {
      this.addError(param.name, `参数 "${param.name}" 最小值为 ${param.minimum}`);
    }

    // 验证最大值
    if (param.maximum !== undefined && Number(value) > param.maximum) {
      this.addError(param.name, `参数 "${param.name}" 最大值为 ${param.maximum}`);
    }

    // 验证正则表达式
    if (param.pattern) {
      const regex = new RegExp(param.pattern);
      if (!regex.test(value)) {
        this.addError(param.name, `参数 "${param.name}" 格式不符合要求`);
      }
    }
  }

  /**
   * 验证请求体
   * @param {string} body - 请求体JSON字符串
   */
  validateRequestBody(body) {
    if (!body || body.trim() === '') {
      return; // 空请求体在某些情况下是允许的
    }

    try {
      JSON.parse(body);
    } catch (e) {
      this.addError('_body', '请求体必须是有效的JSON格式');
    }
  }

  /**
   * 添加错误
   * @param {string} field - 字段名
   * @param {string} message - 错误消息
   */
  addError(field, message) {
    this.errors.push({ field, message });
  }

  /**
   * 获取错误消息HTML
   * @returns {string}
   */
  getErrorHtml() {
    if (this.errors.length === 0) return '';
    
    return `
      <div class="validation-errors">
        <div class="validation-header">
          <span>⚠️</span>
          <span>验证失败，请修正以下错误：</span>
        </div>
        <ul class="validation-list">
          ${this.errors.map(err => `
            <li class="validation-item" data-field="${err.field}">
              <span class="validation-dot">•</span>
              <span>${err.message}</span>
            </li>
          `).join('')}
        </ul>
      </div>
    `;
  }

  /**
   * 高亮错误字段
   * @param {HTMLElement} container - 容器元素
   */
  highlightErrors(container) {
    // 清除之前的高亮
    container.querySelectorAll('.field-error').forEach(el => {
      el.classList.remove('field-error');
    });

    // 高亮当前错误字段
    this.errors.forEach(err => {
      const fieldEl = container.querySelector(`[data-field="${err.field}"]`);
      if (fieldEl) {
        fieldEl.classList.add('field-error');
        
        // 添加抖动动画
        fieldEl.style.animation = 'shake 0.5s ease';
        setTimeout(() => {
          fieldEl.style.animation = '';
        }, 500);
      }
    });
  }

  /**
   * 清除验证状态
   * @param {HTMLElement} container - 容器元素
   */
  clearValidation(container) {
    container.querySelectorAll('.field-error').forEach(el => {
      el.classList.remove('field-error');
    });
    
    const errorContainer = container.querySelector('.validation-errors');
    if (errorContainer) {
      errorContainer.remove();
    }
  }
}
