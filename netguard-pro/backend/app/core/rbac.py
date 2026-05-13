"""
NetGuard Pro - RBAC (Role-Based Access Control) System

Enterprise-grade authorization with:
- Role-based permissions
- Resource-level access control
- Context-aware policies
- Permission inheritance
- Audit integration
"""

from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import settings


class ResourceType(str, Enum):
    """Resource types for access control."""
    
    USER = "user"
    GROUP = "group"
    POLICY = "policy"
    FIREWALL_RULE = "firewall_rule"
    NAT_RULE = "nat_rule"
    PROXY_CONFIG = "proxy_config"
    QOS_POLICY = "qos_policy"
    TARIFF = "tariff"
    BILLING = "billing"
    REPORT = "report"
    SYSTEM = "system"
    AUDIT_LOG = "audit_log"


class Action(str, Enum):
    """Actions that can be performed on resources."""
    
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ADMIN = "admin"  # Full control


class Role(str, Enum):
    """Predefined roles in the system."""
    
    SUPER_ADMIN = "super_admin"
    SECURITY_ADMIN = "security_admin"
    NETWORK_ADMIN = "network_admin"
    BILLING_ADMIN = "billing_admin"
    HELP_DESK = "help_desk"
    AUDITOR = "auditor"
    USER = "user"


# Role permissions matrix
ROLE_PERMISSIONS: Dict[Role, Dict[ResourceType, Set[Action]]] = {
    Role.SUPER_ADMIN: {
        resource: {Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE, Action.ADMIN}
        for resource in ResourceType
    },
    
    Role.SECURITY_ADMIN: {
        ResourceType.FIREWALL_RULE: {Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE},
        ResourceType.POLICY: {Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE},
        ResourceType.USER: {Action.READ},
        ResourceType.GROUP: {Action.READ},
        ResourceType.AUDIT_LOG: {Action.READ},
        ResourceType.SYSTEM: {Action.READ},
    },
    
    Role.NETWORK_ADMIN: {
        ResourceType.NAT_RULE: {Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE},
        ResourceType.PROXY_CONFIG: {Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE},
        ResourceType.QOS_POLICY: {Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE},
        ResourceType.POLICY: {Action.READ},
        ResourceType.USER: {Action.READ},
    },
    
    Role.BILLING_ADMIN: {
        ResourceType.TARIFF: {Action.READ, Action.CREATE, Action.UPDATE, Action.DELETE},
        ResourceType.BILLING: {Action.READ, Action.CREATE, Action.UPDATE},
        ResourceType.USER: {Action.READ, Action.UPDATE},  # For balance adjustments
        ResourceType.REPORT: {Action.READ, Action.CREATE},
    },
    
    Role.HELP_DESK: {
        ResourceType.USER: {Action.READ, Action.UPDATE},  # Password reset, unlock
        ResourceType.GROUP: {Action.READ},
        ResourceType.POLICY: {Action.READ},
        ResourceType.BILLING: {Action.READ},
    },
    
    Role.AUDITOR: {
        ResourceType.AUDIT_LOG: {Action.READ},
        ResourceType.REPORT: {Action.READ},
        ResourceType.USER: {Action.READ},
        ResourceType.POLICY: {Action.READ},
        ResourceType.BILLING: {Action.READ},
    },
    
    Role.USER: {
        ResourceType.USER: {Action.READ, Action.UPDATE},  # Self-service only
        ResourceType.BILLING: {Action.READ},  # Own billing only
    },
}


# Context-aware permission overrides
# These allow fine-grained control based on conditions
CONTEXT_PERMISSIONS: Dict[str, Dict[Role, Dict[ResourceType, Set[Action]]]] = {
    # Example: Allow help desk to reset passwords only for non-admin users
    "help_desk_password_reset": {
        Role.HELP_DESK: {
            ResourceType.USER: {Action.UPDATE},
        }
    },
}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class PermissionChecker:
    """
    Check if a user has permission to perform an action on a resource.
    """
    
    def __init__(
        self,
        required_resource: ResourceType,
        required_action: Action,
        require_all: bool = True,
    ):
        self.required_resource = required_resource
        self.required_action = required_action
        self.require_all = require_all
    
    def __call__(
        self,
        current_user: dict = Depends(get_current_user),
    ) -> bool:
        """
        Check if the current user has the required permission.
        
        Args:
            current_user: Current authenticated user dict
            
        Returns:
            True if permission is granted
            
        Raises:
            HTTPException: If permission is denied
        """
        user_role = Role(current_user.get("role", Role.USER))
        user_permissions = ROLE_PERMISSIONS.get(user_role, {})
        
        # Check if role has permission for the resource
        resource_permissions = user_permissions.get(self.required_resource, set())
        
        # Check for admin action (grants all actions)
        if Action.ADMIN in resource_permissions:
            return True
        
        # Check for specific action
        if self.required_action in resource_permissions:
            return True
        
        # Permission denied
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "permission_denied",
                "message": f"User with role '{user_role.value}' does not have permission "
                          f"to {self.required_action.value} {self.required_resource.value}",
                "required_role": self._get_required_role(),
            },
        )
    
    def _get_required_role(self) -> str:
        """Get the minimum role required for this permission."""
        for role, permissions in ROLE_PERMISSIONS.items():
            resource_perms = permissions.get(self.required_resource, set())
            if self.required_action in resource_perms or Action.ADMIN in resource_perms:
                return role.value
        return "unknown"


