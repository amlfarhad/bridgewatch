from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from .config import Settings
from .models import IntegrationEvent, Severity, ValidationFinding


SUPPORTED_EVENTS = {
    "customer.updated",
    "order.created",
    "payment.authorized",
    "case.opened",
}

SUPPORTED_REGIONS = {"MEA", "NA", "EU", "APAC"}
VALID_ORDER_STATUSES = {"confirmed", "cancelled", "pending"}
VALID_PAYMENT_STATUSES = {"authorized", "captured", "failed"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}


def _finding(
    event: IntegrationEvent,
    check_name: str,
    severity: Severity,
    message: str,
    field_path: str,
    can_retry: bool,
) -> ValidationFinding:
    return ValidationFinding(
        event_id=event.event_id,
        check_name=check_name,
        severity=severity,
        message=message,
        field_path=field_path,
        can_retry=can_retry,
    )


def validate_event_shape(event: IntegrationEvent) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if event.event_type not in SUPPORTED_EVENTS:
        findings.append(
            _finding(event, "supported_event_type", Severity.HIGH, "Unsupported event type.", "event_type", False)
        )
    if not event.source_system:
        findings.append(
            _finding(event, "source_system_present", Severity.HIGH, "Source system is required.", "source_system", False)
        )
    if not isinstance(event.payload, dict) or not event.payload:
        findings.append(
            _finding(event, "payload_present", Severity.CRITICAL, "Payload must be a non-empty object.", "payload", False)
        )
    return findings


def validate_business_rules(event: IntegrationEvent) -> list[ValidationFinding]:
    payload = event.payload
    findings: list[ValidationFinding] = []
    if event.event_type == "customer.updated":
        if not payload.get("customer_id"):
            findings.append(_finding(event, "customer_id_present", Severity.CRITICAL, "Customer ID is required.", "payload.customer_id", False))
        if not payload.get("tier"):
            findings.append(_finding(event, "customer_tier_present", Severity.MEDIUM, "Customer tier is blank.", "payload.tier", True))
        if payload.get("home_region") not in SUPPORTED_REGIONS:
            findings.append(_finding(event, "supported_region", Severity.MEDIUM, "Unsupported customer region.", "payload.home_region", True))
    elif event.event_type == "order.created":
        if not payload.get("order_id"):
            findings.append(_finding(event, "order_id_present", Severity.CRITICAL, "Order ID is required.", "payload.order_id", False))
        if payload.get("status") not in VALID_ORDER_STATUSES:
            findings.append(_finding(event, "valid_order_status", Severity.HIGH, "Order status is invalid.", "payload.status", True))
        if float(payload.get("total_amount", 0)) <= 0:
            findings.append(_finding(event, "positive_order_amount", Severity.HIGH, "Order amount must be positive.", "payload.total_amount", True))
        if payload.get("region") not in SUPPORTED_REGIONS:
            findings.append(_finding(event, "supported_order_region", Severity.MEDIUM, "Unsupported order region.", "payload.region", True))
    elif event.event_type == "payment.authorized":
        if not payload.get("payment_id"):
            findings.append(_finding(event, "payment_id_present", Severity.CRITICAL, "Payment ID is required.", "payload.payment_id", False))
        if float(payload.get("amount", 0)) <= 0:
            findings.append(_finding(event, "positive_payment_amount", Severity.HIGH, "Payment amount must be positive.", "payload.amount", True))
        if payload.get("status") not in VALID_PAYMENT_STATUSES:
            findings.append(_finding(event, "valid_payment_status", Severity.HIGH, "Payment status is invalid.", "payload.status", True))
    elif event.event_type == "case.opened":
        if not payload.get("case_id"):
            findings.append(_finding(event, "case_id_present", Severity.CRITICAL, "Case ID is required.", "payload.case_id", False))
        if payload.get("priority") not in VALID_PRIORITIES:
            findings.append(_finding(event, "valid_case_priority", Severity.MEDIUM, "Case priority is invalid.", "payload.priority", True))
        if not payload.get("owner"):
            findings.append(_finding(event, "case_owner_present", Severity.HIGH, "Support case owner is missing.", "payload.owner", True))
    return findings


def validate_references(event: IntegrationEvent, all_events: Iterable[IntegrationEvent]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    order_ids = {
        item.payload.get("order_id")
        for item in all_events
        if item.event_type == "order.created"
    }
    customer_ids = {
        item.payload.get("customer_id")
        for item in all_events
        if item.event_type == "customer.updated"
    }
    if event.event_type == "payment.authorized" and event.payload.get("order_id") not in order_ids:
        findings.append(
            _finding(event, "payment_order_reference", Severity.HIGH, "Payment references an order that is not available.", "payload.order_id", True)
        )
    if event.event_type in {"order.created", "case.opened"} and event.payload.get("customer_id") not in customer_ids:
        findings.append(
            _finding(event, "customer_reference", Severity.HIGH, "Event references a customer that is not available.", "payload.customer_id", True)
        )
    return findings


def validate_freshness(event: IntegrationEvent, settings: Settings) -> list[ValidationFinding]:
    now = datetime.now(timezone.utc)
    occurred_at = event.occurred_at
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)
    age_minutes = (now - occurred_at).total_seconds() / 60
    if age_minutes > settings.stale_event_minutes:
        return [
            _finding(
                event,
                "event_freshness",
                Severity.MEDIUM,
                f"Event is {age_minutes:.0f} minutes old and may indicate upstream latency.",
                "occurred_at",
                True,
            )
        ]
    return []


def validate_event(
    event: IntegrationEvent,
    all_events: list[IntegrationEvent],
    settings: Settings,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    findings.extend(validate_event_shape(event))
    findings.extend(validate_business_rules(event))
    findings.extend(validate_references(event, all_events))
    findings.extend(validate_freshness(event, settings))
    return findings

