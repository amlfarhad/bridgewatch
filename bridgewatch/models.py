from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventStatus(str, Enum):
    RECEIVED = "received"
    VALIDATED = "validated"
    FAILED = "failed"
    ROUTED = "routed"
    BLOCKED = "blocked"


class RetryStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class IntegrationEvent:
    event_id: str
    source_system: str
    event_type: str
    occurred_at: datetime
    payload: dict[str, Any]


@dataclass(frozen=True)
class ValidationFinding:
    event_id: str
    check_name: str
    severity: Severity
    message: str
    field_path: str
    can_retry: bool


@dataclass(frozen=True)
class IntegrationRunResult:
    run_id: str
    processed: int
    passed: int
    failed: int
    queued_for_retry: int
    incidents_created: int
    findings: list[ValidationFinding]
