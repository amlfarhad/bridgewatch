from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path
    api_key: str
    max_retry_attempts: int = 3
    base_retry_seconds: int = 60
    stale_event_minutes: int = 45


def get_settings() -> Settings:
    default_db = Path.cwd() / "bridgewatch.db"
    return Settings(
        database_path=Path(os.getenv("BRIDGEWATCH_DB", str(default_db))).expanduser(),
        api_key=os.getenv("BRIDGEWATCH_API_KEY", "local-operator-key"),
        max_retry_attempts=int(os.getenv("BRIDGEWATCH_MAX_RETRIES", "3")),
        base_retry_seconds=int(os.getenv("BRIDGEWATCH_BASE_RETRY_SECONDS", "60")),
        stale_event_minutes=int(os.getenv("BRIDGEWATCH_STALE_EVENT_MINUTES", "45")),
    )

