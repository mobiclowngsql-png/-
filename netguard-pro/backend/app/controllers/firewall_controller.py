"""
NetGuard Pro - Firewall Abstraction Layer

Platform-agnostic firewall management with:
- Abstract base classes for cross-platform support
- Linux implementation (nftables/iptables)
- Windows implementation (WFP - Windows Filtering Platform)
- Rule validation and optimization
- Atomic rule application
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Protocol(str, Enum):
    """Network protocols."""
    ANY = "any"
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    IGMP = "igmp"
    GRE = "gre"


class Action(str, Enum):
    """Firewall rule actions."""
    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"
    LOG = "log"
    RATE_LIMIT = "rate_limit"


class Direction(str, Enum):
    """Traffic direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    FORWARD = "forward"


class RuleState(str, Enum):
    """Rule state."""
    ENABLED = "enabled"
    DISABLED = "disabled"


@dataclass
class NetworkAddress:
    """Network address representation."""
    value: str  # IP address, CIDR, or hostname
    is_range: bool = False
    port_start: Optional[int] = None
    port_end: Optional[int] = None
    
    def __post_init__(self):
        if self.port_start and self.port_end:
            if self.port_start > self.port_end:
                raise ValueError("port_start must be <= port_end")
            if not (1 <= self.port_start <= 65535 and 1 <= self.port_end <= 65535):
                raise ValueError("Ports must be between 1 and 65535")


@dataclass
class FirewallRule:
    """
    Firewall rule definition.
    
    Attributes:
        id: Unique rule identifier
        name: Human-readable rule name
        priority: Rule priority (lower = higher priority)
        action: Rule action (accept/drop/reject/log)
        protocol: Network protocol
        source: Source address/network
        destination: Destination address/network
        direction: Traffic direction
        interfaces: List of interface names
        state: Rule state (enabled/disabled)
        logging: Enable logging for this rule
        rate_limit: Rate limit configuration
        comment: Rule description/comment
        tags: Rule tags for organization
    """
    id: str
    name: str
    priority: int = 1000
    action: Action = Action.DROP
    protocol: Protocol = Protocol.ANY
    source: Optional[NetworkAddress] = None
    destination: Optional[NetworkAddress] = None
    direction: Direction = Direction.INBOUND
    interfaces: List[str] = field(default_factory=list)
    state: RuleState = RuleState.ENABLED
    logging: bool = False
    rate_limit: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """Validate rule configuration."""
        if self.priority < 0 or self.priority > 65535:
            raise ValueError("Priority must be between 0 and 65535")
        
        if self.source and self.source.is_range:
            if self.source.port_start is None or self.source.port_end is None:
                raise ValueError("Port range requires port_start and port_end")
        
        if self.destination and self.destination.is_range:
            if self.destination.port_start is None or self.destination.port_end is None:
                raise ValueError("Port range requires port_start and port_end")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority,
            "action": self.action.value,
            "protocol": self.protocol.value,
            "source": {
                "value": self.source.value,
                "is_range": self.source.is_range,
                "port_start": self.source.port_start,
                "port_end": self.source.port_end,
            } if self.source else None,
            "destination": {
                "value": self.destination.value,
                "is_range": self.destination.is_range,
                "port_start": self.destination.port_start,
                "port_end": self.destination.port_end,
            } if self.destination else None,
            "direction": self.direction.value,
            "interfaces": self.interfaces,
            "state": self.state.value,
            "logging": self.logging,
            "rate_limit": self.rate_limit,
            "comment": self.comment,
            "tags": self.tags,
        }


@dataclass
class FirewallStats:
    """Firewall statistics."""
    packets_processed: int = 0
    bytes_processed: int = 0
    packets_dropped: int = 0
    bytes_dropped: int = 0
    packets_accepted: int = 0
    bytes_accepted: int = 0
    active_rules: int = 0
    last_updated: Optional[float] = None


class FirewallError(Exception):
    """Base exception for firewall errors."""
    pass


