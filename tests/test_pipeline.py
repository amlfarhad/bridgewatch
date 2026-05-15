from __future__ import annotations

from bridgewatch.adapters import sample_event_batch
from bridgewatch.config import Settings
from bridgewatch.db import insert_events, reset, row_count, session
from bridgewatch.pipeline import run_integrations


def test_run_integrations_creates_findings_retries_and_incidents(tmp_path):
    settings = Settings(database_path=tmp_path / "pipeline.db", api_key="test-key", base_retry_seconds=0)
    reset(settings)
    insert_events(sample_event_batch(), settings)

    result = run_integrations(settings)

    assert result.processed == 8
    assert result.failed > 0
    assert result.queued_for_retry > 0
    with session(settings) as conn:
        assert row_count(conn, "validation_findings") > 0
        assert row_count(conn, "retry_queue") > 0
        assert row_count(conn, "incidents") > 0
        assert row_count(conn, "audit_log") > 0

