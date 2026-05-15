# ADR 0001: SQLite Operational Store

## Status

Accepted

## Context

The project needs persistent state for events, validation results, retry attempts, incidents, and audit entries without requiring external infrastructure.

## Decision

Use SQLite as the local operational store.

## Consequences

- The system is easy to run locally and in CI.
- SQL tables make the operational model inspectable.
- The schema can later be moved to Postgres with minimal conceptual changes.

