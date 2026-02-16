# 贡献指南

**版本:** 1.0.0  
**最后更新:** 2026-02-16  
**欢迎:** 感谢您对 YL-AR-DGN 项目的关注！

---

## 📋 目录

1. [开始之前](#开始之前)
2. [贡献流程](#贡献流程)
3. [开发环境搭建](#开发环境搭建)
4. [代码规范](#代码规范)
5. [提交规范](#提交规范)
6. [审查流程](#审查流程)
7. [发布流程](#发布流程)

---

## 开始之前

### 行为准则

参与本项目即表示您同意遵守以下准则：

- **尊重他人**: 友好、耐心地对待所有参与者
- **接受批评**: 虚心接受建设性的批评
- **关注重点**: 关注对社区最有利的事情
- **展现同理心**: 理解不同观点和经验

### 您可以贡献的内容

| 类型 | 说明 | 示例 |
|------|------|------|
| **🐛 Bug 修复** | 修复代码中的错误 | 修复内存泄漏、修复崩溃问题 |
| **✨ 新功能** | 添加新功能 | 添加新的人脸模型、新的音频效果 |
| **📚 文档** | 改进文档 | 完善 API 文档、添加使用教程 |
| **🎨 界面优化** | 改进用户界面 | 优化 GUI 布局、改进监控面板 |
| **⚡ 性能优化** | 提升性能 | 优化视频处理速度、降低内存占用 |
| **🔧 工具改进** | 改进开发工具 | 改进脚本、添加自动化工具 |

---

## 贡献流程

### 流程图

```
1. Fork 项目
    ↓
2. 克隆到本地
    ↓
3. 创建功能分支
    ↓
4. 开发和测试
    ↓
5. 提交更改
    ↓
6. 推送到远程
    ↓
7. 创建 Pull Request
    ↓
8. 代码审查
    ↓
9. 合并到主分支
```

### 详细步骤

#### 步骤1: Fork 项目

1. 访问 https://github.com/your-org/YL-AR-DGN
2. 点击右上角的 **Fork** 按钮
3. 等待 Fork 完成

#### 步骤2: 克隆到本地

```bash
# 克隆您的 Fork
git clone https://github.com/YOUR_USERNAME/YL-AR-DGN.git
cd YL-AR-DGN

# 添加上游仓库
git remote add upstream https://github.com/your-org/YL-AR-DGN.git

# 验证远程仓库
git remote -v
# 应显示 origin 和 upstream
```

#### 步骤3: 创建功能分支

```bash
# 确保在主分支上
git checkout main

# 拉取最新更新
git pull upstream main

# 创建功能分支
git checkout -b feature/your-feature-name

# 分支命名规范:
# - feature/xxx - 新功能
# - bugfix/xxx - Bug 修复
# - docs/xxx - 文档更新
# - refactor/xxx - 代码重构
# - test/xxx - 测试相关
```

#### 步骤4: 开发和测试

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 进行开发...

# 运行测试
pytest

# 检查代码风格
flake8 .
black --check .

# 类型检查
mypy .

# 确保所有检查通过
```

#### 步骤5: 提交更改

```bash
# 添加更改的文件
git add .

# 提交（遵循提交规范）
git commit -m "feat: 添加新的人脸检测算法

- 实现基于 YOLOv8 的人脸检测
- 提升检测速度 30%
- 添加单元测试覆盖

Closes #123"

# 推送到您的 Fork
git push origin feature/your-feature-name
```

#### 步骤6: 创建 Pull Request

1. 访问 https://github.com/your-org/YL-AR-DGN
2. 点击 **New Pull Request**
3. 选择您的分支和目标分支
4. 填写 PR 描述（使用模板）
5. 提交 PR

---

## 开发环境搭建

### 快速搭建

```bash
# 1. 克隆项目
git clone https://github.com/YOUR_USERNAME/YL-AR-DGN.git
cd YL-AR-DGN

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. 验证安装
./scripts/yl-ar-dgn.sh validate

# 5. 运行测试
pytest
```

### 开发工具推荐

| 工具 | 用途 | 安装 |
|------|------|------|
| **VS Code** | 代码编辑器 | [下载](https://code.visualstudio.com/) |
| **PyCharm** | Python IDE | [下载](https://www.jetbrains.com/pycharm/) |
| **Git** | 版本控制 | `apt install git` |
| **Docker** | 容器化 | [下载](https://www.docker.com/) |

### VS Code 配置

创建 `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"]
}
```

---

## 代码规范

### 必须遵守的规范

1. **遵循 PEP 8**: Python 代码风格指南
2. **类型注解**: 所有函数添加类型提示
3. **文档字符串**: 所有公共 API 添加文档
4. **单元测试**: 新代码必须有测试覆盖
5. **错误处理**: 完善的异常处理

### 代码审查清单

提交前请确认:

- [ ] 代码遵循 [编码规范](coding-standards.md)
- [ ] 所有测试通过 (`pytest`)
- [ ] 代码覆盖率 > 80% (`pytest --cov`)
- [ ] 代码风格检查通过 (`flake8`, `black`)
- [ ] 类型检查通过 (`mypy`)
- [ ] 文档已更新
- [ ] 提交信息遵循规范

---

## 提交规范

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| **feat** | 新功能 | `feat: 添加实时滤镜功能` |
| **fix** | Bug 修复 | `fix: 修复内存泄漏问题` |
| **docs** | 文档更新 | `docs: 更新 API 文档` |
| **style** | 代码格式 | `style: 格式化代码` |
| **refactor** | 代码重构 | `refactor: 优化人脸检测算法` |
| **test** | 测试相关 | `test: 添加单元测试` |
| **chore** | 构建/工具 | `chore: 更新依赖` |

### 示例

```bash
# 好的提交信息
git commit -m "feat(face-swap): 添加新的深度学习模型

- 集成 InsightFace 模型
- 提升合成质量 25%
- 支持实时预览
- 添加性能测试

Closes #456"

# 差的提交信息
git commit -m "更新代码"
```

---

## 审查流程

### 审查标准

| 检查项 | 说明 | 优先级 |
|--------|------|--------|
| **功能正确性** | 代码是否实现了预期功能 | 🔴 高 |
| **代码质量** | 是否遵循编码规范 | 🔴 高 |
| **测试覆盖** | 是否有足够的测试 | 🔴 高 |
| **文档完整** | 是否更新了相关文档 | 🟡 中 |
| **性能影响** | 是否引入了性能问题 | 🟡 中 |
| **安全考虑** | 是否存在安全隐患 | 🔴 高 |

### 审查流程

1. **自动检查**: CI 运行测试和代码检查
2. **人工审查**: 维护者审查代码
3. **反馈修改**: 根据反馈修改代码
4. **最终批准**: 维护者批准合并

### 响应时间

| 类型 | 预期响应时间 |
|------|--------------|
| 首次响应 | 48 小时内 |
| 审查反馈 | 72 小时内 |
| 合并完成 | 审查通过后 24 小时内 |

---

## 发布流程

### 版本号规范

遵循 [语义化版本](https://semver.org/lang/zh-CN/):

```
主版本号.次版本号.修订号
```

| 版本变化 | 说明 | 示例 |
|----------|------|------|
| **主版本** | 不兼容的 API 修改 | `1.0.0` → `2.0.0` |
| **次版本** | 向下兼容的功能新增 | `1.0.0` → `1.1.0` |
| **修订号** | 向下兼容的问题修复 | `1.0.0` → `1.0.1` |

### 发布步骤

1. **更新版本号**: 修改所有组件的版本
2. **更新日志**: 更新 CHANGELOG.md
3. **创建标签**: `git tag -a v1.1.0 -m "版本 1.1.0"`
4. **推送标签**: `git push origin v1.1.0`
5. **创建 Release**: 在 GitHub 上创建 Release
6. **部署**: 自动触发部署流程

---

## 常见问题

### Q: 如何报告 Bug？

**A:** 使用 GitHub Issues:

1. 访问 Issues 页面
2. 点击 **New Issue**
3. 选择 **Bug Report** 模板
4. 填写详细信息:
   - 问题描述
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息
   - 日志/截图

### Q: 如何请求新功能？

**A:** 使用 GitHub Issues:

1. 访问 Issues 页面
2. 点击 **New Issue**
3. 选择 **Feature Request** 模板
4. 描述您的想法和使用场景

### Q: 我的 PR 为什么被拒绝了？

**A:** 常见原因:

- 代码不符合规范
- 缺少测试
- 缺少文档
- 与项目方向不符
- 存在更好的实现方式

请查看审查反馈并进行修改。

### Q: 如何成为维护者？

**A:** 持续贡献高质量代码:

1. 提交多个被合并的 PR
2. 帮助审查其他贡献者的 PR
3. 参与项目讨论
4. 维护者会主动邀请

---

## 资源链接

| 资源 | 链接 | 说明 |
|------|------|------|
| **项目仓库** | https://github.com/your-org/YL-AR-DGN | 主仓库 |
| **Issues** | https://github.com/your-org/YL-AR-DGN/issues | 问题跟踪 |
| **Discussions** | https://github.com/your-org/YL-AR-DGN/discussions | 讨论区 |
| **文档** | https://yl-ar-dgn.readthedocs.io | 在线文档 |
| **CI/CD** | https://github.com/your-org/YL-AR-DGN/actions | 自动化构建 |

---

## 联系方式

- **邮件**: maintainers@yl-ar-dgn.org
- **Slack**: [加入频道](https://yl-ar-dgn.slack.com)
- **微信**: 添加微信号 yl-ar-dgn

---

## 致谢

感谢所有贡献者让这个项目变得更好！

[![Contributors](https://contrib.rocks/image?repo=your-org/YL-AR-DGN)](https://github.com/your-org/YL-AR-DGN/graphs/contributors)

---

**最后更新:** 2026-02-16  
**维护者:** YL-AR-DGN 项目团队

**再次感谢您的贡献！** 🎉
