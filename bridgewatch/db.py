from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import Settings, get_settings
from .models import IntegrationEvent, ValidationFinding


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  source_system TEXT NOT NULL,
  event_type TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'received',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS integration_runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  processed INTEGER NOT NULL DEFAULT 0,
  passed INTEGER NOT NULL DEFAULT 0,
  failed INTEGER NOT NULL DEFAULT 0,
  queued_for_retry INTEGER NOT NULL DEFAULT 0,
  incidents_created INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS validation_findings (
  finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  check_name TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  field_path TEXT NOT NULL,
  can_retry INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES integration_runs(run_id)
);

CREATE TABLE IF NOT EXISTS retry_queue (
  retry_id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL,
  reason TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
  incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL,
  severity TEXT NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  owner TEXT NOT NULL,
  runbook_slug TEXT NOT NULL,
  created_at TEXT NOT NULL,
  resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
  audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  metadata_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(settings: Settings | None = None) -> sqlite3.Connection:
    resolved = settings or get_settings()
    resolved.database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(resolved.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def session(settings: Settings | None = None) -> Iterator[sqlite3.Connection]:
    conn = connect(settings)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize(settings: Settings | None = None) -> None:
    with session(settings) as conn:
        conn.executescript(SCHEMA)


def reset(settings: Settings | None = None) -> None:
    resolved = settings or get_settings()
    if resolved.database_path.exists():
        resolved.database_path.unlink()
    initialize(resolved)


def insert_events(events: list[IntegrationEvent], settings: Settings | None = None) -> int:
    initialize(settings)
    inserted = 0
    with session(settings) as conn:
        for event in events:
            try:
                conn.execute(
                    """
                    INSERT INTO events(event_id, source_system, event_type, occurred_at, payload_json, status, created_at)
                    VALUES (?, ?, ?, ?, ?, 'received', ?)
                    """,
                    (
                        event.event_id,
                        event.source_system,
                        event.event_type,
                        event.occurred_at.replace(microsecond=0).isoformat(),
                        json.dumps(event.payload, sort_keys=True),
                        utc_now(),
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                audit(conn, "system", "duplicate_event_ignored", "event", event.event_id, {"source": event.source_system})
    return inserted


def list_received_events(conn: sqlite3.Connection) -> list[IntegrationEvent]:
    rows = conn.execute(
        "SELECT * FROM events WHERE status = 'received' ORDER BY occurred_at ASC"
    ).fetchall()
    return [
        IntegrationEvent(
            event_id=row["event_id"],
            source_system=row["source_system"],
            event_type=row["event_type"],
            occurred_at=datetime.fromisoformat(row["occurred_at"]),
            payload=json.loads(row["payload_json"]),
        )
        for row in rows
    ]


def update_event_status(conn: sqlite3.Connection, event_id: str, status: str) -> None:
    conn.execute("UPDATE events SET status = ? WHERE event_id = ?", (status, event_id))


def save_finding(conn: sqlite3.Connection, run_id: str, finding: ValidationFinding) -> None:
    conn.execute(
        """
        INSERT INTO validation_findings(run_id, event_id, check_name, severity, message, field_path, can_retry, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            finding.event_id,
            finding.check_name,
            finding.severity.value,
            finding.message,
            finding.field_path,
            int(finding.can_retry),
            utc_now(),
        ),
    )


def audit(
    conn: sqlite3.Connection,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO audit_log(actor, action, entity_type, entity_id, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (actor, action, entity_type, entity_id, json.dumps(metadata or {}, sort_keys=True), utc_now()),
    )


def row_count(conn: sqlite3.Connection, table: str) -> int:
    allowed = {"events", "integration_runs", "validation_findings", "retry_queue", "incidents", "audit_log"}
    if table not in allowed:
        raise ValueError(f"Unsupported table: {table}")
    return int(conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"])


def database_exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0

