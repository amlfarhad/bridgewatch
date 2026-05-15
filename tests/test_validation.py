from __future__ import annotations

from datetime import datetime, timezone

from bridgewatch.config import Settings
from bridgewatch.models import IntegrationEvent
from bridgewatch.validation import validate_event


def settings(tmp_path):
    return Settings(database_path=tmp_path / "test.db", api_key="test-key", stale_event_minutes=45)


def test_payment_references_missing_order(tmp_path):
    event = IntegrationEvent(
        event_id="pay-test",
        source_system="payments",
        event_type="payment.authorized",
        occurred_at=datetime.now(timezone.utc),
        payload={"payment_id": "P-1", "order_id": "O-missing", "amount": 50, "status": "authorized"},
    )

    findings = validate_event(event, [event], settings(tmp_path))

    assert any(item.check_name == "payment_order_reference" for item in findings)
    assert any(item.can_retry for item in findings)


def test_clean_customer_event_passes(tmp_path):
    event = IntegrationEvent(
        event_id="cust-test",
        source_system="customer-profile",
        event_type="customer.updated",
        occurred_at=datetime.now(timezone.utc),
        payload={"customer_id": "C-1", "tier": "gold", "home_region": "MEA", "email_verified": True},
    )

    assert validate_event(event, [event], settings(tmp_path)) == []

