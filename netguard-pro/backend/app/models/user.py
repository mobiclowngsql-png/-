"""
NetGuard Pro - User Model

User account model with:
- Full user profile
- Authentication data
- Group membership
- Billing account linkage
- Audit tracking
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.account import Account


class User(Base):
    """
    User account model.
    
    Stores all user-related information including:
    - Authentication credentials (hashed)
    - Profile information
    - Account status
    - Group memberships
    - Last login tracking
    """
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Authentication
    username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique username for authentication"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True,
        comment="User email address"
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Hashed password (bcrypt/argon2)"
    )
    
    # Profile
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Full name of the user"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Phone number"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User description/notes"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Is user account active"
    )
    is_disabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is user account disabled by admin"
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Is user blocked (e.g., low balance)"
    )
    
    # Role (RBAC)
    role: Mapped[str] = mapped_column(
        String(50),
        default="user",
        nullable=False,
        comment="User role for RBAC"
    )
    
    # Authentication tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login timestamp"
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="IP address of last login"
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Count of consecutive failed login attempts"
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Account lockout expiration time"
    )
    
    # Password management
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last password change timestamp"
    )
    password_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Password expiration timestamp"
    )
    
    # External identity
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="External ID (AD, LDAP, ESIA)"
    )
    external_source: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="External source type (ad, ldap, esia, radius)"
    )
    
    # Network binding
    allowed_ips: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated list of allowed IP addresses/CIDRs"
    )
    allowed_macs: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated list of allowed MAC addresses"
    )
    vlan_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="VLAN ID for user traffic"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record update timestamp"
    )
    
    # Relationships
    groups: Mapped[List["Group"]] = relationship(
        secondary="user_groups",
        back_populates="users",
        lazy="selectin",
        comment="Groups this user belongs to"
    )
    
    account: Mapped[Optional["Account"]] = relationship(
        back_populates="user",
        uselist=False,
        lazy="selectin",
        comment="Billing account linked to user"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until.replace(tzinfo=None)
    
    @property
    def display_name(self) -> str:
        """Get user display name."""
        return self.full_name or self.username
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary."""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "description": self.description,
            "is_active": self.is_active,
            "is_disabled": self.is_disabled,
            "is_blocked": self.is_blocked,
            "role": self.role,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "last_login_ip": self.last_login_ip,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "external_source": self.external_source,
            "vlan_id": self.vlan_id,
            "display_name": self.display_name,
            "is_locked": self.is_locked,
        }
        
        if include_sensitive:
            data.update({
                "allowed_ips": self.allowed_ips,
                "allowed_macs": self.allowed_macs,
                "failed_login_attempts": self.failed_login_attempts,
                "locked_until": self.locked_until.isoformat() if self.locked_until else None,
            })
        
        return data
