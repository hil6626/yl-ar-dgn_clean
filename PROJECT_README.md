# YL-AR-DGN 项目

## 项目概述

YL-AR-DGN 是一个增强现实(AR)数字人生成系统，包含以下核心组件：

- **AR-backend**: AR后端服务，提供实时视频处理、人脸合成、音频处理等功能
- **YL-monitor**: 监控和运维系统，提供系统监控、告警、资源优化等功能
- **User-GUI**: 用户界面，提供友好的交互体验

## 项目结构

```
yl-ar-dgn_clean/
├── AR-backend/          # AR后端服务
│   ├── app/            # 应用代码
│   ├── services/       # 服务模块
│   ├── config/         # 配置文件
│   └── ...
├── YL-monitor/          # 监控运维系统
│   ├── app/            # 应用代码
│   ├── scripts/        # 监控脚本
│   ├── docs/           # 文档
│   └── ...
├── 部署/                # 部署文档
├── scripts/            # 项目脚本
├── docs/               # 项目文档
├── config/             # 全局配置
└── infrastructure/     # 基础设施配置
```

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 启动AR后端服务
cd AR-backend && python main.py

# 启动监控系统
cd YL-monitor && python start_server.py
```

### 3. 访问服务

- AR后端服务: http://localhost:8000
- 监控面板: http://localhost:5000

## 文档索引

### 部署文档
- [部署索引](部署/0.部署索引.md)
- [项目部署大纲](部署/1.项目部署大纲.md)
- [整体方案](部署/2.整体方案.md)

### 开发文档
- [API标准](YL-monitor/docs/api-standard.md)
- [AR集成指南](YL-monitor/docs/ar-integration-guide.md)
- [前端开发指南](YL-monitor/docs/frontend-development-guide.md)

### 运维文档
- [部署指南](YL-monitor/docs/deployment-guide.md)
- [运维手册](YL-monitor/docs/operations-manual.md)
- [用户手册](YL-monitor/docs/user-manual.md)

## 核心功能

### AR-backend
- 实时视频处理
- 人脸检测与合成
- 音频处理
- 虚拟摄像头支持

### YL-monitor
- 系统资源监控
- 服务健康检查
- 告警通知
- 自动优化

## 技术栈

- **后端**: Python, FastAPI, Flask
- **前端**: HTML, CSS, JavaScript
- **监控**: Prometheus, Grafana
- **容器**: Docker, Docker Compose

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

[LICENSE](LICENSE)

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目Issues
- 邮件联系

---

**最后更新**: 2025年2月
