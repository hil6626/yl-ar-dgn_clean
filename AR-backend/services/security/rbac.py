#!/usr/bin/env python3
"""
Role-Based Access Control (RBAC) Service
YL-AR-DGN API Security Module
"""

from typing import List, Set, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from functools import lru_cache


class Permission(Enum):
    """
    权限枚举
    
    定义系统中所有可用的权限。
    """
    # 用户权限
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"
    
    # 数据权限
    DATA_READ = "data:read"
    DATA_WRITE = "data:write"
    DATA_DELETE = "data:delete"
    DATA_EXPORT = "data:export"
    DATA_IMPORT = "data:import"
    
    # 系统权限
    SYSTEM_CONFIG = "system:config"
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_LOG = "system:log"
    SYSTEM_MONITOR = "system:monitor"
    
    # API权限
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_DELETE = "api:delete"
    API_DOCS = "api:docs"
    
    # 监控权限
    MONITOR_VIEW = "monitor:view"
    MONITOR_ALERT = "monitor:alert"
    MONITOR_DASHBOARD = "monitor:dashboard"
    
    # 规则权限
    RULES_READ = "rules:read"
    RULES_WRITE = "rules:write"
    RULES_DELETE = "rules:delete"


class Role(Enum):
    """
    角色枚举
    
    定义系统中所有可用的角色。
    """
    ADMIN = "admin"
    MANAGER = "manager"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    USER = "user"
    VIEWER = "viewer"
    GUEST = "guest"


@dataclass
class RolePermissions:
    """
    角色权限配置数据类
    
    Attributes:
        role: 角色
        permissions: 直接权限集合
        inherits: 继承的角色列表
        description: 角色描述
        priority: 角色优先级
    """
    role: Role
    permissions: Set[Permission] = field(default_factory=set)
    inherits: List[Role] = field(default_factory=list)
    description: str = ""
    priority: int = 0


