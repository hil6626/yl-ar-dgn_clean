/**
 * yl-ar-dgn 五层规则引擎（轻量版）
 *
 * 设计目标：
 * - 以 JSON 为源：L1~L5 分层文件
 * - 规则可渐进增强：优先可读，其次可执行
 *
 * 注意：当前引擎只做“简单条件 → 写入上下文”的最小实现；
 * 后续可逐步扩展为：行动队列、校验器、场景/模块化加载。
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
    // eslint-disable-next-line global-require, import/no-dynamic-require
    this.config = options.config || require(path.join(this.rulesDir, 'rules.config.js'));
    this.layers = {};
    this.loadLayers();
  }

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
      if (!fs.existsSync(filePath)) continue;
      const layerId = file.replace(/\.json$/i, '');
      this.layers[layerId] = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    }
  }

  execute(context = {}) {
    let result = { ...context };

    for (const file of this.config.layerFiles || []) {
      const layerId = file.replace(/\.json$/i, '');
      result = this.applyLayer(layerId, result);
    }

    return result;
  }

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

  evaluateCondition(condition, context) {
    if (!condition) return true;

    const { field, operator, value } = condition;
    const fieldValue = getByPath(context, field);

    switch (operator) {
      case 'equals':
        // 将 null 视作 “未设置”（兼容 undefined）
        if (value === null) return fieldValue == null; // eslint-disable-line eqeqeq
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

  getLayer(layerId) {
    return this.layers[layerId];
  }
}

module.exports = { RulesEngine };

if (require.main === module) {
  const engine = new RulesEngine();
  const ctx = {
    project: 'yl-ar-dgn',
    action: ['deploy'],
    phase: 'development',
    deployment_maturity_level: engine.config.deploymentMaturity?.defaultLevel ?? 1
  };
  // eslint-disable-next-line no-console
  console.log(JSON.stringify(engine.execute(ctx), null, 2));
}
