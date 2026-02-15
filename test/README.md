# Test 目录

存放项目测试代码。

## 目录结构

```
test/
├── integration/            # 集成测试
├── performance/            # 性能测试
├── stability/              # 稳定性测试
├── test_backend/           # 后端测试
├── test_frontend/          # 前端测试
└── test_integration/       # 集成测试
```

## 测试说明

| 测试类型 | 说明 |
|----------|------|
| 单元测试 | 测试单个函数或类 |
| 集成测试 | 测试模块间交互 |
| 前端测试 | 测试前端组件 |
| 后端测试 | 测试 API 接口 |

## 运行测试

```bash
# 运行所有测试
pytest test/ -v

# 运行特定测试
pytest test/test_backend/ -v

# 生成覆盖率报告
pytest test/ --cov=src --cov-report=html
```

---

**最后更新**: 2026年2月9日
