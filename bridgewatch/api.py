from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .adapters import sample_event_batch
from .auth import require_operator
from .config import get_settings
from .db import initialize, insert_events, row_count, session
from .pipeline import run_integrations
from .retry import process_retry_queue


ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"
RUNBOOK_DIR = ROOT / "docs" / "runbooks"


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize(get_settings())
    yield


app = FastAPI(title="Bridgewatch", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, object]:
    settings = get_settings()
    initialize(settings)
    with session(settings) as conn:
        return {
            "status": "ok",
            "database": str(settings.database_path),
            "counts": {
                "events": row_count(conn, "events"),
                "runs": row_count(conn, "integration_runs"),
                "findings": row_count(conn, "validation_findings"),
                "retries": row_count(conn, "retry_queue"),
                "incidents": row_count(conn, "incidents"),
            },
        }


@app.get("/api/dashboard")
def dashboard() -> dict[str, object]:
    settings = get_settings()
    initialize(settings)
    with session(settings) as conn:
        latest_run = conn.execute(
            "SELECT * FROM integration_runs ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        incidents = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM incidents WHERE status = 'open' ORDER BY created_at DESC LIMIT 20"
            ).fetchall()
        ]
        findings = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM validation_findings ORDER BY created_at DESC LIMIT 30"
            ).fetchall()
        ]
        retries = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM retry_queue ORDER BY updated_at DESC LIMIT 20"
            ).fetchall()
        ]
        events_by_status = [
            dict(row)
            for row in conn.execute(
                "SELECT status, COUNT(*) AS count FROM events GROUP BY status ORDER BY status"
            ).fetchall()
        ]
        severity = [
            dict(row)
            for row in conn.execute(
                "SELECT severity, COUNT(*) AS count FROM validation_findings GROUP BY severity ORDER BY severity"
            ).fetchall()
        ]
    return {
        "latest_run": dict(latest_run) if latest_run else None,
        "events_by_status": events_by_status,
        "severity": severity,
        "incidents": incidents,
        "findings": findings,
        "retries": retries,
    }


@app.post("/api/ingest/sample")
def ingest_sample(actor: str = Depends(require_operator)) -> dict[str, object]:
    inserted = insert_events(sample_event_batch(), get_settings())
    return {"actor": actor, "inserted": inserted}


@app.post("/api/integrations/run")
def run_once(actor: str = Depends(require_operator)) -> dict[str, object]:
    result = run_integrations(get_settings())
    return {
        "actor": actor,
        "run_id": result.run_id,
        "processed": result.processed,
        "passed": result.passed,
        "failed": result.failed,
        "queued_for_retry": result.queued_for_retry,
        "incidents_created": result.incidents_created,
    }


@app.post("/api/retries/process")
def process_retries(actor: str = Depends(require_operator)) -> dict[str, object]:
    settings = get_settings()
    with session(settings) as conn:
        result = process_retry_queue(conn, settings)
    return {"actor": actor, **result}


@app.get("/api/runbooks")
def runbooks() -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for path in sorted(RUNBOOK_DIR.glob("*.md")):
        title = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        entries.append({"slug": path.stem, "title": title, "path": f"docs/runbooks/{path.name}"})
    return entries


@app.get("/api/audit")
def audit_log() -> list[dict[str, object]]:
    with session(get_settings()) as conn:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 50").fetchall()
        output = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item.pop("metadata_json"))
            output.append(item)
        return output
