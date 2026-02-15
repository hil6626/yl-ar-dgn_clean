/**
 * 代码质量检查器
 * 检查代码规范和潜在问题
 * 版本: v1.0.0
 */

export class CodeQualityChecker {
  constructor() {
    this.issues = [];
    this.rules = this.defineRules();
  }

  /**
   * 定义检查规则
   * @returns {Array}
   */
  defineRules() {
    return [
      {
        id: 'console-log',
        name: 'Console语句检查',
        description: '检查是否包含未删除的console语句',
        severity: 'warning',
        check: (content) => {
          const matches = content.match(/console\.(log|debug|info)\(/g);
          return matches ? matches.length : 0;
        }
      },
      {
        id: 'debugger',
        name: 'Debugger语句检查',
        description: '检查是否包含debugger语句',
        severity: 'error',
        check: (content) => {
          return content.includes('debugger;') ? 1 : 0;
        }
      },
      {
        id: 'todo',
        name: 'TODO注释检查',
        description: '检查TODO注释数量',
        severity: 'info',
        check: (content) => {
          const matches = content.match(/TODO|FIXME|XXX/gi);
          return matches ? matches.length : 0;
        }
      },
      {
        id: 'long-function',
        name: '函数长度检查',
        description: '检查超长函数',
        severity: 'warning',
        check: (content) => {
          const functions = content.match(/function\s+\w+\s*\([^)]*\)\s*\{[^}]*\}/g) || [];
          let count = 0;
          functions.forEach(fn => {
            const lines = fn.split('\n').length;
            if (lines > 50) count++;
          });
          return count;
        }
      },
      {
        id: 'var-usage',
        name: 'Var关键字检查',
        description: '检查是否使用var（建议使用let/const）',
        severity: 'warning',
        check: (content) => {
          const matches = content.match(/\bvar\b\s+/g);
          return matches ? matches.length : 0;
        }
      },
      {
        id: 'eval-usage',
        name: 'Eval使用检查',
        description: '检查是否使用eval',
        severity: 'error',
        check: (content) => {
          return content.match(/\beval\s*\(/) ? 1 : 0;
        }
      },
      {
        id: 'inner-html',
        name: 'innerHTML使用检查',
        description: '检查innerHTML使用（可能存在XSS风险）',
        severity: 'warning',
        check: (content) => {
          const matches = content.match(/\.innerHTML\s*=/g);
          return matches ? matches.length : 0;
        }
      }
    ];
  }

  /**
   * 检查代码
   * @param {string} content - 代码内容
   * @param {string} filename - 文件名
   * @returns {Object}
   */
  check(content, filename) {
    const result = {
      filename,
      issues: [],
      summary: {
        total: 0,
        errors: 0,
        warnings: 0,
        info: 0
      }
    };

    this.rules.forEach(rule => {
      const count = rule.check(content);
      
      if (count > 0) {
        const issue = {
          rule: rule.id,
          name: rule.name,
          severity: rule.severity,
          count,
          description: rule.description
        };
        
        result.issues.push(issue);
        result.summary.total += count;
        
        switch (rule.severity) {
          case 'error':
            result.summary.errors += count;
            break;
          case 'warning':
            result.summary.warnings += count;
            break;
          case 'info':
            result.summary.info += count;
            break;
        }
      }
    });

    return result;
  }

  /**
   * 批量检查文件
   * @param {Array} files - 文件列表 [{name, content}]
   * @returns {Object}
   */
  checkFiles(files) {
    const results = files.map(file => this.check(file.content, file.name));
    
    const summary = results.reduce((acc, result) => {
      acc.total += result.summary.total;
      acc.errors += result.summary.errors;
      acc.warnings += result.summary.warnings;
      acc.info += result.summary.info;
      return acc;
    }, { total: 0, errors: 0, warnings: 0, info: 0 });

    return {
      files: results,
      summary,
      score: this.calculateScore(summary)
    };
  }

