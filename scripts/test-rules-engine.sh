#!/bin/bash
# YL-AR-DGN 规则引擎集成测试脚本
# 版本: 1.0.0
# 用途: 验证规则引擎功能完整性和规则文件正确性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/home/vboxuser/桌面/项目部署/项目1/yl-ar-dgn_clean"
RULES_DIR="$PROJECT_ROOT/rules"

echo "=========================================="
echo "YL-AR-DGN 规则引擎集成测试"
echo "=========================================="
echo ""

# 测试计数器
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -n "测试 $TESTS_TOTAL: $test_name ... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}通过${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}失败${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "1. 文件存在性检查"
echo "-------------------"

# 测试1-5: 检查规则文件是否存在
run_test "L1-meta-goal.json 存在" "test -f $RULES_DIR/L1-meta-goal.json"
run_test "L2-understanding.json 存在" "test -f $RULES_DIR/L2-understanding.json"
run_test "L3-constraints.json 存在" "test -f $RULES_DIR/L3-constraints.json"
run_test "L4-decisions.json 存在" "test -f $RULES_DIR/L4-decisions.json"
run_test "L5-execution.json 存在" "test -f $RULES_DIR/L5-execution.json"
run_test "rules.config.js 存在" "test -f $RULES_DIR/rules.config.js"
run_test "index.js 存在" "test -f $RULES_DIR/index.js"

echo ""
echo "2. JSON格式验证"
echo "----------------"

# 测试8-12: 验证JSON格式
run_test "L1-meta-goal.json 格式正确" "python3 -c \"import json; json.load(open('$RULES_DIR/L1-meta-goal.json'))\""
run_test "L2-understanding.json 格式正确" "python3 -c \"import json; json.load(open('$RULES_DIR/L2-understanding.json'))\""
run_test "L3-constraints.json 格式正确" "python3 -c \"import json; json.load(open('$RULES_DIR/L3-constraints.json'))\""
run_test "L4-decisions.json 格式正确" "python3 -c \"import json; json.load(open('$RULES_DIR/L4-decisions.json'))\""
run_test "L5-execution.json 格式正确" "python3 -c \"import json; json.load(open('$RULES_DIR/L5-execution.json'))\""

echo ""
echo "3. 规则结构验证"
echo "----------------"

# 测试13-17: 验证规则文件基本结构
run_test "L1 包含 goals 数组" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L1-meta-goal.json')); assert 'goals' in d and isinstance(d['goals'], list)\""
run_test "L2 包含 architecture.modules 数组" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L2-understanding.json')); assert 'architecture' in d and 'modules' in d['architecture'] and isinstance(d['architecture']['modules'], list)\""
run_test "L3 包含 constraints 对象" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L3-constraints.json')); assert 'constraints' in d and isinstance(d['constraints'], dict)\""
run_test "L4 包含 rules 数组" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L4-decisions.json')); assert 'rules' in d and isinstance(d['rules'], list)\""
run_test "L5 包含 executionPlans 对象" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L5-execution.json')); assert 'executionPlans' in d and isinstance(d['executionPlans'], dict)\""

echo ""
echo "4. 版本信息验证"
echo "----------------"

# 测试18-22: 验证版本信息
run_test "L1 版本 >= 1.2.0" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L1-meta-goal.json')); assert d.get('version', '0') >= '1.2.0'\""
run_test "L2 版本 >= 1.2.0" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L2-understanding.json')); assert d.get('version', '0') >= '1.2.0'\""
run_test "L3 版本 >= 1.2.0" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L3-constraints.json')); assert d.get('version', '0') >= '1.2.0'\""
run_test "L4 版本 >= 1.2.0" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L4-decisions.json')); assert d.get('version', '0') >= '1.2.0'\""
run_test "L5 版本 >= 1.2.0" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L5-execution.json')); assert d.get('version', '0') >= '1.2.0'\""

echo ""
echo "5. 部署状态验证"
echo "----------------"

# 测试23-25: 验证部署状态
run_test "L1 包含阶段1完成状态" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L1-meta-goal.json')); g=d.get('goals', []); assert any('monitoring-integration' in str(gi) and gi.get('status')=='completed' for gi in g)\""
run_test "L3 包含 deploymentStatus" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L3-constraints.json')); assert 'deploymentStatus' in d\""
run_test "L4 包含 deploymentStatus" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L4-decisions.json')); assert 'deploymentStatus' in d\""

echo ""
echo "6. 规则引擎功能测试"
echo "---------------------"

# 测试26: 规则引擎可以加载
if command -v node &> /dev/null; then
    run_test "规则引擎可以加载" "cd $RULES_DIR && node -e \"const {RulesEngine} = require('./index.js'); const engine = new RulesEngine(); console.log('OK');\""
    
    # 测试27: 规则引擎可以执行
    run_test "规则引擎可以执行" "cd $RULES_DIR && node -e \"const {RulesEngine} = require('./index.js'); const engine = new RulesEngine(); const result = engine.execute({phase: '3'}); console.log('OK');\""
    
    # 测试28: 规则引擎可以验证
    run_test "规则引擎可以验证" "cd $RULES_DIR && node -e \"const {RulesEngine} = require('./index.js'); const engine = new RulesEngine(); const v = engine.validate(); console.log(v.overall);\" | grep -q 'success'"
    
    # 测试29: 可以获取部署状态
    run_test "可以获取部署状态" "cd $RULES_DIR && node -e \"const {RulesEngine} = require('./index.js'); const engine = new RulesEngine(); const s = engine.getDeploymentStatus(); console.log(s.currentMaturityLevel);\" | grep -q '[0-9]'"
else
    echo -e "${YELLOW}警告: Node.js 未安装，跳过规则引擎功能测试${NC}"
fi

echo ""
echo "7. 约束定义验证"
echo "----------------"

# 测试30-33: 验证关键约束存在
run_test "L3 包含 entrypoints-consistency 约束" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L3-constraints.json')); c=d.get('constraints', {}).get('technical', []); assert any(ci.get('id')=='entrypoints-consistency' for ci in c)\""
run_test "L3 包含 monitoring-endpoints 约束" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L3-constraints.json')); c=d.get('constraints', {}).get('technical', []); assert any(ci.get('id')=='monitoring-endpoints' for ci in c)\""
run_test "L3 包含 quick-ops-scripts 约束" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L3-constraints.json')); c=d.get('constraints', {}).get('operational', []); assert any(ci.get('id')=='quick-ops-scripts' for ci in c)\""
run_test "L3 包含 port-allocation 约束" "python3 -c \"import json; d=json.load(open('$RULES_DIR/L3-constraints.json')); c=d.get('constraints', {}).get('resource', []); assert any(ci.get('id')=='port-allocation' for ci in c)\""

echo ""
echo "=========================================="
echo "测试结果汇总"
echo "=========================================="
echo -e "总测试数: $TESTS_TOTAL"
echo -e "通过: ${GREEN}$TESTS_PASSED${NC}"
echo -e "失败: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 所有测试通过！规则引擎集成测试成功。${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ 有 $TESTS_FAILED 个测试失败，请检查规则文件。${NC}"
    exit 1
fi
