from __future__ import annotations

import argparse
import json

from .adapters import sample_event_batch
from .config import get_settings
from .db import initialize, insert_events, reset, row_count, session
from .pipeline import run_integrations
from .retry import process_retry_queue


def main() -> None:
    parser = argparse.ArgumentParser(prog="bridgewatch")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("reset")
    sub.add_parser("seed")
    sub.add_parser("run-once")
    sub.add_parser("retry")
    sub.add_parser("summary")
    args = parser.parse_args()
    settings = get_settings()

    if args.command == "reset":
        reset(settings)
        print(f"Reset {settings.database_path}")
    elif args.command == "seed":
        inserted = insert_events(sample_event_batch(), settings)
        print(json.dumps({"inserted": inserted}, indent=2))
    elif args.command == "run-once":
        result = run_integrations(settings)
        print(json.dumps(result.__dict__ | {"findings": [item.__dict__ for item in result.findings]}, default=str, indent=2))
    elif args.command == "retry":
        initialize(settings)
        with session(settings) as conn:
            print(json.dumps(process_retry_queue(conn, settings), indent=2))
    elif args.command == "summary":
        initialize(settings)
        with session(settings) as conn:
            print(json.dumps({
                "events": row_count(conn, "events"),
                "runs": row_count(conn, "integration_runs"),
                "findings": row_count(conn, "validation_findings"),
                "retries": row_count(conn, "retry_queue"),
                "incidents": row_count(conn, "incidents"),
                "audit": row_count(conn, "audit_log"),
            }, indent=2))


if __name__ == "__main__":
    main()

