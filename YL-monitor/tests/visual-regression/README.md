# 视觉回归测试

## 概述

视觉回归测试用于检测UI的视觉变化，确保样式修改不会意外破坏页面布局。

## 测试范围

### 覆盖页面
- [x] 平台首页 (/)
- [x] 仪表盘 (/dashboard)
- [x] 脚本管理 (/scripts)
- [x] DAG流水线 (/dag)
- [x] AR监控 (/ar)
- [x] API文档 (/api-doc)

### 测试场景
1. **桌面端** (1920x1080) - 完整布局
2. **平板端** (1024x768) - 中等屏幕适配
3. **移动端** (375x667) - 小屏幕适配
4. **深色模式** - 主题切换测试

## 使用方式

### 1. 安装依赖
```bash
npm install -g playwright
playwright install
```

### 2. 生成基准截图
```bash
npm run test:visual:baseline
```

### 3. 运行对比测试
```bash
npm run test:visual
```

### 4. 查看报告
```bash
npm run test:visual:report
```

## 目录结构

```
tests/visual-regression/
├── README.md
├── playwright.config.js
├── baseline/           # 基准截图
│   ├── desktop/
│   ├── tablet/
│   └── mobile/
├── current/            # 当前截图
├── diff/              # 差异对比
└── reports/           # 测试报告
```

## 集成CI/CD

在GitHub Actions中自动运行：
```yaml
- name: Visual Regression Test
  run: |
    npm run test:visual
    if [ $? -ne 0 ]; then
      echo "::warning::视觉回归测试发现差异"
    fi
```

## 更新基准

当有意进行UI修改时，更新基准截图：
```bash
npm run test:visual:update
```

## 注意事项

1. **动态内容**: 测试中需要mock动态数据（时间、随机数等）
2. **动画**: 等待动画完成后再截图
3. **字体**: 使用系统字体避免跨平台差异
4. **时区**: 统一使用UTC时区
