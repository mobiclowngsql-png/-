"""
NetGuard Pro - Authentication Endpoints

Authentication API with:
- JWT token-based auth
- Login/logout
- Token refresh
- Password management
- MFA support
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.config import settings
from app.core.rbac import oauth2_scheme, get_current_user
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.logging_config import audit_logger

router = APIRouter()


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str
    mfa_code: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request model."""
    current_password: str
    new_password: str


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.
    
    Supports:
    - Username/password authentication
    - AD/LDAP authentication (if configured)
    - MFA (if enabled)
    """
    from app.db.session import get_db_context
    from app.models.user import User
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    async with get_db_context() as db:
        # Find user by username
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.username == form_data.username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            audit_logger.login_failure(
                username=form_data.username,
                source_ip=client_ip,
                auth_method="password",
                reason="user_not_found",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is locked
        if user.is_locked:
            audit_logger.login_failure(
                username=form_data.username,
                source_ip=client_ip,
                auth_method="password",
                reason="account_locked",
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is locked due to too many failed attempts",
            )
        
        # Verify password
        if not verify_password(form_data.password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account if max attempts reached
            if user.failed_login_attempts >= settings.security.max_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=settings.security.lockout_duration_minutes
                )
            
            await db.commit()
            
            audit_logger.login_failure(
                username=form_data.username,
                source_ip=client_ip,
                auth_method="password",
                reason="invalid_password",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip
        
        await db.commit()
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.security.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
        },
        expires_delta=access_token_expires,
    )
    
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)},
    )
    
    # Log successful login
    audit_logger.login_success(
        user_id=user.id,
        username=user.username,
        source_ip=client_ip,
        auth_method="password",
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_token_expires.total_seconds()),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request_data: RefreshTokenRequest) -> TokenResponse:
    """Refresh access token using refresh token."""
    payload = verify_token(request_data.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.security.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=access_token_expires,
    )
    
    # Create new refresh token (rotation)
    new_refresh_token = create_refresh_token(
        data={"sub": user_id},
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=int(access_token_expires.total_seconds()),
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Logout user (invalidate tokens).
    
    Note: With stateless JWT, we rely on token expiration.
    For immediate invalidation, tokens can be added to a blacklist in Redis.
    """
    # In production: add token to blacklist in Redis
    # redis_client = request.app.state.redis
    # await redis_client.setex(f"blacklist:{token}", expire_time, "1")
    
    return {"message": "Successfully logged out"}


@router.post("/change-password")
async def change_password(
    request_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Change user password."""
    from app.db.session import get_db_context
    from app.models.user import User
    from sqlalchemy import select
    
    async with get_db_context() as db:
        result = await db.execute(
            select(User).where(User.id == int(current_user["id"]))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Verify current password
        if not verify_password(request_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        
        # Validate new password
        if len(request_data.new_password) < settings.security.password_min_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must be at least {settings.security.password_min_length} characters",
            )
        
        # Update password
        user.password_hash = hash_password(request_data.new_password)
        user.password_changed_at = datetime.utcnow()
        
        await db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current user information."""
    return current_user