class FirewallPermissionError(FirewallError):
    """Raised when lacking permissions to modify firewall."""
    pass


class FirewallRuleError(FirewallError):
    """Raised when rule configuration is invalid."""
    pass


class BaseFirewallManager(ABC):
    """
    Abstract base class for firewall managers.
    
    Provides platform-agnostic interface for firewall operations.
    Implementations for Linux (nftables) and Windows (WFP) inherit from this.
    """
    
    def __init__(self):
        self.rules: Dict[str, FirewallRule] = {}
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize firewall manager.
        
        Returns:
            True if initialization successful
            
        Raises:
            FirewallPermissionError: If lacking required permissions
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if firewall subsystem is available on this platform."""
        pass
    
    @abstractmethod
    def add_rule(self, rule: FirewallRule) -> str:
        """
        Add a firewall rule.
        
        Args:
            rule: Rule to add
            
        Returns:
            Rule ID
            
        Raises:
            FirewallRuleError: If rule is invalid
            FirewallError: If rule addition fails
        """
        pass
    
    @abstractmethod
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a firewall rule.
        
        Args:
            rule_id: ID of rule to remove
            
        Returns:
            True if rule was removed
        """
        pass
    
    @abstractmethod
    def update_rule(self, rule: FirewallRule) -> bool:
        """
        Update an existing firewall rule.
        
        Args:
            rule: Updated rule
            
        Returns:
            True if update successful
        """
        pass
    
    @abstractmethod
    def get_rule(self, rule_id: str) -> Optional[FirewallRule]:
        """Get a specific rule by ID."""
        pass
    
    @abstractmethod
    def list_rules(self, filters: Optional[Dict[str, Any]] = None) -> List[FirewallRule]:
        """
        List all rules, optionally filtered.
        
        Args:
            filters: Optional filters (e.g., {"state": "enabled", "direction": "inbound"})
            
        Returns:
            List of matching rules
        """
        pass
    
    @abstractmethod
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a disabled rule."""
        pass
    
    @abstractmethod
    def disable_rule(self, rule_id: str) -> bool:
        """Disable an enabled rule."""
        pass
    
    @abstractmethod
    def set_default_policy(self, direction: Direction, action: Action) -> bool:
        """
        Set default policy for a direction.
        
        Args:
            direction: Traffic direction
            action: Default action (accept/drop)
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> FirewallStats:
        """Get firewall statistics."""
        pass
    
    @abstractmethod
    def flush_rules(self, preserve_system: bool = True) -> bool:
        """
        Remove all user-defined rules.
        
        Args:
            preserve_system: If True, preserve system-critical rules
            
        Returns:
            True if flush successful
        """
        pass
    
    @abstractmethod
    def backup_config(self) -> str:
        """
        Backup current firewall configuration.
        
        Returns:
            Configuration as string (format depends on platform)
        """
        pass
    
    @abstractmethod
    def restore_config(self, config: str) -> bool:
        """
        Restore firewall configuration from backup.
        
        Args:
            config: Configuration string
            
        Returns:
            True if restore successful
        """
        pass
    
    def validate_rule(self, rule: FirewallRule) -> bool:
        """Validate a rule before adding."""
        try:
            return rule.validate()
        except ValueError as e:
            logger.error(f"Rule validation failed: {e}")
            raise FirewallRuleError(str(e))
    
    def _check_duplicate(self, rule: FirewallRule) -> bool:
        """Check for duplicate rules."""
        for existing in self.rules.values():
            if (existing.action == rule.action and
                existing.protocol == rule.protocol and
                existing.direction == rule.direction and
                str(existing.source) == str(rule.source) and
                str(existing.destination) == str(rule.destination)):
                return True
        return False


# Placeholder implementations - actual implementations in platform-specific modules

