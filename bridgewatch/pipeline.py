from __future__ import annotations

from collections import defaultdict
from uuid import uuid4

from .config import Settings, get_settings
from .db import audit, initialize, list_received_events, save_finding, session, update_event_status, utc_now
from .models import IntegrationRunResult, Severity, ValidationFinding
from .retry import create_incident, queue_retry
from .validation import validate_event


def run_integrations(settings: Settings | None = None) -> IntegrationRunResult:
    resolved = settings or get_settings()
    initialize(resolved)
    run_id = f"run-{uuid4().hex[:10]}"
    findings: list[ValidationFinding] = []
    passed = 0
    failed = 0
    queued_for_retry = 0
    incidents_created = 0

    with session(resolved) as conn:
        conn.execute(
            """
            INSERT INTO integration_runs(run_id, started_at)
            VALUES (?, ?)
            """,
            (run_id, utc_now()),
        )
        events = list_received_events(conn)
        event_findings: dict[str, list[ValidationFinding]] = defaultdict(list)
        for event in events:
            event_findings[event.event_id].extend(validate_event(event, events, resolved))

        for event in events:
            current_findings = event_findings[event.event_id]
            findings.extend(current_findings)
            if not current_findings:
                passed += 1
                update_event_status(conn, event.event_id, "routed")
                audit(conn, "system", "event_routed", "event", event.event_id, {"run_id": run_id})
                continue

            failed += 1
            update_event_status(conn, event.event_id, "failed")
            for finding in current_findings:
                save_finding(conn, run_id, finding)
                if finding.can_retry:
                    queued_for_retry += 1
                    queue_retry(conn, finding, resolved)
                if finding.severity in {Severity.HIGH, Severity.CRITICAL}:
                    incidents_created += 1
                    create_incident(
                        conn,
                        event_id=finding.event_id,
                        severity=finding.severity,
                        title=finding.message,
                        runbook_slug=runbook_for(finding),
                    )
        conn.execute(
            """
            UPDATE integration_runs
            SET completed_at = ?, processed = ?, passed = ?, failed = ?, queued_for_retry = ?, incidents_created = ?
            WHERE run_id = ?
            """,
            (utc_now(), len(events), passed, failed, queued_for_retry, incidents_created, run_id),
        )
        audit(conn, "system", "integration_run_completed", "run", run_id, {"processed": len(events), "failed": failed})

    return IntegrationRunResult(
        run_id=run_id,
        processed=passed + failed,
        passed=passed,
        failed=failed,
        queued_for_retry=queued_for_retry,
        incidents_created=incidents_created,
        findings=findings,
    )


def runbook_for(finding: ValidationFinding) -> str:
    if "reference" in finding.check_name:
        return "missing-reference"
    if "freshness" in finding.check_name:
        return "stale-event"
    if "amount" in finding.check_name:
        return "invalid-financial-value"
    return "validation-failure"

