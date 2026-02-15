# API安全模块

**模块路径:** `AR-backend/services/`  
**版本:** 1.0.0  
**最后更新:** 2026-02-04

---

## 模块概述

API安全模块提供完整的认证、授权和审计功能，确保API接口的安全性。

## 模块结构

```
AR-backend/services/
├── auth.py           # JWT认证和API密钥认证
├── rbac.py           # 基于角色的访问控制
├── audit.py          # 审计日志记录
└── security.py       # 安全工具和入侵检测
```

## 功能特性

### 1. 认证功能 (auth.py)

| 功能 | 说明 | 状态 |
|------|------|------|
| JWT访问令牌 | 创建和验证JWT访问令牌 | ✅ 已完成 |
| JWT刷新令牌 | 创建和验证刷新令牌 | ✅ 已完成 |
| OAuth2支持 | 第三方OAuth2认证 | ✅ 已完成 |
| API密钥认证 | API密钥创建和验证 | ✅ 已完成 |
| Token刷新 | 自动刷新访问令牌 | ✅ 已完成 |

### 2. 授权功能 (rbac.py)

| 功能 | 说明 | 状态 |
|------|------|------|
| 角色定义 | 7种预定义角色 | ✅ 已完成 |
| 权限管理 | 细粒度权限控制 | ✅ 已完成 |
| 角色继承 | 支持角色权限继承 | ✅ 已完成 |
| 资源访问控制 | 基于资源的访问控制 | ✅ 已完成 |
| 策略验证 | 访问策略验证 | ✅ 已完成 |

### 3. 审计功能 (audit.py)

| 功能 | 说明 | 状态 |
|------|------|------|
| 审计日志 | 记录所有操作 | ✅ 已完成 |
| 日志查询 | 灵活的日志查询 | ✅ 已完成 |
| 统计报告 | 生成统计报告 | ✅ 已完成 |
| 日志导出 | 导出日志数据 | ✅ 已完成 |
| 自动清理 | 自动清理旧日志 | ✅ 已完成 |

## 使用示例

### JWT认证

```python
from services.auth import JWTAuth

# 创建认证服务
auth = JWTAuth(
    secret_key="your-secret-key",
    access_token_expire_minutes=30,
    refresh_token_expire_days=7
)

# 创建访问令牌
access_token = auth.create_access_token(
    user_id="user123",
    role="admin",
    permissions=["user:read", "user:write"]
)

# 验证令牌
payload = auth.verify_token(access_token)
if payload:
    print(f"用户: {payload.user_id}")
    print(f"角色: {payload.role}")
```

### RBAC权限检查

```python
from services.rbac import RBAC, Role, Permission

# 创建RBAC服务
rbac = RBAC()

# 检查权限
if rbac.has_permission(Role.ADMIN, Permission.USER_DELETE):
    print("有删除用户的权限")

# 获取角色权限
permissions = rbac.get_role_permissions(Role.MANAGER)
print(f"经理角色权限: {[p.value for p in permissions]}")
```

### 审计日志

```python
from services.audit import AuditLogger, AuditAction, AuditStatus

# 创建审计日志记录器
logger = AuditLogger(log_dir="logs/audit")

# 记录审计日志
logger.log(
    action=AuditAction.CREATE,
    user_id="user123",
    user_role="admin",
    resource_type="data",
    resource_id="data456",
    details={"name": "测试数据"},
    ip_address="192.168.1.100",
    status=AuditStatus.SUCCESS
)
```

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| JWT_SECRET_KEY | JWT签名密钥 | 自动生成 |
| JWT_ALGORITHM | 加密算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 访问令牌过期时间 | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | 刷新令牌过期时间 | 7 |
| AUDIT_LOG_DIR | 审计日志目录 | logs/audit |
| AUDIT_MAX_DAYS | 日志保留天数 | 30 |

### 角色权限配置

```python
from services.rbac import RBAC, Role, Permission

# 自定义角色配置
custom_config = {
    Role.ADMIN: RolePermissions(
        role=Role.ADMIN,
        permissions=set(Permission),
        inherits=[],
        description="系统管理员"
    ),
    # ... 其他角色
}

rbac = RBAC(role_config=custom_config)
```

## 安全最佳实践

### 1. 密钥管理

- 使用强随机密钥
- 定期轮换密钥
- 使用环境变量存储密钥
- 不要在代码中硬编码密钥

### 2. Token安全

- 设置合理的过期时间
- 使用HTTPS传输
- 实现Token刷新机制
- 记录Token使用情况

### 3. 审计日志

- 记录所有敏感操作
- 保护日志文件
- 定期归档日志
- 监控异常行为

## 测试

```bash
# 运行认证测试
pytest test/test_auth.py -v

# 运行权限测试
pytest test/test_rbac.py -v

# 运行审计测试
pytest test/test_audit.py -v

# 运行所有安全测试
pytest test/test_security.py -v
```

## 依赖

```txt
PyJWT>=2.8.0
python-jose[cryptography]>=3.3.0
```

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-02-04 | 初始版本发布 |

## 维护者

- AI 编程代理

## 许可证

项目许可证
