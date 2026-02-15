# YL-Monitor 测试体系

## 概述

YL-Monitor 测试体系包含三个层次的测试，确保系统的功能完整性、性能达标和用户体验。

## 测试结构

```
tests/
├── __init__.py                    # 测试包初始化
├── conftest.py                    # pytest配置和共享夹具
├── run_all_tests.py               # 统一测试执行入口
├── README.md                      # 测试文档
├── integration/                   # 集成测试
│   ├── __init__.py
│   └── test_module_linkage.py     # 模块联动性测试
├── performance/                   # 性能测试
│   ├── __init__.py
│   ├── test_frontend_performance.py  # 前端性能测试
│   └── test_api_performance.py    # API性能测试
└── uat/                           # 用户验收测试
    ├── __init__.py
    └── test_user_acceptance.py    # 用户验收测试
```

## 测试类型

### 1. 集成测试 (Integration Tests)

**目标**: 验证7项优化模块间的联动性

**测试场景**:
- 沉积清理管理器 ↔ 错误恢复服务联动
- 队列监控器 ↔ 仪表盘监控联动
- 渲染优化器 ↔ 性能监控脚本联动
- API客户端 ↔ 错误码定义一致性
- DAG可视化器 ↔ AR监控扩展接口兼容性
- WebSocket实时推送 ↔ 前端性能监控联动

**执行命令**:
```bash
pytest tests/integration/ -v
```

### 2. 性能测试 (Performance Tests)

**目标**: 验证性能指标是否达到优化目标

**性能目标**:
| 指标 | 目标值 | 测试文件 |
|------|--------|----------|
| FCP (首屏加载) | < 2秒 | test_frontend_performance.py |
| LCP (最大内容绘制) | < 2.5秒 | test_frontend_performance.py |
| FID (首次输入延迟) | < 100ms | test_frontend_performance.py |
| CLS (累积布局偏移) | < 0.1 | test_frontend_performance.py |
| 虚拟滚动 FPS | >= 60 | test_frontend_performance.py |
| API响应时间 P95 | < 500ms | test_api_performance.py |
| 并发处理能力 | 100并发 | test_api_performance.py |
| 吞吐量 | >= 50 req/s | test_api_performance.py |
| WebSocket延迟 | < 5秒 | test_frontend_performance.py |

**执行命令**:
```bash
pytest tests/performance/ -v
```

### 3. 用户验收测试 (UAT)

**目标**: 模拟真实用户场景，验证功能完整性和用户体验

**测试场景**:
- 监控脚本执行流程完整性
- DAG可视化交互体验
- 仪表盘实时数据展示准确性
- 告警通知渠道可用性
- 主题切换功能
- 移动端适配性
- 文档可读性和完整性

**执行命令**:
```bash
pytest tests/uat/ -v
```

## 使用方法

### 运行所有测试

```bash
python tests/run_all_tests.py
```

### 运行特定类型测试

```bash
# 集成测试
python tests/run_all_tests.py --type integration

# 性能测试
python tests/run_all_tests.py --type performance

# 用户验收测试
python tests/run_all_tests.py --type uat
```

### 生成测试报告

```bash
# HTML报告
python tests/run_all_tests.py --report

# 覆盖率报告
python tests/run_all_tests.py --coverage

# 详细输出
python tests/run_all_tests.py --verbose
```

### 使用pytest直接运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行集成测试
pytest tests/integration/test_module_linkage.py -v

# 运行性能测试
pytest tests/performance/test_frontend_performance.py -v

# 运行UAT测试
pytest tests/uat/test_user_acceptance.py -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 生成HTML测试报告
pytest tests/ --html=tests/reports/report.html --self-contained-html
```

## 测试夹具 (Fixtures)

### 数据夹具

- `sample_metrics_data`: 示例监控指标数据
- `sample_alert_data`: 示例告警数据
- `sample_dag_data`: 示例DAG数据
- `sample_script_data`: 示例脚本数据

### 服务夹具

- `mock_dashboard_monitor`: 模拟仪表盘监控器
- `mock_alert_service`: 模拟告警服务
- `mock_script_engine`: 模拟脚本引擎

### 配置夹具

- `performance_thresholds`: 性能测试阈值
- `test_config`: 测试环境配置
- `test_helpers`: 测试辅助函数

## 测试标记

- `integration`: 集成测试
- `performance`: 性能测试
- `uat`: 用户验收测试
- `slow`: 慢速测试（执行时间较长）

## 性能目标

### 前端性能

| 指标 | 目标 | 优先级 |
|------|------|--------|
| FCP | < 2秒 | P0 |
| LCP | < 2.5秒 | P0 |
| FID | < 100ms | P1 |
| CLS | < 0.1 | P1 |
| 虚拟滚动 FPS | >= 60 | P0 |

### API性能

| 指标 | 目标 | 优先级 |
|------|------|--------|
| 响应时间 P95 | < 500ms | P0 |
| 并发处理 | 100并发 | P0 |
| 吞吐量 | >= 50 req/s | P1 |
| 错误率 | < 0.1% | P0 |

## 持续集成

建议在CI/CD流程中集成以下测试步骤：

```yaml
# .github/workflows/test.yml 示例
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx
          
      - name: Run integration tests
        run: pytest tests/integration/ -v
        
      - name: Run performance tests
        run: pytest tests/performance/ -v
        
      - name: Run UAT tests
        run: pytest tests/uat/ -v
        
      - name: Generate coverage report
        run: pytest tests/ --cov=app --cov-report=xml
        
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 注意事项

1. **性能测试**: 性能测试需要在稳定的环境中运行，避免其他进程干扰
2. **集成测试**: 部分集成测试需要相关服务运行，可能需要使用mock
3. **UAT测试**: UAT测试模拟真实用户场景，可能需要更长的执行时间
4. **测试数据**: 测试使用模拟数据，不会影响生产环境

## 问题排查

### 测试失败常见原因

1. **依赖未安装**: 确保安装了所有测试依赖
   ```bash
   pip install pytest pytest-asyncio pytest-cov httpx
   ```

2. **服务未运行**: 部分测试需要服务运行，使用mock或启动服务

3. **端口冲突**: 确保测试端口未被占用

4. **权限问题**: 确保测试文件有执行权限
   ```bash
   chmod +x tests/run_all_tests.py
   ```

## 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-02-09 | 初始版本，包含集成测试、性能测试、UAT测试 |

## 联系方式

如有测试相关问题，请参考项目文档或联系开发团队。