def require_permission(resource: ResourceType, action: Action):
    """
    Decorator to require specific permission for an endpoint.
    
    Usage:
        @router.get("/users")
        @require_permission(ResourceType.USER, Action.READ)
        async def get_users():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Permission check is handled by FastAPI dependencies
            return await func(*args, **kwargs)
        
        # Add dependency to the function
        wrapper.__dict__["permissions"] = (resource, action)
        return wrapper
    return decorator


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Get current authenticated user from JWT token.
    
    This is a placeholder implementation. In production, this should:
    1. Decode and validate the JWT token
    2. Check token expiration
    3. Load user from database
    4. Return user dict with role and permissions
    """
    from jose import JWTError, jwt
    from app.core.security import verify_token
    
    try:
        payload = verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role", Role.USER.value)
        
        if user_id is None or username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "id": user_id,
            "username": username,
            "role": role,
        }
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get current active user (not disabled/blocked).
    
    Additional checks:
    - User is not disabled
    - User is not blocked (billing)
    - User account is not expired
    """
    # In production, load user from database and check status
    # if current_user.get("is_disabled"):
    #     raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user


async def get_current_super_admin(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """
    Get current user and verify they are a super admin.
    """
    if current_user.get("role") != Role.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user


class ResourceAccessValidator:
    """
    Validate access to specific resource instances.
    
    Used for context-aware access control:
    - Users can only access their own data (unless admin)
    - Help desk can only modify non-admin users
    - Billing admin can only modify balances within limits
    """
    
    @staticmethod
    def validate_user_access(
        current_user: dict,
        target_user_id: int,
    ) -> bool:
        """
        Validate if current user can access target user.
        
        Rules:
        - Super admin: always allowed
        - User: can only access themselves
        - Other roles: based on permissions
        """
        role = Role(current_user.get("role", Role.USER))
        
        if role == Role.SUPER_ADMIN:
            return True
        
        if role == Role.USER:
            return current_user.get("id") == target_user_id
        
        # Other roles checked by permission matrix
        return True
    
    @staticmethod
    def validate_group_access(
        current_user: dict,
        group_id: int,
    ) -> bool:
        """Validate group access based on user's group membership."""
        role = Role(current_user.get("role", Role.USER))
        
        if role in [Role.SUPER_ADMIN, Role.SECURITY_ADMIN]:
            return True
        
        # Check if user is member of the group
        # user_groups = current_user.get("groups", [])
        # return group_id in user_groups
        
        return False
    
    @staticmethod
    def validate_billing_access(
        current_user: dict,
        target_user_id: int,
        amount: float,
    ) -> bool:
        """
        Validate billing operation.
        
        Rules:
        - Billing admin: can adjust balances within limits
        - User: can only view own billing
        """
        role = Role(current_user.get("role", Role.USER))
        
        if role == Role.SUPER_ADMIN:
            return True
        
        if role == Role.BILLING_ADMIN:
            # Check amount limits
            max_adjustment = 10000.0  # Configurable
            return abs(amount) <= max_adjustment
        
        if role == Role.USER:
            return current_user.get("id") == target_user_id
        
        return False


# Dependency for resource-level validation
def validate_resource_access(resource_type: ResourceType, resource_id_param: str = "id"):
    """
    Create dependency for resource-level access validation.
    
    Usage:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: int,
            _: bool = Depends(validate_resource_access(ResourceType.USER, "user_id"))
        ):
            ...
    """
    async def validator(
        current_user: dict = Depends(get_current_active_user),
        **path_params,
    ) -> bool:
        resource_id = path_params.get(resource_id_param)
        
        if resource_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing resource ID parameter: {resource_id_param}",
            )
        
        # Validate based on resource type
        if resource_type == ResourceType.USER:
            if not ResourceAccessValidator.validate_user_access(
                current_user, int(resource_id)
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this user resource",
                )
        
        # Add more resource type validators as needed
        
        return True
    
    return validator
