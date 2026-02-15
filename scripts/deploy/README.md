# Deploy Scripts
# 部署脚本目录

**版本:** 1.0.0  
**最后更新:** 2026-02-05

本目录包含部署相关的脚本。

## 📁 目录内容

```
deploy/
├── deploy.sh           # 部署脚本
├── rollback.sh         # 回滚脚本
├── notify_deployment.py # 部署通知脚本
└── README.md           # 本文档
```

## 📖 脚本说明

### deploy.sh
**功能:** 主部署脚本  
**描述:** 执行完整的部署流程，包括：
- 停止旧服务
- 备份数据
- 拉取最新镜像
- 启动新服务
- 健康检查

**用法:**
```bash
./deploy.sh [environment]
# 示例: ./deploy.sh production
```

### rollback.sh
**功能:** 回滚脚本  
**描述:** 在部署失败时执行回滚操作，包括：
- 停止当前服务
- 恢复上一版本
- 验证服务状态

**用法:**
```bash
./rollback.sh [environment]
# 示例: ./rollback.sh production
```

### notify_deployment.py
**功能:** 部署通知脚本  
**描述:** 发送部署通知到：
- Slack
- 钉钉
- 邮件

**用法:**
```bash
python notify_deployment.py --status success --environment production
```

## 🔗 关联文档

| 文档 | 描述 |
|------|------|
| [AR-backend/DEPLOYMENT.md](../AR-backend/DEPLOYMENT.md) | AR后端部署文档 |
| [docker-compose.yml](../docker-compose.yml) | Docker编排配置 |

---

**版本:** 1.0.0  
**最后更新:** 2026-02-05
