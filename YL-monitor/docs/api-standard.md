# YL-Monitor API设计规范

**版本**: 1.0.0  
**创建时间**: 2026-02-08  
**适用范围**: 全项目API设计

---

## 一、设计原则

### 1.1 RESTful设计

- **资源导向**: URL表示资源，而非操作
- **HTTP动词**: 使用标准HTTP方法表示操作
- **状态码**: 使用标准HTTP状态码
- **无状态**: 每个请求独立，不依赖上下文

### 1.2 一致性

- **命名规范**: 统一使用小写字母和下划线
- **数据格式**: 统一使用JSON
- **错误格式**: 统一的错误响应结构
- **时间格式**: 统一使用ISO 8601格式

### 1.3 安全性

- **认证**: 使用Token认证
- **授权**: 基于角色的访问控制
- **验证**: 输入数据严格验证
- **限流**: 防止API滥用

---

## 二、URL设计

### 2.1 URL结构

```
/api/{version}/{resource}/{id}/{sub-resource}
```

**示例**:
- `/api/v1/scripts` - 脚本列表
- `/api/v1/scripts/123` - 特定脚本
- `/api/v1/scripts/123/runs` - 脚本的执行记录

### 2.2 版本控制

- **URL路径**: `/api/v1/`, `/api/v2/`
- **向后兼容**: 新版本不破坏旧版本
- **弃用通知**: 提前通知API弃用

### 2.3 资源命名

| 资源 | URL | 说明 |
|------|-----|------|
| 脚本 | `/scripts` | 监控脚本 |
| DAG | `/dags` | 工作流定义 |
| 告警 | `/alerts` | 告警记录 |
| 指标 | `/metrics` | 监控指标 |
| 仪表盘 | `/dashboards` | 仪表盘配置 |

---

## 三、HTTP方法

### 3.1 方法使用

| 方法 | 用途 | 幂等性 | 示例 |
|------|------|--------|------|
| GET | 获取资源 | 是 | `GET /api/v1/scripts` |
| POST | 创建资源 | 否 | `POST /api/v1/scripts` |
| PUT | 更新资源（完整） | 是 | `PUT /api/v1/scripts/123` |
| PATCH | 更新资源（部分） | 否 | `PATCH /api/v1/scripts/123` |
| DELETE | 删除资源 | 是 | `DELETE /api/v1/scripts/123` |

### 3.2 批量操作

```
POST /api/v1/scripts/batch
{
    "operation": "delete",
    "ids": ["1", "2", "3"]
}
```

---

## 四、请求格式

### 4.1 请求头部

| 头部 | 必需 | 说明 |
|------|------|------|
| Content-Type | 是 | `application/json` |
| Authorization | 是 | `Bearer {token}` |
| X-Request-ID | 否 | 请求唯一标识 |
| Accept | 否 | `application/json` |

### 4.2 请求体

```json
{
    "name": "cpu_monitor",
    "type": "monitor",
    "config": {
        "interval": 60,
        "threshold": 80
    }
}
```

### 4.3 查询参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| page | int | 页码 | `?page=1` |
| per_page | int | 每页数量 | `?per_page=20` |
| sort | string | 排序字段 | `?sort=-created_at` |
| filter | string | 过滤条件 | `?filter=status:active` |
| fields | string | 返回字段 | `?fields=id,name,status` |

---

## 五、响应格式

### 5.1 成功响应

```json
{
    "success": true,
    "data": {
        "id": "123",
        "name": "cpu_monitor",
        "status": "active",
        "created_at": "2026-02-08T10:30:00Z"
    },
    "meta": {
        "page": 1,
        "per_page": 20,
        "total": 100,
        "total_pages": 5
    }
}
```

### 5.2 列表响应

```json
{
    "success": true,
    "data": [
        {
            "id": "1",
            "name": "script1"
        },
        {
            "id": "2",
            "name": "script2"
        }
    ],
    "meta": {
        "page": 1,
        "per_page": 20,
        "total": 100
    }
}
```

### 5.3 错误响应

```json
{
    "success": false,
    "error": {
        "code": "VAL_3000",
        "message": "参数无效: name不能为空",
        "category": "VALIDATION",
        "http_status": 400,
        "request_id": "req_abc123",
        "details": {
            "field": "name",
            "constraint": "required"
        }
    }
}
```

---

## 六、HTTP状态码

### 6.1 成功状态码

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | GET请求成功 |
| 201 | Created | POST创建成功 |
| 202 | Accepted | 异步任务已接受 |
| 204 | No Content | DELETE成功 |

### 6.2 客户端错误

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 400 | Bad Request | 请求格式错误 |
| 401 | Unauthorized | 未认证 |
| 403 | Forbidden | 无权限 |
| 404 | Not Found | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 422 | Unprocessable | 验证失败 |
| 429 | Too Many Requests | 请求过于频繁 |

