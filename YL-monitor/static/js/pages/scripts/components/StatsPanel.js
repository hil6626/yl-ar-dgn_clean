/**
 * 统计面板组件
 * 拆分自: page-scripts.js renderStats() 和 calculateStats()
 * 版本: v1.0.0
 */

export class StatsPanel {
  /**
   * @param {ScriptsPage} page - Scripts页面实例
   */
  constructor(page) {
    this.page = page;
    this.mount = document.getElementById('scripts-stats');
    this.period = '24h';
  }

  /**
   * 渲染统计面板
   */
  render() {
    if (!this.mount) {
      console.warn('[StatsPanel] 挂载点不存在: #scripts-stats');
      return;
    }

    const stats = this.calculateStats();

    this.mount.innerHTML = `
      <div class="stats-header">
        <h3>📊 性能统计</h3>
        <select class="sort-select" id="stats-period">
          <option value="24h" ${this.period === '24h' ? 'selected' : ''}>最近24小时</option>
          <option value="7d" ${this.period === '7d' ? 'selected' : ''}>最近7天</option>
          <option value="30d" ${this.period === '30d' ? 'selected' : ''}>最近30天</option>
        </select>
      </div>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-card-value">${stats.totalRuns}</div>
          <div class="stat-card-label">总执行次数</div>
          <div class="stat-card-trend ${stats.runsTrend >= 0 ? 'up' : 'down'}">
            ${stats.runsTrend >= 0 ? '↑' : '↓'} ${Math.abs(stats.runsTrend)}%
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-card-value" style="color: var(--success)">${stats.successRate}%</div>
          <div class="stat-card-label">成功率</div>
          <div class="stat-card-trend ${stats.successTrend >= 0 ? 'up' : 'down'}">
            ${stats.successTrend >= 0 ? '↑' : '↓'} ${Math.abs(stats.successTrend)}%
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-card-value" style="color: var(--danger)">${stats.errorCount}</div>
          <div class="stat-card-label">错误次数</div>
          <div class="stat-card-trend ${stats.errorTrend <= 0 ? 'up' : 'down'}">
            ${stats.errorTrend <= 0 ? '↓' : '↑'} ${Math.abs(stats.errorTrend)}%
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-card-value">${stats.avgDuration}s</div>
          <div class="stat-card-label">平均执行时间</div>
          <div class="stat-card-trend ${stats.durationTrend <= 0 ? 'up' : 'down'}">
            ${stats.durationTrend <= 0 ? '↓' : '↑'} ${Math.abs(stats.durationTrend)}%
          </div>
        </div>
      </div>
    `;

    this.bindEvents();
  }

  /**
   * 计算统计数据
   * @returns {Object} 统计数据
   */
  calculateStats() {
    const totalRuns = this.page.scripts.reduce((sum, s) => sum + s.successCount + s.errorCount, 0);
    const totalSuccess = this.page.scripts.reduce((sum, s) => sum + s.successCount, 0);
    const totalError = this.page.scripts.reduce((sum, s) => sum + s.errorCount, 0);
    const successRate = totalRuns > 0 ? Math.round((totalSuccess / totalRuns) * 100) : 0;

    // 根据时间段调整趋势值
    const multiplier = this.period === '24h' ? 1 : (this.period === '7d' ? 7 : 30);

    return {
      totalRuns,
      successRate,
      errorCount: totalError,
      avgDuration: 2.3,
      runsTrend: 12 * multiplier,
      successTrend: 5 * multiplier,
      errorTrend: -8 * multiplier,
      durationTrend: -15 * multiplier
    };
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    document.getElementById('stats-period')?.addEventListener('change', (e) => {
      this.period = e.target.value;
      this.render();
    });
  }
}
