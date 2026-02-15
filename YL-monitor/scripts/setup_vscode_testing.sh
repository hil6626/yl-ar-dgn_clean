#!/bin/bash
# VSCode 测试环境一键配置脚本

echo "=========================================="
echo "YL-Monitor VSCode 测试环境配置"
echo "=========================================="

# 1. 创建 .vscode 目录
echo "创建 VSCode 配置目录..."
mkdir -p .vscode

# 2. 创建 settings.json
echo "创建 settings.json..."
cat > .vscode/settings.json << 'EOF'
{
    "python.testing.pytestArgs": [
        "tests",
        "-v",
        "--cov=app",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term-missing"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true,
    "python.testing.autoTestDiscoverOnSaveEnabled": true,
    
    "coverage-gutters.showLineCoverage": true,
    "coverage-gutters.showRulerCoverage": true,
    "coverage-gutters.coverageBaseDir": "htmlcov",
    
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true
}
EOF

# 3. 创建 tasks.json
echo "创建 tasks.json..."
cat > .vscode/tasks.json << 'EOF'
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run All Tests",
            "type": "shell",
            "command": "python",
            "args": ["-m", "pytest", "tests", "-v", "--cov=app"],
            "group": {"kind": "test", "isDefault": true}
        },
        {
            "label": "Run Tests with Coverage",
            "type": "shell",
            "command": "python",
            "args": [
                "-m", "pytest", "tests", 
                "-v", 
                "--cov=app", 
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml"
            ],
            "group": "test"
        },
        {
            "label": "Auto Fix Imports",
            "type": "shell",
            "command": "python",
            "args": ["scripts/auto_fix_imports.py"],
            "group": "build"
        },
        {
            "label": "Code Quality Check",
            "type": "shell",
            "command": "python",
            "args": ["-m", "ruff", "check", "app", "tests"],
            "group": "build"
        }
    ]
}
EOF

# 4. 创建 keybindings.json
echo "创建 keybindings.json..."
cat > .vscode/keybindings.json << 'EOF'
[
    {
        "key": "ctrl+shift+t",
        "command": "workbench.action.tasks.runTask",
        "args": "Run All Tests"
    },
    {
        "key": "ctrl+shift+c",
        "command": "workbench.action.tasks.runTask",
        "args": "Run Tests with Coverage"
    },
    {
        "key": "ctrl+shift+f",
        "command": "workbench.action.tasks.runTask",
        "args": "Auto Fix Imports"
    }
]
EOF

echo ""
echo "=========================================="
echo "✅ VSCode 配置完成！"
echo "=========================================="
echo ""
echo "请安装以下 VSCode 扩展："
echo "  1. Python (Microsoft) - 已内置"
echo "  2. Coverage Gutters - 搜索安装"
echo "  3. Python Test Explorer - 搜索安装"
echo ""
echo "快捷键："
echo "  Ctrl+Shift+T - 运行所有测试"
echo "  Ctrl+Shift+C - 运行测试并生成覆盖率"
echo "  Ctrl+Shift+F - 自动修复导入错误"
echo ""
echo "更多详情请参考：docs/vscode-extension-testing-guide.md"
echo ""
