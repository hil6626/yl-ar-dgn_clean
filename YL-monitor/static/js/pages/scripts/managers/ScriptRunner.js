/**
 * 脚本运行管理器
 * 拆分自: page-scripts.js runScript(), stopScript() 等方法
 * 版本: v1.0.0
 */

export class ScriptRunner {
  /**
   * @param {ScriptsPage} page - Scripts页面实例
   */
  constructor(page) {
    this.page = page;
    this.runningScripts = new Set();
  }

  /**
   * 运行脚本
   * @param {string} scriptId - 脚本ID
   * @returns {Promise<boolean>}
   */
  async run(scriptId) {
    try {
      const response = await fetch(`${this.page.apiBaseUrl}/scripts/${scriptId}/run`, {
        method: 'POST'
      });

      if (response.ok) {
        this.runningScripts.add(scriptId);
        this.page.showToast('success', '脚本已开始运行');
        return true;
      } else {
        throw new Error('启动失败');
      }
    } catch (error) {
      console.error(`[ScriptRunner] 启动脚本 ${scriptId} 失败:`, error);
      this.page.showToast('error', '启动脚本失败');
      return false;
    }
  }

  /**
   * 停止脚本
   * @param {string} scriptId - 脚本ID
   * @returns {Promise<boolean>}
   */
  async stop(scriptId) {
    try {
      const response = await fetch(`${this.page.apiBaseUrl}/scripts/${scriptId}/stop`, {
        method: 'POST'
      });

      if (response.ok) {
        this.runningScripts.delete(scriptId);
        this.page.showToast('success', '脚本已停止');
        return true;
      } else {
        throw new Error('停止失败');
      }
    } catch (error) {
      console.error(`[ScriptRunner] 停止脚本 ${scriptId} 失败:`, error);
      this.page.showToast('error', '停止脚本失败');
      return false;
    }
  }

  /**
   * 检查脚本是否正在运行
   * @param {string} scriptId - 脚本ID
   * @returns {boolean}
   */
  isRunning(scriptId) {
    return this.runningScripts.has(scriptId);
  }

  /**
   * 获取运行中的脚本数量
   * @returns {number}
   */
  getRunningCount() {
    return this.runningScripts.size;
  }
}
