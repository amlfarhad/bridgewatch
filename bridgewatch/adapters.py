from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import IntegrationEvent


def _now_minus(minutes: int) -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=minutes)


def sample_order_events() -> list[IntegrationEvent]:
    return [
        IntegrationEvent(
            event_id="ord-1001",
            source_system="order-management",
            event_type="order.created",
            occurred_at=_now_minus(7),
            payload={
                "order_id": "O-1001",
                "customer_id": "C-771",
                "region": "MEA",
                "status": "confirmed",
                "total_amount": 482.20,
            },
        ),
        IntegrationEvent(
            event_id="ord-1002",
            source_system="order-management",
            event_type="order.created",
            occurred_at=_now_minus(90),
            payload={
                "order_id": "O-1002",
                "customer_id": "C-002",
                "region": "NA",
                "status": "confirmed",
                "total_amount": 0,
            },
        ),
    ]


def sample_payment_events() -> list[IntegrationEvent]:
    return [
        IntegrationEvent(
            event_id="pay-7781",
            source_system="payments",
            event_type="payment.authorized",
            occurred_at=_now_minus(6),
            payload={
                "payment_id": "P-7781",
                "order_id": "O-1001",
                "amount": 482.20,
                "currency": "AED",
                "status": "authorized",
            },
        ),
        IntegrationEvent(
            event_id="pay-7782",
            source_system="payments",
            event_type="payment.authorized",
            occurred_at=_now_minus(3),
            payload={
                "payment_id": "P-7782",
                "order_id": "O-missing",
                "amount": 218.10,
                "currency": "AED",
                "status": "authorized",
            },
        ),
    ]


def sample_customer_events() -> list[IntegrationEvent]:
    return [
        IntegrationEvent(
            event_id="cust-771",
            source_system="customer-profile",
            event_type="customer.updated",
            occurred_at=_now_minus(5),
            payload={
                "customer_id": "C-771",
                "tier": "gold",
                "home_region": "MEA",
                "email_verified": True,
            },
        ),
        IntegrationEvent(
            event_id="cust-002",
            source_system="customer-profile",
            event_type="customer.updated",
            occurred_at=_now_minus(5),
            payload={
                "customer_id": "C-002",
                "tier": "",
                "home_region": "NA",
                "email_verified": False,
            },
        ),
    ]


def sample_support_events() -> list[IntegrationEvent]:
    return [
        IntegrationEvent(
            event_id="case-2001",
            source_system="support",
            event_type="case.opened",
            occurred_at=_now_minus(2),
            payload={
                "case_id": "S-2001",
                "customer_id": "C-771",
                "priority": "medium",
                "owner": "service-ops",
            },
        ),
        IntegrationEvent(
            event_id="case-2002",
            source_system="support",
            event_type="case.opened",
            occurred_at=_now_minus(1),
            payload={
                "case_id": "S-2002",
                "customer_id": "C-404",
                "priority": "critical",
                "owner": "",
            },
        ),
    ]


def sample_event_batch() -> list[IntegrationEvent]:
    events: list[IntegrationEvent] = []
    for factory in [sample_customer_events, sample_order_events, sample_payment_events, sample_support_events]:
        events.extend(factory())
    return events