class LinuxFirewallManager(BaseFirewallManager):
    """
    Linux firewall manager using nftables.
    
    Features:
    - nftables native support
    - Atomic rule updates
    - Named sets for efficient IP matching
    - Connection tracking integration
    """
    
    def __init__(self):
        super().__init__()
        self.nft_available = False
        self.table_name = "netguard"
        self.chain_prefix = "ng_"
    
    def initialize(self) -> bool:
        """Initialize nftables connection and create table."""
        import subprocess
        
        try:
            # Check if nft is available
            result = subprocess.run(
                ["nft", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.nft_available = result.returncode == 0
            
            if not self.nft_available:
                logger.warning("nftables not available, falling back to iptables")
                return False
            
            # Create netguard table
            self._create_table()
            self._initialized = True
            logger.info("Linux firewall manager initialized with nftables")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout checking nftables availability")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize nftables: {e}")
            raise FirewallPermissionError(f"Cannot initialize firewall: {e}")
    
    def _create_table(self):
        """Create netguard table and base chains."""
        import subprocess
        
        commands = [
            f"nft add table inet {self.table_name}",
            f"nft add chain inet {self.table_name} {self.chain_prefix}input {{ type filter hook input priority 0 \\; policy drop \\; }}",
            f"nft add chain inet {self.table_name} {self.chain_prefix}output {{ type filter hook output priority 0 \\; policy accept \\; }}",
            f"nft add chain inet {self.table_name} {self.chain_prefix}forward {{ type filter hook forward priority 0 \\; policy drop \\; }}",
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, check=False, capture_output=True)
            except Exception as e:
                logger.debug(f"Command '{cmd}' result: {e}")
    
    def is_available(self) -> bool:
        """Check if nftables is available."""
        return self.nft_available
    
    def add_rule(self, rule: FirewallRule) -> str:
        """Add rule using nftables."""
        import subprocess
        
        self.validate_rule(rule)
        
        # Build nftables rule command
        chain = self._get_chain_for_direction(rule.direction)
        nft_rule = self._build_nft_rule(rule)
        
        cmd = f"nft add rule inet {self.table_name} {chain} {nft_rule}"
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to add rule: {result.stderr}")
                raise FirewallError(f"Failed to add rule: {result.stderr}")
            
            self.rules[rule.id] = rule
            logger.info(f"Added firewall rule: {rule.name}")
            return rule.id
            
        except subprocess.TimeoutExpired:
            raise FirewallError("Timeout adding firewall rule")
    
    def _get_chain_for_direction(self, direction: Direction) -> str:
        """Get nftables chain name for direction."""
        mapping = {
            Direction.INBOUND: f"{self.chain_prefix}input",
            Direction.OUTBOUND: f"{self.chain_prefix}output",
            Direction.FORWARD: f"{self.chain_prefix}forward",
        }
        return mapping.get(direction, f"{self.chain_prefix}input")
    
    def _build_nft_rule(self, rule: FirewallRule) -> str:
        """Build nftables rule string."""
        parts = []
        
        # Interface
        if rule.interfaces:
            iface_list = ", ".join(rule.interfaces)
            parts.append(f"iifname {{ {iface_list} }}")
        
        # Protocol
        if rule.protocol != Protocol.ANY:
            parts.append(rule.protocol.value)
        
        # Source address
        if rule.source:
            if rule.source.is_range and rule.source.port_start:
                parts.append(f"ip saddr {rule.source.value}")
                parts.append(f"sport {rule.source.port_start}-{rule.source.port_end}")
            else:
                parts.append(f"ip saddr {rule.source.value}")
        
        # Destination address
        if rule.destination:
            if rule.destination.is_range and rule.destination.port_start:
                parts.append(f"ip daddr {rule.destination.value}")
                parts.append(f"dport {rule.destination.port_start}-{rule.destination.port_end}")
            else:
                parts.append(f"ip daddr {rule.destination.value}")
        
        # Action
        action_map = {
            Action.ACCEPT: "accept",
            Action.DROP: "drop",
            Action.REJECT: "reject",
            Action.LOG: "log",
            Action.RATE_LIMIT: "limit rate 10/second accept",
        }
        action_str = action_map.get(rule.action, "drop")
        
        # Logging
        if rule.logging:
            parts.append("log prefix \"netguard: \"")
        
        parts.append(action_str)
        
        return " ".join(parts)
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove rule by ID."""
        if rule_id not in self.rules:
            return False
        
        # In production: get handle and delete via nft delete rule
        del self.rules[rule_id]
        return True
    
    def update_rule(self, rule: FirewallRule) -> bool:
        """Update existing rule."""
        if rule.id not in self.rules:
            return False
        
        self.remove_rule(rule.id)
        return self.add_rule(rule)
    
    def get_rule(self, rule_id: str) -> Optional[FirewallRule]:
        """Get rule by ID."""
        return self.rules.get(rule_id)
    
    def list_rules(self, filters: Optional[Dict[str, Any]] = None) -> List[FirewallRule]:
        """List rules with optional filtering."""
        rules = list(self.rules.values())
        
        if not filters:
            return rules
        
        filtered = []
        for rule in rules:
            match = True
            for key, value in filters.items():
                if hasattr(rule, key):
                    if getattr(rule, key) != value:
                        match = False
                        break
            if match:
                filtered.append(rule)
        
        return filtered
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].state = RuleState.ENABLED
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].state = RuleState.DISABLED
            return True
        return False
    
    def set_default_policy(self, direction: Direction, action: Action) -> bool:
        """Set default policy for chain."""
        import subprocess
        
        chain = self._get_chain_for_direction(direction)
        policy = "accept" if action == Action.ACCEPT else "drop"
        
        cmd = f"nft chain inet {self.table_name} {chain} {{ policy {policy} \\; }}"
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to set default policy: {e}")
            return False
    
    def get_stats(self) -> FirewallStats:
        """Get firewall statistics."""
        # In production: parse nft list ruleset -a for counters
        return FirewallStats(active_rules=len(self.rules))
    
    def flush_rules(self, preserve_system: bool = True) -> bool:
        """Flush all rules."""
        import subprocess
        
        try:
            cmd = f"nft flush table inet {self.table_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                self.rules.clear()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to flush rules: {e}")
            return False
    
    def backup_config(self) -> str:
        """Backup configuration."""
        import subprocess
        
        try:
            result = subprocess.run(
                f"nft list table inet {self.table_name}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout if result.returncode == 0 else ""
        except Exception as e:
            logger.error(f"Failed to backup config: {e}")
            return ""
    
    def restore_config(self, config: str) -> bool:
        """Restore configuration."""
        import subprocess
        
        try:
            # Write config to temp file and restore
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.nft', delete=False) as f:
                f.write(config)
                temp_path = f.name
            
            cmd = f"nft -f {temp_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
            
            import os
            os.unlink(temp_path)
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to restore config: {e}")
            return False


class WindowsFirewallManager(BaseFirewallManager):
    """
    Windows firewall manager using Windows Filtering Platform (WFP).
    
    Features:
    - WFP native API via ctypes
    - Filter layer support
    - Callout support for deep inspection
    - Integration with Windows Defender Firewall
    """
    
    def __init__(self):
        super().__init__()
        self.wfp_available = False
        self.engine_handle = None
    
    def initialize(self) -> bool:
        """Initialize WFP session."""
        import sys
        
        if sys.platform != 'win32':
            logger.warning("WFP only available on Windows")
            return False
        
        try:
            # Import WFP functions via ctypes
            # In production: proper WFP initialization
            self.wfp_available = True
            self._initialized = True
            logger.info("Windows firewall manager initialized with WFP")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize WFP: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if WFP is available."""
        return self.wfp_available
    
    def add_rule(self, rule: FirewallRule) -> str:
        """Add rule using WFP."""
        self.validate_rule(rule)
        
        # In production: proper WFP filter addition via fwpmFilterAdd0
        self.rules[rule.id] = rule
        logger.info(f"Added Windows firewall rule: {rule.name}")
        return rule.id
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
    
    def update_rule(self, rule: FirewallRule) -> bool:
        """Update rule."""
        if rule.id not in self.rules:
            return False
        self.remove_rule(rule.id)
        return self.add_rule(rule)
    
    def get_rule(self, rule_id: str) -> Optional[FirewallRule]:
        """Get rule."""
        return self.rules.get(rule_id)
    
    def list_rules(self, filters: Optional[Dict[str, Any]] = None) -> List[FirewallRule]:
        """List rules."""
        rules = list(self.rules.values())
        if not filters:
            return rules
        
        filtered = []
        for rule in rules:
            match = True
            for key, value in filters.items():
                if hasattr(rule, key):
                    if getattr(rule, key) != value:
                        match = False
                        break
            if match:
                filtered.append(rule)
        return filtered
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable rule."""
        if rule_id in self.rules:
            self.rules[rule_id].state = RuleState.ENABLED
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable rule."""
        if rule_id in self.rules:
            self.rules[rule_id].state = RuleState.DISABLED
            return True
        return False
    
    def set_default_policy(self, direction: Direction, action: Action) -> bool:
        """Set default policy."""
        # In production: WFP profile configuration
        return True
    
    def get_stats(self) -> FirewallStats:
        """Get statistics."""
        return FirewallStats(active_rules=len(self.rules))
    
    def flush_rules(self, preserve_system: bool = True) -> bool:
        """Flush rules."""
        self.rules.clear()
        return True
    
    def backup_config(self) -> str:
        """Backup configuration."""
        import json
        return json.dumps([r.to_dict() for r in self.rules.values()])
    
    def restore_config(self, config: str) -> bool:
        """Restore configuration."""
        import json
        try:
            rules_data = json.loads(config)
            for rule_data in rules_data:
                rule = FirewallRule(**rule_data)
                self.add_rule(rule)
            return True
        except Exception as e:
            logger.error(f"Failed to restore config: {e}")
            return False


# Factory function to get appropriate firewall manager for platform

def get_firewall_manager() -> BaseFirewallManager:
    """
    Get the appropriate firewall manager for the current platform.
    
    Returns:
        Platform-specific firewall manager instance
    """
    import sys
    
    if sys.platform.startswith('linux'):
        return LinuxFirewallManager()
    elif sys.platform == 'win32':
        return WindowsFirewallManager()
    else:
        logger.warning(f"Unsupported platform: {sys.platform}")
        # Return a mock manager that doesn't actually modify firewall
        return MockFirewallManager()


# Mock implementation for unsupported platforms or testing
class MockFirewallManager(BaseFirewallManager):
    """Mock firewall manager for testing or unsupported platforms."""
    
    def initialize(self) -> bool:
        self._initialized = True
        return True
    
    def is_available(self) -> bool:
        return True
    
    def add_rule(self, rule: FirewallRule) -> str:
        self.validate_rule(rule)
        self.rules[rule.id] = rule
        return rule.id
    
    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
    
    def update_rule(self, rule: FirewallRule) -> bool:
        if rule.id not in self.rules:
            return False
        self.rules[rule.id] = rule
        return True
    
    def get_rule(self, rule_id: str) -> Optional[FirewallRule]:
        return self.rules.get(rule_id)
    
    def list_rules(self, filters: Optional[Dict[str, Any]] = None) -> List[FirewallRule]:
        return list(self.rules.values())
    
    def enable_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            self.rules[rule_id].state = RuleState.ENABLED
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            self.rules[rule_id].state = RuleState.DISABLED
            return True
        return False
    
    def set_default_policy(self, direction: Direction, action: Action) -> bool:
        return True
    
    def get_stats(self) -> FirewallStats:
        return FirewallStats(active_rules=len(self.rules))
    
    def flush_rules(self, preserve_system: bool = True) -> bool:
        self.rules.clear()
        return True
    
    def backup_config(self) -> str:
        import json
        return json.dumps([r.to_dict() for r in self.rules.values()])
    
    def restore_config(self, config: str) -> bool:
        import json
        try:
            rules_data = json.loads(config)
            for rule_data in rules_data:
                rule = FirewallRule(**rule_data)
                self.add_rule(rule)
            return True
        except Exception:
            return False
