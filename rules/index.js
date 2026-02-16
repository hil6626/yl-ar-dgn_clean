/**
 * yl-ar-dgn 五层规则引擎（增强版 v1.2.0）
 *
 * 设计目标：
 * - 以 JSON 为源：L1~L5 分层文件
 * - 规则可渐进增强：优先可读，其次可执行
 * - 支持动态重载、规则验证、冲突检测
 *
 * 增强功能（v1.2.0）：
 * - 动态重载：支持运行时重新加载规则文件
 * - 规则验证：验证规则文件格式和依赖关系
 * - 冲突检测：检测规则之间的潜在冲突
 * - 部署状态查询：获取当前部署进度和状态
 */

const fs = require('fs');
const path = require('path');

function getByPath(obj, dottedPath) {
  if (!dottedPath) return undefined;
  const parts = String(dottedPath).split('.');
  let cur = obj;
  for (const part of parts) {
    if (cur == null) return undefined;
    cur = cur[part];
  }
  return cur;
}

class RulesEngine {
  constructor(options = {}) {
    this.rulesDir = options.rulesDir || __dirname;
    this.configPath = path.join(this.rulesDir, 'rules.config.js');
    this.loadConfig();
    this.layers = {};
    this.validationResults = [];
    this.conflicts = [];
    this.loadLayers();
  }

  /**
   * 加载配置文件
   */
  loadConfig() {
    try {
      // 清除require缓存以支持动态重载
      delete require.cache[this.configPath];
      this.config = require(this.configPath);
      this.configVersion = this.config.version || '1.0.0';
    } catch (error) {
      console.error(`[RulesEngine] 加载配置失败: ${error.message}`);
      this.config = { layerFiles: [], deploymentMaturity: { defaultLevel: 1 } };
      this.configVersion = 'unknown';
    }
  }

  /**
   * 动态重载所有规则
   */
  reload() {
    console.log('[RulesEngine] 正在重新加载规则...');
    this.loadConfig();
    this.layers = {};
    this.validationResults = [];
    this.conflicts = [];
    this.loadLayers();
    console.log('[RulesEngine] 规则重载完成');
    return this.getStatus();
  }

  /**
   * 加载所有层级规则文件
   */
  loadLayers() {
    const layerFiles = this.config.layerFiles || [
      'L1-meta-goal.json',
      'L2-understanding.json',
      'L3-constraints.json',
      'L4-decisions.json',
      'L5-execution.json'
    ];

    for (const file of layerFiles) {
      const filePath = path.join(this.rulesDir, file);
      const layerId = file.replace(/\.json$/i, '');
      
      if (!fs.existsSync(filePath)) {
        console.warn(`[RulesEngine] 警告: 规则文件不存在 ${file}`);
        this.validationResults.push({
          file,
          layerId,
          status: 'error',
          message: '文件不存在'
        });
        continue;
      }

      try {
        const content = fs.readFileSync(filePath, 'utf8');
        const layer = JSON.parse(content);
        this.layers[layerId] = layer;
        
        this.validationResults.push({
          file,
          layerId,
          status: 'success',
          version: layer.version || 'unknown',
          lastUpdated: layer.lastUpdated || 'unknown'
        });
      } catch (error) {
        console.error(`[RulesEngine] 解析失败 ${file}: ${error.message}`);
        this.validationResults.push({
          file,
          layerId,
          status: 'error',
          message: `JSON解析错误: ${error.message}`
        });
      }
    }

    // 加载完成后检测冲突
    this.detectConflicts();
  }