  /**
   * 计算质量分数
   * @param {Object} summary - 摘要
   * @returns {number}
   */
  calculateScore(summary) {
    const weights = {
      errors: 10,
      warnings: 2,
      info: 0.5
    };
    
    const penalty = 
      summary.errors * weights.errors +
      summary.warnings * weights.warnings +
      summary.info * weights.info;
    
    return Math.max(0, 100 - penalty);
  }

  /**
   * 生成报告
   * @param {Object} results - 检查结果
   * @returns {string}
   */
  generateReport(results) {
    let report = `# 代码质量检查报告\n\n`;
    report += `生成时间: ${new Date().toLocaleString()}\n\n`;
    
    report += `## 总体评分: ${results.score.toFixed(1)}/100\n\n`;
    
    report += `## 问题统计\n`;
    report += `- 总计: ${results.summary.total}\n`;
    report += `- 错误: ${results.summary.errors}\n`;
    report += `- 警告: ${results.summary.warnings}\n`;
    report += `- 信息: ${results.summary.info}\n\n`;
    
    report += `## 文件详情\n\n`;
    
    results.files.forEach(file => {
      if (file.issues.length === 0) return;
      
      report += `### ${file.filename}\n`;
      file.issues.forEach(issue => {
        const icon = issue.severity === 'error' ? '❌' : 
                     issue.severity === 'warning' ? '⚠️' : 'ℹ️';
        report += `- ${icon} [${issue.severity.toUpperCase()}] ${issue.name}: ${issue.count}处\n`;
        report += `  ${issue.description}\n`;
      });
      report += '\n';
    });
    
    report += `## 建议\n`;
    if (results.summary.errors > 0) {
      report += `- 优先修复错误级别的问题\n`;
    }
    if (results.summary.warnings > 0) {
      report += `- 处理警告以提升代码质量\n`;
    }
    report += `- 定期运行代码检查\n`;
    
    return report;
  }

  /**
   * 显示报告面板
   * @param {Object} results - 检查结果
   */
  showReportPanel(results) {
    const panel = document.createElement('div');
    panel.className = 'code-quality-panel';
    panel.innerHTML = `
      <div class="quality-panel-overlay">
        <div class="quality-panel-content">
          <div class="quality-panel-header">
            <h3>🔍 代码质量检查</h3>
            <button class="btn btn-ghost" data-action="close">✕</button>
          </div>
          <div class="quality-panel-body">
            <div class="quality-score">
              <div class="score-circle" style="--score: ${results.score}">
                <span class="score-value">${results.score.toFixed(0)}</span>
                <span class="score-label">分</span>
              </div>
            </div>
            
            <div class="quality-stats">
              <div class="stat-item error">
                <span class="stat-count">${results.summary.errors}</span>
                <span class="stat-label">错误</span>
              </div>
              <div class="stat-item warning">
                <span class="stat-count">${results.summary.warnings}</span>
                <span class="stat-label">警告</span>
              </div>
              <div class="stat-item info">
                <span class="stat-count">${results.summary.info}</span>
                <span class="stat-label">信息</span>
              </div>
            </div>
            
            <div class="quality-files">
              ${results.files.filter(f => f.issues.length > 0).map(file => `
                <div class="quality-file">
                  <div class="file-header">
                    <span class="file-name">${file.filename}</span>
                    <span class="file-count">${file.summary.total}</span>
                  </div>
                  <div class="file-issues">
                    ${file.issues.map(issue => `
                      <div class="issue-item ${issue.severity}">
                        <span class="issue-icon">${issue.severity === 'error' ? '❌' : issue.severity === 'warning' ? '⚠️' : 'ℹ️'}</span>
                        <span class="issue-name">${issue.name}</span>
                        <span class="issue-count">×${issue.count}</span>
                      </div>
                    `).join('')}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(panel);
    
    panel.querySelector('[data-action="close"]').addEventListener('click', () => {
      panel.remove();
    });
    
    requestAnimationFrame(() => {
      panel.classList.add('active');
    });
  }
}