class RBAC:
    """
    基于角色的访问控制服务类
    
    提供权限检查、角色管理和访问控制功能。
    
    Attributes:
        role_config: 角色权限配置
    """
    
    # 默认角色权限配置
    DEFAULT_ROLE_CONFIG: Dict[Role, RolePermissions] = {
        Role.ADMIN: RolePermissions(
            role=Role.ADMIN,
            permissions=set(Permission),  # 所有权限
            inherits=[],
            description="系统管理员，拥有所有权限",
            priority=100
        ),
        Role.MANAGER: RolePermissions(
            role=Role.MANAGER,
            permissions={
                Permission.USER_READ,
                Permission.USER_CREATE,
                Permission.USER_UPDATE,
                Permission.DATA_READ,
                Permission.DATA_WRITE,
                Permission.DATA_DELETE,
                Permission.DATA_EXPORT,
                Permission.API_READ,
                Permission.API_WRITE,
                Permission.MONITOR_VIEW,
                Permission.MONITOR_DASHBOARD,
                Permission.RULES_READ,
                Permission.RULES_WRITE,
            },
            inherits=[Role.USER],
            description="经理，可以管理用户和数据",
            priority=80
        ),
        Role.DEVELOPER: RolePermissions(
            role=Role.DEVELOPER,
            permissions={
                Permission.USER_READ,
                Permission.DATA_READ,
                Permission.DATA_WRITE,
                Permission.API_READ,
                Permission.API_WRITE,
                Permission.API_DOCS,
                Permission.MONITOR_VIEW,
                Permission.RULES_READ,
            },
            inherits=[Role.USER],
            description="开发人员，可以访问API和监控",
            priority=60
        ),
        Role.OPERATOR: RolePermissions(
            role=Role.OPERATOR,
            permissions={
                Permission.USER_READ,
                Permission.DATA_READ,
                Permission.DATA_EXPORT,
                Permission.SYSTEM_LOG,
                Permission.SYSTEM_MONITOR,
                Permission.MONITOR_VIEW,
                Permission.MONITOR_ALERT,
                Permission.MONITOR_DASHBOARD,
            },
            inherits=[Role.USER],
            description="运维人员，可以查看监控和处理告警",
            priority=50
        ),
        Role.USER: RolePermissions(
            role=Role.USER,
            permissions={
                Permission.USER_READ,
                Permission.DATA_READ,
                Permission.DATA_WRITE,
                Permission.API_READ,
                Permission.MONITOR_VIEW,
            },
            inherits=[Role.VIEWER],
            description="普通用户，可以读写自己的数据",
            priority=30
        ),
        Role.VIEWER: RolePermissions(
            role=Role.VIEWER,
            permissions={
                Permission.DATA_READ,
                Permission.API_READ,
                Permission.API_DOCS,
                Permission.MONITOR_VIEW,
            },
            inherits=[Role.GUEST],
            description="查看者，只读访问",
            priority=10
        ),
        Role.GUEST: RolePermissions(
            role=Role.GUEST,
            permissions=set(),
            inherits=[],
            description="访客，最小权限",
            priority=0
        ),
    }
    
    def __init__(
        self,
        role_config: Dict[Role, RolePermissions] = None,
        enable_cache: bool = True
    ):
        """
        初始化RBAC服务
        
        Args:
            role_config: 自定义角色配置
            enable_cache: 是否启用权限缓存
        """
        self.role_config = role_config or self.DEFAULT_ROLE_CONFIG.copy()
        self.enable_cache = enable_cache
        self._permissions_cache: Dict[Role, Set[Permission]] = {}
    
    def get_role_permissions(self, role: Role) -> Set[Permission]:
        """
        获取角色权限（包含继承）
        
        Args:
            role: 角色
            
        Returns:
            Set[Permission]: 权限集合
        """
        if self.enable_cache and role in self._permissions_cache:
            return self._permissions_cache[role].copy()
        
        if role not in self.role_config:
            return set()
        
        permissions = set()
        role_perms = self.role_config[role]
        
        # 收集直接权限
        permissions.update(role_perms.permissions)
        
        # 收集继承权限
        for inherited_role in role_perms.inherits:
            permissions.update(self.get_role_permissions(inherited_role))
        
        # 缓存结果
        if self.enable_cache:
            self._permissions_cache[role] = permissions.copy()
        
        return permissions
    
    def has_permission(
        self,
        role: Role,
        permission: Permission
    ) -> bool:
        """
        检查角色是否有指定权限
        
        Args:
            role: 角色
            permission: 权限
            
        Returns:
            bool: 是否有权限
        """
        permissions = self.get_role_permissions(role)
        return permission in permissions
    
    def has_any_permission(
        self,
        role: Role,
        permissions: List[Permission]
    ) -> bool:
        """
        检查角色是否有任一指定权限
        
        Args:
            role: 角色
            permissions: 权限列表
            
        Returns:
            bool: 是否有任一权限
        """
        role_permissions = self.get_role_permissions(role)
        return any(p in role_permissions for p in permissions)
    
    def has_all_permissions(
        self,
        role: Role,
        permissions: List[Permission]
    ) -> bool:
        """
        检查角色是否有所有指定权限
        
        Args:
            role: 角色
            permissions: 权限列表
            
        Returns:
            bool: 是否有所有权限
        """
        role_permissions = self.get_role_permissions(role)
        return all(p in role_permissions for p in permissions)
    
    def get_user_permissions(
        self,
        user_roles: List[Role]
    ) -> Set[Permission]:
        """
        获取用户的聚合权限
        
        Args:
            user_roles: 用户角色列表
            
        Returns:
            Set[Permission]: 聚合后的权限集合
        """
        permissions = set()
        for role in user_roles:
            permissions.update(self.get_role_permissions(role))
        return permissions
    
    def can_access_resource(
        self,
        user_roles: List[Role],
        resource_owner: str,
        user_id: str,
        required_permission: Permission
    ) -> bool:
        """
        检查用户是否可以访问资源
        
        Args:
            user_roles: 用户角色列表
            resource_owner: 资源所有者ID
            user_id: 用户ID
            required_permission: 所需权限
            
        Returns:
            bool: 是否可以访问
        """
        # 管理员可以访问所有资源
        if Role.ADMIN in user_roles:
            return True
        
        # 资源所有者有所有权限
        if resource_owner == user_id:
            return True
        
        # 检查权限
        user_permissions = self.get_user_permissions(user_roles)
        return required_permission in user_permissions
    
    def get_role_hierarchy(self) -> Dict[Role, List[Role]]:
        """
        获取角色继承层次结构
        
        Returns:
            Dict[Role, List[Role]]: 角色继承关系
        """
        hierarchy = {}
        for role in Role:
            if role in self.role_config:
                hierarchy[role] = self.role_config[role].inherits.copy()
            else:
                hierarchy[role] = []
        return hierarchy
    
    def list_roles(self) -> List[Dict[str, Any]]:
        """
        列出所有角色及其权限
        
        Returns:
            List[Dict]: 角色信息列表
        """
        roles = []
        for role in Role:
            if role in self.role_config:
                config = self.role_config[role]
                roles.append({
                    "name": role.value,
                    "description": config.description,
                    "priority": config.priority,
                    "permissions": [p.value for p in config.permissions],
                    "inherits": [r.value for r in config.inherits],
                    "total_permissions": len(self.get_role_permissions(role))
                })
        return roles
    
    def validate_role(self, role: Role) -> tuple:
        """
        验证角色配置是否有效
        
        Returns:
            tuple: (是否有效, 错误消息列表)
        """
        errors = []
        
        if role not in self.role_config:
            errors.append(f"角色 {role.value} 未配置")
            return False, errors
        
        config = self.role_config[role]
        
        # 检查循环继承
        visited = set()
        stack = [role]
        while stack:
            current = stack.pop()
            if current in visited:
                errors.append(f"检测到循环继承: {role.value}")
                break
            visited.add(current)
            if current in self.role_config:
                for inherited in self.role_config[current].inherits:
                    if inherited not in visited:
                        stack.append(inherited)
        
        # 检查权限格式
        for perm in config.permissions:
            if not isinstance(perm, Permission):
                errors.append(f"无效的权限类型: {perm}")
        
        return len(errors) == 0, errors