  /**
   * 检测规则冲突
   */
  detectConflicts() {
    this.conflicts = [];
    const allRules = [];

    // 收集所有规则
    for (const [layerId, layer] of Object.entries(this.layers)) {
      if (layer.rules && Array.isArray(layer.rules)) {
        for (const rule of layer.rules) {
          allRules.push({
            layerId,
            ruleId: rule.id,
            condition: rule.condition,
            action: rule.action,
            description: rule.description
          });
        }
      }
    }

    // 检测冲突：相同条件但不同动作
    for (let i = 0; i < allRules.length; i++) {
      for (let j = i + 1; j < allRules.length; j++) {
        const rule1 = allRules[i];
        const rule2 = allRules[j];

        if (this.conditionsEqual(rule1.condition, rule2.condition)) {
          if (!this.actionsEqual(rule1.action, rule2.action)) {
            this.conflicts.push({
              type: 'same_condition_different_action',
              severity: 'warning',
              rule1: { layerId: rule1.layerId, ruleId: rule1.ruleId },
              rule2: { layerId: rule2.layerId, ruleId: rule2.ruleId },
              description: `规则 ${rule1.ruleId} 和 ${rule2.ruleId} 条件相同但动作不同`
            });
          }
        }
      }
    }

    if (this.conflicts.length > 0) {
      console.warn(`[RulesEngine] 检测到 ${this.conflicts.length} 个潜在冲突`);
    }
  }

  /**
   * 比较两个条件是否相等
   */
  conditionsEqual(cond1, cond2) {
    if (!cond1 || !cond2) return false;
    return cond1.field === cond2.field &&
           cond1.operator === cond2.operator &&
           JSON.stringify(cond1.value) === JSON.stringify(cond2.value);
  }

  /**
   * 比较两个动作是否相等
   */
  actionsEqual(action1, action2) {
    if (!action1 || !action2) return false;
    return action1.target === action2.target &&
           JSON.stringify(action1.value) === JSON.stringify(action2.value);
  }

  /**
   * 验证所有规则文件
   */
  validate() {
    const results = {
      overall: 'success',
      layers: {},
      conflicts: this.conflicts,
      summary: {
        totalLayers: 0,
        validLayers: 0,
        errorLayers: 0,
        totalRules: 0
      }
    };

    for (const [layerId, layer] of Object.entries(this.layers)) {
      results.summary.totalLayers++;
      const layerResult = {
        status: 'success',
        version: layer.version,
        lastUpdated: layer.lastUpdated,
        errors: [],
        rules: 0
      };

      // 验证基本结构
      if (!layer.name) {
        layerResult.errors.push('缺少name字段');
      }
      if (!layer.description) {
        layerResult.errors.push('缺少description字段');
      }

      // 验证规则数组
      if (layer.rules && Array.isArray(layer.rules)) {
        layerResult.rules = layer.rules.length;
        results.summary.totalRules += layer.rules.length;

        for (const rule of layer.rules) {
          if (!rule.id) {
            layerResult.errors.push('规则缺少id字段');
          }
          if (rule.condition && !rule.condition.operator) {
            layerResult.errors.push(`规则 ${rule.id || 'unknown'} 条件缺少operator`);
          }
          if (rule.action && !rule.action.target) {
            layerResult.errors.push(`规则 ${rule.id || 'unknown'} 动作缺少target`);
          }
        }
      }

      if (layerResult.errors.length > 0) {
        layerResult.status = 'error';
        results.summary.errorLayers++;
        results.overall = 'error';
      } else {
        results.summary.validLayers++;
      }

      results.layers[layerId] = layerResult;
    }

    return results;
  }

  /**
   * 获取部署状态
   */
  getDeploymentStatus() {
    const status = {
      currentMaturityLevel: 1,
      targetMaturityLevel: 5,
      phases: {},
      overallProgress: 0
    };

    // 从L4获取成熟度信息
    const l4 = this.layers['L4-decisions'];
    if (l4 && l4.deploymentStatus) {
      status.currentMaturityLevel = l4.deploymentStatus.currentMaturityLevel || 1;
      status.targetMaturityLevel = l4.deploymentStatus.targetMaturityLevel || 5;
      
      if (l4.deploymentStatus.phase1) {
        status.phases.phase1 = l4.deploymentStatus.phase1;
      }
      if (l4.deploymentStatus.phase2) {
        status.phases.phase2 = l4.deploymentStatus.phase2;
      }
      if (l4.deploymentStatus.phase3) {
        status.phases.phase3 = l4.deploymentStatus.phase3;
      }
    }

    // 计算总体进度
    const l1 = this.layers['L1-meta-goal'];
    if (l1 && l1.goals) {
      const completedGoals = l1.goals.filter(g => g.status === 'completed').length;
      const totalGoals = l1.goals.length;
      status.overallProgress = totalGoals > 0 ? Math.round((completedGoals / totalGoals) * 100) : 0;
    }

    return status;
  }

