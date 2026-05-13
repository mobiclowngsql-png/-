"""
NetGuard Pro - Logging Configuration

Enterprise-grade structured logging with:
- JSON formatting for production
- Human-readable format for development
- Correlation IDs for request tracing
- Audit logging integration
- Log level management
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_output: str = "stdout",
    log_file_path: Optional[str] = None,
    include_timestamp: bool = True,
    include_caller: bool = True,
) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format (json or text)
        log_output: Output destination (stdout or file)
        log_file_path: Path to log file (if output is file)
        include_timestamp: Include timestamp in logs
        include_caller: Include caller information in logs
    """
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Build processors pipeline
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso" if include_timestamp else None),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]
    
    # Add caller info if requested
    if include_caller:
        processors.insert(
            1,
            structlog.stdlib.add_logger_name,
        )
        processors.insert(
            2,
            structlog.stdlib.add_caller,
        )
    
    # Configure formatter based on format type
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=processors[:-1],
        )
    else:
        # Human-readable format for development
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=processors[:-1],
        )
    
    # Configure handler
    if log_output == "file" and log_file_path:
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=100 * 1024 * 1024,  # 100 MB
            backupCount=5,
        )
    else:
        handler = logging.StreamHandler(sys.stdout)
    
    handler.setFormatter(formatter)
    
    # Get root logger and configure
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class AuditLogger:
    """
    Specialized logger for audit events.
    
    All audit events are logged with:
    - User identification
    - Action performed
    - Resource affected
    - Timestamp
    - Source IP
    - Result (success/failure)
    """
    
    def __init__(self):
        self.logger = structlog.get_logger("audit")
    
    def log(
        self,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        source_ip: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an audit event.
        
        Args:
            action: Action performed (e.g., "user_created", "policy_updated")
            user_id: ID of the user who performed the action
            username: Username of the user who performed the action
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            source_ip: Source IP address
            result: Result of the action (success/failure)
            details: Additional details as dictionary
        """
        log_entry = {
            "event": "audit",
            "action": action,
            "user_id": user_id,
            "username": username,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "source_ip": source_ip,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if details:
            log_entry["details"] = details
        
        if result == "success":
            self.logger.info("audit_event", **log_entry)
        else:
            self.logger.warning("audit_event", **log_entry)
    
    def login_success(
        self,
        user_id: int,
        username: str,
        source_ip: str,
        auth_method: str,
    ) -> None:
        """Log successful login."""
        self.log(
            action="login",
            user_id=user_id,
            username=username,
            source_ip=source_ip,
            result="success",
            details={"auth_method": auth_method},
        )
    
    def login_failure(
        self,
        username: str,
        source_ip: str,
        auth_method: str,
        reason: str,
    ) -> None:
        """Log failed login attempt."""
        self.log(
            action="login",
            username=username,
            source_ip=source_ip,
            result="failure",
            details={
                "auth_method": auth_method,
                "reason": reason,
            },
        )
    
    def resource_access(
        self,
        user_id: int,
        username: str,
        resource_type: str,
        resource_id: int,
        action: str,
        source_ip: str,
        result: str,
    ) -> None:
        """Log resource access attempt."""
        self.log(
            action=f"resource_{action}",
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            source_ip=source_ip,
            result=result,
        )
    
    def policy_change(
        self,
        user_id: int,
        username: str,
        policy_type: str,
        policy_id: int,
        change_type: str,
        source_ip: str,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
    ) -> None:
        """Log policy configuration change."""
        self.log(
            action=f"policy_{change_type}",
            user_id=user_id,
            username=username,
            resource_type="policy",
            resource_id=policy_id,
            source_ip=source_ip,
            result="success",
            details={
                "policy_type": policy_type,
                "old_value": str(old_value) if old_value is not None else None,
                "new_value": str(new_value) if new_value is not None else None,
            },
        )
    
    def security_event(
        self,
        event_type: str,
        severity: str,
        source_ip: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log security-related event."""
        self.log(
            action=f"security_{event_type}",
            user_id=user_id,
            username=username,
            source_ip=source_ip,
            result="alert" if severity in ["high", "critical"] else "info",
            details={
                "severity": severity,
                **(details or {}),
            },
        )


# Global audit logger instance
audit_logger = AuditLogger()


class RequestLoggingMiddleware:
    """
    ASGI middleware for request logging with correlation IDs.
    
    Adds:
    - Request ID for tracing
    - Request/response timing
    - Status code logging
    - Client IP logging
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate correlation ID
        import uuid
        correlation_id = str(uuid.uuid4())
        
        # Extract request info
        method = scope["method"]
        path = scope["path"]
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        
        logger = structlog.get_logger("requests")
        
        # Log request start
        logger.info(
            "request_started",
            correlation_id=correlation_id,
            method=method,
            path=path,
            client_ip=client_ip,
        )
        
        # Track timing
        import time
        start_time = time.time()
        
        # Wrap send to capture response status
        response_status = None
        
        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)
        
        try:
            # Add correlation ID to scope for use in handlers
            scope["correlation_id"] = correlation_id
            
            # Process request
            await self.app(scope, receive, send_wrapper)
            
            # Log completion
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "request_completed",
                correlation_id=correlation_id,
                method=method,
                path=path,
                client_ip=client_ip,
                status_code=response_status,
                duration_ms=round(duration_ms, 2),
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "request_failed",
                correlation_id=correlation_id,
                method=method,
                path=path,
                client_ip=client_ip,
                error=str(e),
                duration_ms=round(duration_ms, 2),
            )
            raise


# Initialize logging on module import (for development)
# In production, call setup_logging() explicitly with appropriate settings
if __name__ == "__main__":
    setup_logging(log_level="DEBUG", log_format="text")
    logger = structlog.get_logger()
    logger.info("Logging initialized", test=True)