class ResourceAccessControl:
    """
    资源访问控制类
    
    提供基于资源类型和操作的访问控制。
    """
    
    @dataclass
    class Resource:
        """资源数据类"""
        type: str
        id: str
        owner_id: str
        is_public: bool = False
        shared_with: List[str] = field(default_factory=list)
        metadata: Dict[str, Any] = field(default_factory=dict)
    
    @dataclass
    class AccessPolicy:
        """访问策略数据类"""
        resource_type: str
        action: str
        condition: str
        required_permission: Permission = None
        priority: int = 0
    
    # 默认访问策略
    DEFAULT_POLICIES: List[AccessPolicy] = [
        # 用户资源策略
        AccessPolicy(
            resource_type="user",
            action="read",
            condition="owner_or_admin_or_self",
            required_permission=Permission.USER_READ,
            priority=10
        ),
        AccessPolicy(
            resource_type="user",
            action="update",
            condition="owner_or_admin",
            required_permission=Permission.USER_UPDATE,
            priority=10
        ),
        # 数据资源策略
        AccessPolicy(
            resource_type="data",
            action="read",
            condition="public_or_owner_or_shared",
            required_permission=Permission.DATA_READ,
            priority=10
        ),
        AccessPolicy(
            resource_type="data",
            action="write",
            condition="owner_or_admin",
            required_permission=Permission.DATA_WRITE,
            priority=10
        ),
        AccessPolicy(
            resource_type="data",
            action="delete",
            condition="owner_or_admin",
            required_permission=Permission.DATA_DELETE,
            priority=10
        ),
        # API资源策略
        AccessPolicy(
            resource_type="api",
            action="*",
            condition="authenticated",
            required_permission=Permission.API_READ,
            priority=5
        ),
        # 监控资源策略
        AccessPolicy(
            resource_type="monitor",
            action="view",
            condition="authenticated",
            required_permission=Permission.MONITOR_VIEW,
            priority=5
        ),
    ]
    
    def __init__(
        self,
        rbac: RBAC = None,
        policies: List[AccessPolicy] = None
    ):
        """
        初始化资源访问控制
        
        Args:
            rbac: RBAC实例
            policies: 自定义访问策略
        """
        self.rbac = rbac or RBAC()
        self.policies = policies or self.DEFAULT_POLICIES.copy()
    
    def check_access(
        self,
        resource: Resource,
        action: str,
        user_id: str,
        user_roles: List[Role]
    ) -> tuple:
        """
        检查用户对资源的访问权限
        
        Args:
            resource: 资源
            action: 操作
            user_id: 用户ID
            user_roles: 用户角色列表
            
        Returns:
            tuple: (是否允许, 拒绝原因)
        """
        # 查找匹配的策略
        policy = self._find_policy(resource.type, action)
        if not policy:
            return False, f"未找到资源类型 '{resource.type}' 的访问策略"
        
        # 检查条件
        if not self._check_condition(
            policy.condition,
            resource,
            user_id,
            user_roles
        ):
            return False, f"访问条件不满足: {policy.condition}"
        
        # 检查权限
        if policy.required_permission:
            if not self.rbac.has_any_permission(
                user_roles[0] if user_roles else Role.GUEST,
                [policy.required_permission]
            ):
                return False, f"权限不足: 需要 {policy.required_permission.value}"
        
        return True, ""
    
    def _find_policy(
        self,
        resource_type: str,
        action: str
    ) -> Optional[AccessPolicy]:
        """查找匹配的访问策略"""
        # 首先尝试精确匹配
        for policy in self.policies:
            if policy.resource_type == resource_type and policy.action == action:
                return policy
        
        # 尝试通配符匹配
        for policy in self.policies:
            if policy.resource_type == resource_type and policy.action == "*":
                return policy
        
        return None
    
    def _check_condition(
        self,
        condition: str,
        resource: Resource,
        user_id: str,
        user_roles: List[Role]
    ) -> bool:
        """检查访问条件"""
        # 管理员有所有权限
        if Role.ADMIN in user_roles:
            return True
        
        conditions = {
            "public": resource.is_public,
            "authenticated": user_id is not None,
            "owner": resource.owner_id == user_id,
            "owner_or_admin": (
                resource.owner_id == user_id or 
                Role.ADMIN in user_roles
            ),
            "owner_or_self": (
                resource.owner_id == user_id or 
                resource.owner_id == ""
            ),
            "owner_or_admin_or_self": (
                resource.owner_id == user_id or 
                Role.ADMIN in user_roles or
                resource.owner_id == ""
            ),
            "public_or_owner_or_shared": (
                resource.is_public or
                resource.owner_id == user_id or
                user_id in resource.shared_with
            ),
        }
        
        return conditions.get(condition, False)


# 便捷函数
def create_rbac() -> RBAC:
    """创建RBAC服务实例"""
    return RBAC()


def create_resource_access_control() -> ResourceAccessControl:
    """创建资源访问控制实例"""
    return ResourceAccessControl()
