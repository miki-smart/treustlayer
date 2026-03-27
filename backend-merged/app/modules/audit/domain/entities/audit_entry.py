"""
AuditEntry — immutable audit log entry.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class AuditEntry:
    """
    Immutable audit log entry.
    
    Attributes:
        actor_id: User who performed the action (None for system actions)
        action: Action performed (e.g., "user.created", "kyc.approved")
        resource_type: Type of resource affected
        resource_id: ID of affected resource
        metadata: Additional context (IP, user agent, etc.)
        changes: Before/after values for updates
    """
    action: str
    resource_type: str
    actor_id: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    changes: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
