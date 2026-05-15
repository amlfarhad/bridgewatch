# Architecture

Bridgewatch is organized around the path an integration event follows from source system to operational decision.

## Components

- **Adapter layer:** creates normalized event objects from source systems such as order management, payments, customer profiles, and support.
- **Validation engine:** applies shape, business-rule, referential, freshness, and operational checks.
- **Operational store:** persists events, validation findings, integration runs, retry items, incidents, and audit entries.
- **Retry controller:** enforces attempt limits and escalation policy for recoverable failures.
- **API service:** exposes dashboard, ingestion, validation, retry, runbook, and audit endpoints.
- **Dashboard:** surfaces health metrics, open incidents, retry queue state, and recent validation findings.

## Data Flow

1. Source events are inserted into the `events` table with `received` status.
2. An integration run loads received events and validates them as one batch.
3. Clean events move to `routed`.
4. Recoverable failures are recorded in `validation_findings` and queued for retry.
5. High-severity failures create incidents with an assigned runbook.
6. Retry processing either returns events for revalidation or blocks them after the attempt limit.

## Reliability Boundaries

Bridgewatch treats validation, retry, incident creation, and audit logging as separate responsibilities. This keeps operational decisions explainable and makes failures easier to debug.

