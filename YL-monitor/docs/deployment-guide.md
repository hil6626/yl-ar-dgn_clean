# YL-Monitor 部署指南

**版本**: 1.0.0  
**适用对象**: 运维工程师、系统管理员  
**最后更新**: 2026-02-10

---

## 📚 目录

1. [部署前准备](#一部署前准备)
2. [环境要求](#二环境要求)
3. [部署方式](#三部署方式)
4. [配置说明](#四配置说明)
5. [验证部署](#五验证部署)
6. [运维管理](#六运维管理)
7. [故障处理](#七故障处理)

---

## 一、部署前准备

### 1.1 部署架构选择

根据业务规模选择合适的部署架构：

| 架构类型 | 适用场景 | 服务器要求 | 特点 |
|----------|----------|------------|------|
| **单机部署** | 小规模 (<100节点) | 1台 4核8G | 简单快速 |
| **主从部署** | 中规模 (100-500节点) | 2台 8核16G | 高可用 |
| **集群部署** | 大规模 (>500节点) | 3+台 16核32G | 高可用+高性能 |

### 1.2 部署组件清单

**必需组件**:
- YL-Monitor 应用服务
- SQLite/PostgreSQL 数据库
- Redis 缓存 (可选，推荐)
- Nginx 反向代理

**可选组件**:
- Prometheus (指标存储)
- Grafana (可视化)
- ELK Stack (日志分析)

### 1.3 网络规划

```
┌─────────────────────────────────────────┐
│              用户访问层                   │
│         (浏览器/移动设备/API)             │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           Nginx 负载均衡层               │
│         (SSL终止/静态资源/限流)            │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           YL-Monitor 应用层              │
│    (Docker容器/多实例/健康检查)            │
└─────────────────────────────────────────┘
                    │
        ┌──────────┴──────────┐
        ▼                      ▼
┌──────────────┐      ┌──────────────┐
│   数据库层    │      │   缓存层      │
│ (SQLite/PG)  │      │  (Redis)     │
└──────────────┘      └──────────────┘
```

---

## 二、环境要求

### 2.1 系统要求

**操作系统**:
- Ubuntu 20.04 LTS 或更高版本 (推荐)
- CentOS 8 或更高版本
- Debian 11 或更高版本

**硬件要求** (单机部署):

| 资源 | 最低配置 | 推荐配置 | 说明 |
|------|----------|----------|------|
| CPU | 2核 | 4核 | 影响并发处理能力 |
| 内存 | 4GB | 8GB | 影响缓存和查询性能 |
| 磁盘 | 50GB SSD | 100GB SSD | 影响数据存储和I/O |
| 网络 | 100Mbps | 1Gbps | 影响数据传输 |

**软件依赖**:
- Docker 20.10+
- Docker Compose 2.0+
- Nginx 1.18+
- Python 3.9+ (如不使用Docker)

### 2.2 端口规划

| 端口 | 用途 | 协议 | 说明 |
|------|------|------|------|
| 80 | HTTP | TCP | Web访问入口 |
| 443 | HTTPS | TCP | 安全Web访问 |
| 8000 | 应用服务 | TCP | YL-Monitor服务 |
| 6379 | Redis | TCP | 缓存服务 (可选) |
| 5432 | PostgreSQL | TCP | 数据库服务 (可选) |

### 2.3 预安装检查

```bash
# 检查操作系统
cat /etc/os-release

# 检查Docker
docker --version
docker-compose --version

# 检查Nginx
nginx -v

# 检查磁盘空间
df -h

# 检查内存
free -h

# 检查CPU
nproc
cat /proc/cpuinfo | grep "model name"
```

---

## 三、部署方式

### 3.1 方式一：一键脚本部署 (推荐)

**适用场景**: 快速部署、标准化环境

**步骤**:

1. **下载部署脚本**
   ```bash
   # 克隆代码仓库
   git clone https://github.com/your-org/yl-monitor.git
   cd yl-monitor
   
   # 或使用已下载的代码包
   cd /path/to/yl-monitor
   ```

2. **执行部署**
   ```bash
   # 使用root权限执行
   sudo ./scripts/deploy.sh deploy
   ```

3. **等待部署完成**
   - 脚本会自动完成所有配置
   - 预计耗时 5-10 分钟

4. **验证部署**
   ```bash
   # 检查服务状态
   sudo ./scripts/deploy.sh status
   
   # 或查看日志
   sudo ./scripts/deploy.sh logs
   ```

**部署脚本功能**:
- ✅ 系统要求检查
- ✅ 自动备份现有部署
- ✅ 应用代码部署
- ✅ 环境变量配置
- ✅ Docker镜像构建
- ✅ 服务启动管理
- ✅ systemd服务配置
- ✅ Nginx反向代理配置
- ✅ 数据库迁移
- ✅ 部署验证

### 3.2 方式二：Docker Compose 部署

**适用场景**: 开发环境、自定义配置

**步骤**:

1. **准备配置文件**

   创建 `.env` 文件:
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   
   # 编辑配置
   nano .env
   ```

   关键配置项:
   ```env
   # 应用配置
   APP_NAME=yl-monitor
   DEBUG=false
   LOG_LEVEL=INFO
   
   # 数据库配置
   DATABASE_URL=sqlite:///data/yl_monitor.db
   
   # 安全配置
   JWT_SECRET_KEY=your-secret-key-here
   
   # 端口配置
   HTTP_PORT=8000
   ```

2. **启动服务**
   ```bash
   # 构建并启动
   docker-compose up -d --build
   
   # 查看日志
   docker-compose logs -f
   ```

3. **验证服务**
   ```bash
   # 健康检查
   curl http://0.0.0.0:8000/health
   
   # 查看API文档
   curl http://0.0.0.0:8000/api/docs
   ```

### 3.3 方式三：手动部署

**适用场景**: 特殊环境、深度定制

**步骤**:

1. **安装依赖**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install -y python3 python3-pip python3-venv nginx
   
   # CentOS/RHEL
   sudo yum install -y python3 python3-pip nginx
   ```

2. **创建应用目录**
   ```bash
   sudo mkdir -p /opt/yl-monitor
   sudo chown $USER:$USER /opt/yl-monitor
   cd /opt/yl-monitor
   ```

3. **部署代码**
   ```bash
   # 复制应用代码
   cp -r /path/to/source/* .
   
   # 创建虚拟环境
   python3 -m venv venv
   source venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   # 创建环境变量文件
   cat > .env << EOF
   APP_NAME=yl-monitor
   DATABASE_URL=sqlite:///data/yl_monitor.db
   JWT_SECRET_KEY=$(openssl rand -hex 32)
   EOF
   ```

5. **配置Nginx**
   ```bash
   # 创建Nginx配置
   sudo tee /etc/nginx/sites-available/yl-monitor << 'EOF'
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /static/ {
           alias /opt/yl-monitor/static/;
       }
   }
   EOF
   
   # 启用配置
   sudo ln -s /etc/nginx/sites-available/yl-monitor /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

6. **创建Systemd服务**
   ```bash
   sudo tee /etc/systemd/system/yl-monitor.service << 'EOF'
   [Unit]
   Description=YL-Monitor Application
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/yl-monitor
   EnvironmentFile=/opt/yl-monitor/.env
   ExecStart=/opt/yl-monitor/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # 启动服务
   sudo systemctl daemon-reload
   sudo systemctl enable yl-monitor
   sudo systemctl start yl-monitor
   ```

---

## 四、配置说明

### 4.1 环境变量配置

**核心配置项**:

| 变量名 | 默认值 | 说明 | 必填 |
|--------|--------|------|------|
| `APP_NAME` | yl-monitor | 应用名称 | 否 |
| `DEBUG` | false | 调试模式 | 否 |
| `LOG_LEVEL` | INFO | 日志级别 | 否 |
| `DATABASE_URL` | sqlite:///... | 数据库连接 | 是 |
| `JWT_SECRET_KEY` | - | JWT密钥 | 是 |
| `REDIS_URL` | - | Redis连接 | 否 |
| `SMTP_HOST` | - | 邮件服务器 | 否 |
| `HTTP_PORT` | 8000 | HTTP端口 | 否 |

**安全配置项**:

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `JWT_ALGORITHM` | HS256 | JWT算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | 访问Token过期时间 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | 刷新Token过期时间 |
| `MAX_LOGIN_ATTEMPTS` | 5 | 最大登录尝试次数 |
| `ENABLE_RATE_LIMIT` | true | 启用限流 |
| `RATE_LIMIT_REQUESTS` | 1000 | 限流请求数/小时 |

**性能配置项**:

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `CACHE_TTL` | 300 | 缓存TTL(秒) |
| `DB_POOL_SIZE` | 10 | 数据库连接池大小 |
| `ENABLE_COMPRESSION` | true | 启用响应压缩 |
| `MAX_CONCURRENT_TASKS` | 50 | 最大并发任务数 |

### 4.2 数据库配置

**SQLite (默认)**:
```env
DATABASE_URL=sqlite:///data/yl_monitor.db
```

**PostgreSQL (推荐生产环境)**:
```env
DATABASE_URL=postgresql://user:password@0.0.0.0:5432/yl_monitor
```

**MySQL**:
```env
DATABASE_URL=mysql://user:password@0.0.0.0:3306/yl_monitor
```

### 4.3 缓存配置

**内存缓存 (默认)**:
```env
CACHE_BACKEND=memory
CACHE_TTL=300
```

**Redis缓存 (推荐)**:
```env
CACHE_BACKEND=redis
REDIS_URL=redis://0.0.0.0:6379/0
REDIS_PASSWORD=your-redis-password
```

### 4.4 邮件通知配置

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true
FROM_EMAIL=noreply@yl-monitor.com
```

---

## 五、验证部署

### 5.1 健康检查

```bash
# 检查服务健康状态
curl http://0.0.0.0:8000/health

# 预期响应
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-10T10:30:00Z"
}
```

### 5.2 API测试

```bash
# 测试API接口
curl http://0.0.0.0:8000/api/v1/meta

# 测试认证
curl -X POST http://0.0.0.0:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 5.3 功能验证

**Web界面**:
1. 打开浏览器访问 `http://your-server-ip`
2. 使用默认账号登录
3. 检查各功能模块是否正常

**监控功能**:
1. 进入"监控中心"
2. 查看实时数据是否正常显示
3. 测试告警规则是否生效

### 5.4 性能验证

```bash
# 运行性能基准测试
python tests/performance/performance_benchmark.py

# 预期结果
# - API P95响应时间 < 200ms
# - 并发支持100+用户
# - 缓存命中率 > 80%
```

---

## 六、运维管理

### 6.1 日常运维命令

```bash
# 查看服务状态
sudo systemctl status yl-monitor

# 查看日志
sudo journalctl -u yl-monitor -f

# 重启服务
sudo systemctl restart yl-monitor

# 停止服务
sudo systemctl stop yl-monitor

# 使用部署脚本
sudo ./scripts/deploy.sh status
sudo ./scripts/deploy.sh logs
sudo ./scripts/deploy.sh restart
```

### 6.2 备份与恢复

**自动备份**:
- 系统每天自动备份到 `/opt/backups/yl-monitor/`
- 保留最近10个备份

**手动备份**:
```bash
# 创建备份
sudo ./scripts/deploy.sh backup

# 或手动备份
sudo tar -czf backup_$(date +%Y%m%d).tar.gz /opt/yl-monitor/data/
```

**数据恢复**:
```bash
# 使用部署脚本回滚
sudo ./scripts/deploy.sh rollback

# 或手动恢复
sudo systemctl stop yl-monitor
sudo rm -rf /opt/yl-monitor/data/*
sudo tar -xzf backup_20260210.tar.gz -C /
sudo systemctl start yl-monitor
```

### 6.3 日志管理

**日志位置**:
- 应用日志: `/var/log/yl-monitor/app.log`
- 错误日志: `/var/log/yl-monitor/error.log`
- 访问日志: `/var/log/nginx/yl-monitor-access.log`

**日志轮转**:
```bash
# 配置logrotate
sudo tee /etc/logrotate.d/yl-monitor << 'EOF'
/var/log/yl-monitor/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload yl-monitor
    endscript
}
EOF
```

### 6.4 监控与告警

**系统监控**:
```bash
# 检查资源使用
top
htop
df -h
free -h

# 检查网络
netstat -tlnp
ss -tlnp
```

**应用监控**:
- 内置健康检查: `/health`
- 指标端点: `/metrics`
- 性能监控: 使用性能基准测试脚本

---

## 七、故障处理

### 7.1 服务无法启动

**排查步骤**:
1. 检查日志: `sudo journalctl -u yl-monitor -n 100`
2. 检查配置: `cat /opt/yl-monitor/.env`
3. 检查端口: `sudo netstat -tlnp | grep 8000`
4. 检查权限: `ls -la /opt/yl-monitor/`

**常见原因**:
- 端口被占用
- 配置文件错误
- 数据库连接失败
- 权限不足

### 7.2 数据库连接失败

**排查步骤**:
1. 检查数据库服务: `sudo systemctl status postgresql`
2. 检查连接字符串: `grep DATABASE_URL /opt/yl-monitor/.env`
3. 测试连接: `psql $DATABASE_URL -c "SELECT 1"`

**解决方案**:
```bash
# 重启数据库
sudo systemctl restart postgresql

# 检查数据库权限
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE yl_monitor TO yl_user;"
```

### 7.3 性能问题

**排查步骤**:
1. 检查资源使用: `top`, `htop`
2. 检查慢查询: 查看应用日志
3. 检查缓存: 运行性能基准测试
4. 检查并发: 查看连接数

**优化建议**:
- 增加缓存TTL
- 优化数据库索引
- 增加硬件资源
- 启用Redis缓存

### 7.4 安全问题

**排查步骤**:
1. 运行安全渗透测试: `python tests/security/security_penetration_test.py`
2. 检查日志中的异常访问
3. 检查用户权限配置

**紧急处理**:
```bash
# 立即禁用可疑用户
# 修改JWT密钥使所有Token失效
# 重启服务
sudo systemctl restart yl-monitor
```

---

## 📞 技术支持

**部署问题**: deployment@yl-monitor.com  
**紧急支持**: +86-xxx-xxxx-xxxx  
**文档中心**: https://docs.yl-monitor.com/deployment

---

**文档版本**: 1.0.0  
**最后更新**: 2026-02-10  
**维护团队**: YL-Monitor DevOps Team
