from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3

from .config import Settings
from .db import audit, utc_now
from .models import Severity, ValidationFinding


def next_attempt_time(attempts: int, settings: Settings) -> str:
    wait_seconds = settings.base_retry_seconds * (2 ** max(attempts, 0))
    return (datetime.now(timezone.utc) + timedelta(seconds=wait_seconds)).replace(microsecond=0).isoformat()


def queue_retry(
    conn: sqlite3.Connection,
    finding: ValidationFinding,
    settings: Settings,
) -> None:
    existing = conn.execute(
        """
        SELECT retry_id, attempts, status
        FROM retry_queue
        WHERE event_id = ? AND status IN ('queued', 'processing')
        ORDER BY retry_id DESC
        LIMIT 1
        """,
        (finding.event_id,),
    ).fetchone()
    if existing:
        return
    conn.execute(
        """
        INSERT INTO retry_queue(event_id, reason, attempts, next_attempt_at, status, created_at, updated_at)
        VALUES (?, ?, 0, ?, 'queued', ?, ?)
        """,
        (
            finding.event_id,
            f"{finding.check_name}: {finding.message}",
            next_attempt_time(0, settings),
            utc_now(),
            utc_now(),
        ),
    )
    audit(conn, "system", "retry_queued", "event", finding.event_id, {"reason": finding.message})


def create_incident(
    conn: sqlite3.Connection,
    event_id: str,
    severity: Severity,
    title: str,
    runbook_slug: str,
    owner: str = "integration-ops",
) -> None:
    existing = conn.execute(
        """
        SELECT incident_id
        FROM incidents
        WHERE event_id = ? AND status = 'open'
        LIMIT 1
        """,
        (event_id,),
    ).fetchone()
    if existing:
        return
    conn.execute(
        """
        INSERT INTO incidents(event_id, severity, title, status, owner, runbook_slug, created_at)
        VALUES (?, ?, ?, 'open', ?, ?, ?)
        """,
        (event_id, severity.value, title, owner, runbook_slug, utc_now()),
    )
    audit(conn, "system", "incident_created", "event", event_id, {"severity": severity.value, "title": title})


def process_retry_queue(conn: sqlite3.Connection, settings: Settings) -> dict[str, int]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rows = conn.execute(
        """
        SELECT retry_id, event_id, attempts, reason
        FROM retry_queue
        WHERE status = 'queued' AND next_attempt_at <= ?
        ORDER BY next_attempt_at ASC
        """,
        (now,),
    ).fetchall()
    processed = 0
    blocked = 0
    resolved = 0
    for row in rows:
        processed += 1
        attempts = int(row["attempts"]) + 1
        if attempts >= settings.max_retry_attempts:
            blocked += 1
            conn.execute(
                """
                UPDATE retry_queue
                SET attempts = ?, status = 'blocked', updated_at = ?
                WHERE retry_id = ?
                """,
                (attempts, utc_now(), row["retry_id"]),
            )
            conn.execute("UPDATE events SET status = 'blocked' WHERE event_id = ?", (row["event_id"],))
            create_incident(
                conn,
                event_id=row["event_id"],
                severity=Severity.HIGH,
                title="Retry attempts exhausted",
                runbook_slug="retry-exhausted",
            )
        else:
            resolved += 1
            conn.execute(
                """
                UPDATE retry_queue
                SET attempts = ?, status = 'resolved', updated_at = ?
                WHERE retry_id = ?
                """,
                (attempts, utc_now(), row["retry_id"]),
            )
            conn.execute("UPDATE events SET status = 'received' WHERE event_id = ?", (row["event_id"],))
            audit(conn, "system", "retry_resolved_for_revalidation", "event", row["event_id"], {"attempts": attempts})
    return {"processed": processed, "resolved": resolved, "blocked": blocked}

