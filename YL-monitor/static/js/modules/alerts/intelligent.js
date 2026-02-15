/**
 * 智能告警模块
 * 从 intelligent-alert.js 提取重构
 */

export class IntelligentModule {
    constructor(alertCenter) {
        this.center = alertCenter;
        this.config = {
            noiseReduction: true,
            trendPrediction: true,
            rootCauseAnalysis: false
        };
        this.initialized = false;
    }

    /**
     * 初始化模块
     */
    async init() {
        if (this.initialized) return;

        console.log('[IntelligentModule] 初始化智能告警模块...');
        
        await this.loadConfig();
        this.renderFeatures();
        
        this.initialized = true;
    }

    /**
     * 加载配置
     */
    async loadConfig() {
        try {
            const response = await fetch(`${this.center.apiBaseUrl}/alerts/intelligent/config`);
            if (response.ok) {
                const config = await response.json();
                this.config = { ...this.config, ...config };
            }
        } catch (error) {
            console.error('[IntelligentModule] 加载配置失败:', error);
        }
    }

    /**
     * 渲染特性卡片
     */
    renderFeatures() {
        // 更新UI状态
        this.updateFeatureStatus('noise-reduction', this.config.noiseReduction);
        this.updateFeatureStatus('trend-prediction', this.config.trendPrediction);
        this.updateFeatureStatus('root-cause-analysis', this.config.rootCauseAnalysis);
    }

    /**
     * 更新特性状态显示
     */
    updateFeatureStatus(featureId, enabled) {
        // 查找对应的特性卡片并更新状态显示
        const cards = document.querySelectorAll('.feature-card');
        cards.forEach(card => {
            const statusEl = card.querySelector('.feature-status');
            if (statusEl) {
                const isEnabled = statusEl.classList.contains('enabled');
                if (isEnabled !== enabled) {
                    statusEl.classList.toggle('enabled', enabled);
                    statusEl.classList.toggle('disabled', !enabled);
                    const dot = statusEl.querySelector('.status-dot');
                    const text = statusEl.querySelector('span:last-child');
                    if (text) {
                        text.textContent = enabled ? '已启用' : '未启用';
                    }
                }
            }
        });
    }

    /**
     * 打开配置模态框
     */
    openConfigModal() {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'intelligent-config-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>智能告警配置</h3>
                    <button class="btn-close" onclick="this.closest('.modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="config-section">
                        <h4>核心功能</h4>
                        
                        <div class="config-item">
                            <div class="config-info">
                                <div class="config-name">智能降噪</div>
                                <div class="config-desc">自动识别并抑制重复告警，减少告警疲劳</div>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" id="config-noise" ${this.config.noiseReduction ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        
                        <div class="config-item">
                            <div class="config-info">
                                <div class="config-name">趋势预测</div>
                                <div class="config-desc">基于历史数据预测潜在问题，提前预警</div>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" id="config-trend" ${this.config.trendPrediction ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        
                        <div class="config-item">
                            <div class="config-info">
                                <div class="config-name">根因分析</div>
                                <div class="config-desc">自动分析告警关联性，定位问题根源（实验性功能）</div>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" id="config-root" ${this.config.rootCauseAnalysis ? 'checked' : ''}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    
                    <div class="config-section">
                        <h4>降噪配置</h4>
                        <div class="form-group">
                            <label>相似度阈值 (%)</label>
                            <input type="range" id="similarity-threshold" min="50" max="95" value="80">
                            <span class="range-value">80%</span>
                        </div>
                        <div class="form-group">
                            <label>时间窗口 (分钟)</label>
                            <input type="number" id="time-window" value="30" min="5" max="120">
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">取消</button>
                    <button class="btn btn-primary" onclick="AlertCenter.intelligent.saveConfig()">保存配置</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 绑定切换事件
        const toggles = modal.querySelectorAll('.toggle-switch input');
        toggles.forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                const feature = e.target.id.replace('config-', '');
                const enabled = e.target.checked;
                this.updateFeatureState(feature, enabled);
            });
        });
    }

    /**
     * 更新特性状态
     */
    updateFeatureState(feature, enabled) {
        switch(feature) {
            case 'noise':
                this.config.noiseReduction = enabled;
                break;
            case 'trend':
                this.config.trendPrediction = enabled;
                break;
            case 'root':
                this.config.rootCauseAnalysis = enabled;
                break;
        }
    }

    /**
     * 保存配置
     */
    async saveConfig() {
        // 从表单收集配置
        const noiseEnabled = document.getElementById('config-noise')?.checked ?? this.config.noiseReduction;
        const trendEnabled = document.getElementById('config-trend')?.checked ?? this.config.trendPrediction;
        const rootEnabled = document.getElementById('config-root')?.checked ?? this.config.rootCauseAnalysis;
        
        const similarityThreshold = document.getElementById('similarity-threshold')?.value || 80;
        const timeWindow = document.getElementById('time-window')?.value || 30;

        const config = {
            noiseReduction: noiseEnabled,
            trendPrediction: trendEnabled,
            rootCauseAnalysis: rootEnabled,
            similarityThreshold: parseInt(similarityThreshold),
            timeWindow: parseInt(timeWindow)
        };

        try {
            const response = await fetch(`${this.center.apiBaseUrl}/alerts/intelligent/config`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (!response.ok) throw new Error('保存配置失败');

            this.config = config;
            this.renderFeatures();
            
            // 关闭模态框
            const modal = document.getElementById('intelligent-config-modal');
            if (modal) modal.remove();
            
            this.center.showToast('智能告警配置已保存', 'success');

        } catch (error) {
            console.error('[IntelligentModule] 保存配置失败:', error);
            this.center.showToast('保存配置失败', 'error');
        }
    }

    /**
     * 获取降噪统计
     */
    async getNoiseReductionStats() {
        try {
            const response = await fetch(`${this.center.apiBaseUrl}/alerts/intelligent/noise-stats`);
            if (!response.ok) return null;
            return await response.json();
        } catch (error) {
            console.error('[IntelligentModule] 获取降噪统计失败:', error);
            return null;
        }
    }

    /**
     * 获取预测数据
     */
    async getPredictionData() {
        try {
            const response = await fetch(`${this.center.apiBaseUrl}/alerts/intelligent/predictions`);
            if (!response.ok) return null;
            return await response.json();
        } catch (error) {
            console.error('[IntelligentModule] 获取预测数据失败:', error);
            return null;
        }
    }
}