### 6.3 服务端错误

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 500 | Internal Error | 服务器内部错误 |
| 502 | Bad Gateway | 网关错误 |
| 503 | Service Unavailable | 服务不可用 |
| 504 | Gateway Timeout | 网关超时 |

---

## 七、错误处理

### 7.1 错误码体系

使用 `app/utils/error_codes.py` 中定义的标准错误码：

| 错误码 | 含义 | HTTP状态 |
|--------|------|----------|
| SUCCESS | 成功 | 200 |
| SYS_1000 | 未知错误 | 500 |
| VAL_3000 | 参数无效 | 400 |
| AUTH_4000 | 未授权 | 401 |
| BIZ_2003 | 数据不存在 | 404 |

### 7.2 错误响应示例

**参数错误**:
```json
{
    "success": false,
    "error": {
        "code": "VAL_3000",
        "message": "参数无效",
        "details": {
            "field": "email",
            "error": "格式不正确"
        }
    }
}
```

**认证错误**:
```json
{
    "success": false,
    "error": {
        "code": "AUTH_4000",
        "message": "未授权",
        "details": {
            "reason": "token过期"
        }
    }
}
```

---

## 八、认证授权

### 8.1 Token认证

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 8.2 Token刷新

```
POST /api/v1/auth/refresh
{
    "refresh_token": "..."
}
```

### 8.3 权限控制

- **角色**: admin, operator, viewer
- **权限**: 基于资源的CRUD权限

---

## 九、分页规范

### 9.1 请求参数

```
GET /api/v1/scripts?page=1&per_page=20&sort=-created_at
```

### 9.2 响应格式

```json
{
    "success": true,
    "data": [...],
    "meta": {
        "page": 1,
        "per_page": 20,
        "total": 100,
        "total_pages": 5,
        "has_next": true,
        "has_prev": false
    }
}
```

### 9.3 游标分页（大数据量）

```
GET /api/v1/logs?cursor=xxx&limit=100
```

---

## 十、过滤和排序

### 10.1 过滤

```
GET /api/v1/scripts?filter=status:active,type:monitor
```

### 10.2 排序

```
GET /api/v1/scripts?sort=-created_at,name
```

- `+` 或无前缀: 升序
- `-`: 降序

### 10.3 字段选择

```
GET /api/v1/scripts?fields=id,name,status
```

---

## 十一、文件上传

### 11.1 单文件上传

```
POST /api/v1/files
Content-Type: multipart/form-data

file: [二进制数据]
```

### 11.2 响应

```json
{
    "success": true,
    "data": {
        "file_id": "xxx",
        "url": "https://...",
        "size": 1024,
        "mime_type": "image/png"
    }
}
```

---

## 十二、WebSocket API

### 12.1 连接

```
wss://api.example.com/ws/metrics
```

### 12.2 消息格式

```json
{
    "type": "subscribe",
    "channel": "system_metrics",
    "filters": ["cpu", "memory"]
}
```

### 12.3 实时数据推送

```json
{
    "type": "metrics",
    "timestamp": "2026-02-08T10:30:00Z",
    "data": {
        "cpu": 45.2,
        "memory": 67.8
    }
}
```

---

## 十三、API版本管理

### 13.1 版本策略

- **当前版本**: v1
- **支持版本**: 最近2个主版本
- **弃用通知**: 提前6个月通知

### 13.2 版本信息

```
GET /api/meta
```

```json
{
    "api_version": "1.0.0",
    "supported_versions": ["v1", "v2"],
    "deprecated_versions": [],
    "documentation_url": "https://docs.example.com"
}
```

---

## 十四、限流策略

### 14.1 限流头部

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1644300000
```

### 14.2 限流响应

```json
{
    "success": false,
    "error": {
        "code": "EXT_5004",
        "message": "请求过于频繁",
        "details": {
            "retry_after": 60
        }
    }
}
```

---

## 十五、最佳实践

### 15.1 设计检查清单

- [ ] URL使用小写字母和下划线
- [ ] 使用复数名词表示资源
- [ ] 正确使用HTTP方法
- [ ] 返回适当的状态码
- [ ] 错误响应包含错误码和详情
- [ ] 支持分页和过滤
- [ ] 实现认证和授权
- [ ] 添加API文档

### 15.2 性能优化

- [ ] 使用缓存（ETag, Last-Modified）
- [ ] 支持字段选择
- [ ] 实现压缩（gzip, brotli）
- [ ] 使用连接池
- [ ] 异步处理

### 15.3 安全建议

- [ ] 使用HTTPS
- [ ] 验证所有输入
- [ ] 防止SQL注入
- [ ] 防止XSS攻击
- [ ] 实现CSRF保护
- [ ] 记录安全日志

---

## 十六、附录

### 16.1 参考文档

- [RESTful API设计指南](https://restfulapi.net/)
- [HTTP状态码](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [JSON API规范](https://jsonapi.org/)

### 16.2 更新记录

| 版本 | 时间 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2026-02-08 | 初始版本 |

---

**维护者**: AI Assistant  
**审核状态**: 待审核
