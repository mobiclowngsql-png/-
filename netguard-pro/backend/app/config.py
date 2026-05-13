"""
NetGuard Pro - Configuration Management

Enterprise-grade configuration system with support for:
- Environment variables
- Configuration files (YAML/JSON)
- Secrets management
- Platform-specific settings
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    name: str = Field(default="netguard", description="Database name")
    user: str = Field(default="netguard", description="Database user")
    password: str = Field(default="", description="Database password")
    pool_size: int = Field(default=20, ge=5, le=100, description="Connection pool size")
    pool_timeout: int = Field(default=30, ge=10, le=300, description="Pool timeout in seconds")
    echo: bool = Field(default=False, description="Echo SQL queries (debug)")
    
    @property
    def async_url(self) -> str:
        """Get async database URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def sync_url(self) -> str:
        """Get sync database URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    model_config = SettingsConfigDict(env_prefix="DB_")


class RedisSettings(BaseSettings):
    """Redis configuration."""
    
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    max_connections: int = Field(default=50, ge=10, le=200, description="Max connections")
    
    @property
    def url(self) -> str:
        """Get Redis URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    model_config = SettingsConfigDict(env_prefix="REDIS_")


class SecuritySettings(BaseSettings):
    """Security configuration."""
    
    secret_key: str = Field(
        default="",
        description="Secret key for JWT signing (must be set in production)"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiration in days"
    )
    password_min_length: int = Field(default=8, ge=8, le=128, description="Minimum password length")
    password_require_uppercase: bool = Field(default=True, description="Require uppercase letters")
    password_require_lowercase: bool = Field(default=True, description="Require lowercase letters")
    password_require_digits: bool = Field(default=True, description="Require digits")
    password_require_special: bool = Field(default=True, description="Require special characters")
    max_login_attempts: int = Field(default=5, ge=3, le=10, description="Max login attempts before lockout")
    lockout_duration_minutes: int = Field(default=15, ge=5, le=60, description="Lockout duration")
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    model_config = SettingsConfigDict(env_prefix="SECURITY_")


class FirewallSettings(BaseSettings):
    """Firewall configuration."""
    
    enabled: bool = Field(default=True, description="Enable firewall")
    default_policy: str = Field(default="DROP", description="Default policy (DROP/ACCEPT)")
    log_dropped: bool = Field(default=True, description="Log dropped packets")
    log_level: str = Field(default="info", description="Logging level")
    max_rules: int = Field(default=10000, ge=100, le=100000, description="Maximum rules count")
    rule_evaluation_timeout_ms: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Rule evaluation timeout"
    )
    
    model_config = SettingsConfigDict(env_prefix="FIREWALL_")


class ProxySettings(BaseSettings):
    """Proxy server configuration."""
    
    http_enabled: bool = Field(default=True, description="Enable HTTP proxy")
    https_enabled: bool = Field(default=True, description="Enable HTTPS proxy")
    socks_enabled: bool = Field(default=False, description="Enable SOCKS proxy")
    http_port: int = Field(default=3128, ge=1, le=65535, description="HTTP proxy port")
    https_port: int = Field(default=3129, ge=1, le=65535, description="HTTPS proxy port")
    socks_port: int = Field(default=1080, ge=1, le=65535, description="SOCKS proxy port")
    transparent_mode: bool = Field(default=False, description="Transparent proxy mode")
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_size_mb: int = Field(default=1024, ge=128, le=65536, description="Cache size in MB")
    ssl_inspection_enabled: bool = Field(default=False, description="Enable SSL inspection")
    ssl_ca_cert_path: Optional[str] = Field(default=None, description="SSL CA certificate path")
    ssl_ca_key_path: Optional[str] = Field(default=None, description="SSL CA private key path")
    
    model_config = SettingsConfigDict(env_prefix="PROXY_")


class BillingSettings(BaseSettings):
    """Billing system configuration."""
    
    enabled: bool = Field(default=True, description="Enable billing")
    currency: str = Field(default="RUB", description="Currency code")
    low_balance_threshold: float = Field(default=50.0, ge=0, description="Low balance threshold")
    auto_block_on_low_balance: bool = Field(
        default=True,
        description="Auto-block users on low balance"
    )
    grace_period_hours: int = Field(
        default=24,
        ge=0,
        le=168,
        description="Grace period before blocking"
    )
    accounting_interval_seconds: int = Field(
        default=60,
        ge=10,
        le=3600,
        description="Accounting interval"
    )
    
    model_config = SettingsConfigDict(env_prefix="BILLING_")


class IntegrationSettings(BaseSettings):
    """External integrations configuration."""
    
    # Active Directory
    ad_enabled: bool = Field(default=False, description="Enable AD integration")
    ad_domain: Optional[str] = Field(default=None, description="AD domain")
    ad_server: Optional[str] = Field(default=None, description="AD server")
    ad_bind_dn: Optional[str] = Field(default=None, description="AD bind DN")
    ad_bind_password: Optional[str] = Field(default=None, description="AD bind password")
    
    # RADIUS
    radius_enabled: bool = Field(default=False, description="Enable RADIUS")
    radius_server: Optional[str] = Field(default=None, description="RADIUS server")
    radius_port: int = Field(default=1812, ge=1, le=65535, description="RADIUS port")
    radius_secret: Optional[str] = Field(default=None, description="RADIUS secret")
    
    # ЕСИА (Gosuslugi)
    esia_enabled: bool = Field(default=False, description="Enable ESIA OAuth")
    esia_client_id: Optional[str] = Field(default=None, description="ESIA client ID")
    esia_client_secret: Optional[str] = Field(default=None, description="ESIA client secret")
    esia_redirect_uri: Optional[str] = Field(default=None, description="ESIA redirect URI")
    
    # Antivirus (ICAP)
    icap_enabled: bool = Field(default=False, description="Enable ICAP antivirus")
    icap_server: Optional[str] = Field(default=None, description="ICAP server URL")
    
    # Suricata IDS/IPS
    suricata_enabled: bool = Field(default=False, description="Enable Suricata")
    suricata_socket: Optional[str] = Field(default=None, description="Suricata socket path")
    
    model_config = SettingsConfigDict(env_prefix="INTEGRATION_")


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="json",
        description="Log format (json/text)"
    )
    output: str = Field(default="stdout", description="Log output (stdout/file)")
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_file_size_mb: int = Field(default=100, ge=10, le=1024, description="Max log file size")
    backup_count: int = Field(default=5, ge=1, le=30, description="Backup log files count")
    include_timestamp: bool = Field(default=True, description="Include timestamp")
    include_caller: bool = Field(default=True, description="Include caller info")
    
    model_config = SettingsConfigDict(env_prefix="LOG_")


class ServerSettings(BaseSettings):
    """Server configuration."""
    
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=4, ge=1, le=32, description="Number of worker processes")
    reload: bool = Field(default=False, description="Auto-reload on changes (dev)")
    debug: bool = Field(default=False, description="Debug mode")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="CORS allowed origins"
    )
    rate_limit_per_minute: int = Field(default=100, ge=10, le=1000, description="Rate limit")
    
    model_config = SettingsConfigDict(env_prefix="SERVER_")


class Settings(BaseSettings):
    """Main application settings."""
    
    app_name: str = Field(default="NetGuard Pro", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development/production)")
    
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    firewall: FirewallSettings = Field(default_factory=FirewallSettings)
    proxy: ProxySettings = Field(default_factory=ProxySettings)
    billing: BillingSettings = Field(default_factory=BillingSettings)
    integration: IntegrationSettings = Field(default_factory=IntegrationSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
