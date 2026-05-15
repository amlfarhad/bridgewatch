from __future__ import annotations

from bridgewatch.adapters import sample_event_batch
from bridgewatch.config import Settings
from bridgewatch.db import insert_events, reset, session
from bridgewatch.pipeline import run_integrations
from bridgewatch.retry import process_retry_queue


def test_retry_processing_returns_events_for_revalidation(tmp_path):
    settings = Settings(
        database_path=tmp_path / "retry.db",
        api_key="test-key",
        base_retry_seconds=-1,
        max_retry_attempts=3,
    )
    reset(settings)
    insert_events(sample_event_batch(), settings)
    run_integrations(settings)

    with session(settings) as conn:
        result = process_retry_queue(conn, settings)
        received = conn.execute("SELECT COUNT(*) AS count FROM events WHERE status = 'received'").fetchone()["count"]

    assert result["processed"] > 0
    assert result["resolved"] > 0
    assert received > 0

