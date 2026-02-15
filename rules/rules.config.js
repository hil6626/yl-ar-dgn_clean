// rules.config.js - 规则引擎基本配置
module.exports = {
  name: "yl-ar-dgn-rules",
  version: "1.0.0",
  docs: {
    frontendInteractionSpec: "../docs/project/rules-docs/frontend-interaction-spec.md",
  },
  layerFiles: [
    "L1-meta-goal.json",
    "L2-understanding.json",
    "L3-constraints.json",
    "L4-decisions.json",
    "L5-execution.json"
  ],
  deploymentMaturity: {
    defaultLevel: 1
  }
};