  /**
   * 获取引擎状态
   */
  getStatus() {
    return {
      configVersion: this.configVersion,
      loadedLayers: Object.keys(this.layers),
      validationResults: this.validationResults,
      conflictCount: this.conflicts.length,
      deploymentStatus: this.getDeploymentStatus()
    };
  }

  /**
   * 执行规则引擎
   */
  execute(context = {}) {
    let result = { ...context };

    for (const file of this.config.layerFiles || []) {
      const layerId = file.replace(/\.json$/i, '');
      result = this.applyLayer(layerId, result);
    }

    return result;
  }

  /**
   * 应用单个层级的规则
   */
  applyLayer(layerId, context) {
    const layer = this.layers[layerId];
    if (!layer || !Array.isArray(layer.rules)) return context;

    const result = { ...context };
    for (const rule of layer.rules) {
      if (this.evaluateCondition(rule.condition, result)) {
        if (rule.action && rule.action.target) {
          result[rule.action.target] = rule.action.value;
        }
      }
    }
    return result;
  }

  /**
   * 评估条件
   */
  evaluateCondition(condition, context) {
    if (!condition) return true;

    const { field, operator, value } = condition;
    const fieldValue = getByPath(context, field);

    switch (operator) {
      case 'equals':
        if (value === null) return fieldValue == null;
        return fieldValue === value;
      case 'contains':
        if (Array.isArray(fieldValue)) return fieldValue.includes(value);
        if (typeof fieldValue === 'string') return fieldValue.includes(String(value));
        return false;
      case 'greater':
        return Number(fieldValue) > Number(value);
      case 'greater_or_equal':
        return Number(fieldValue) >= Number(value);
      case 'less':
        return Number(fieldValue) < Number(value);
      case 'less_or_equal':
        return Number(fieldValue) <= Number(value);
      case 'in':
        return Array.isArray(value) ? value.includes(fieldValue) : false;
      default:
        return true;
    }
  }

  /**
   * 获取指定层
   */
  getLayer(layerId) {
    return this.layers[layerId];
  }

  /**
   * 获取所有约束（从L3）
   */
  getConstraints() {
    const l3 = this.layers['L3-constraints'];
    if (!l3 || !l3.constraints) return {};
    return l3.constraints;
  }

  /**
   * 获取所有决策（从L4）
   */
  getDecisions() {
    const l4 = this.layers['L4-decisions'];
    if (!l4 || !l4.rules) return [];
    return l4.rules;
  }
}

module.exports = { RulesEngine };

// CLI 运行
if (require.main === module) {
  const engine = new RulesEngine();
  
  console.log('=== YL-AR-DGN 规则引擎 v1.2.0 ===\n');
  
  // 显示状态
  const status = engine.getStatus();
  console.log('配置版本:', status.configVersion);
  console.log('已加载层级:', status.loadedLayers.join(', '));
  console.log('冲突数量:', status.conflictCount);
  console.log('');
  
  // 验证规则
  console.log('=== 规则验证 ===');
  const validation = engine.validate();
  console.log('总体状态:', validation.overall);
  console.log('有效层级:', validation.summary.validLayers);
  console.log('错误层级:', validation.summary.errorLayers);
  console.log('总规则数:', validation.summary.totalRules);
  console.log('');
  
  // 显示部署状态
  console.log('=== 部署状态 ===');
  const deployStatus = status.deploymentStatus;
  console.log('当前成熟度:', deployStatus.currentMaturityLevel);
  console.log('目标成熟度:', deployStatus.targetMaturityLevel);
  console.log('总体进度:', deployStatus.overallProgress + '%');
  console.log('');
  
  // 执行示例
  console.log('=== 规则执行示例 ===');
  const ctx = {
    project: 'yl-ar-dgn',
    action: ['deploy'],
    phase: '3',
    deployment_maturity_level: 3
  };
  const result = engine.execute(ctx);
  console.log('输入上下文:', JSON.stringify(ctx, null, 2));
  console.log('执行结果:', JSON.stringify(result, null, 2));
}
