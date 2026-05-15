# ADR 0002: Deterministic Validation

## Status

Accepted

## Context

Integration reliability requires explainable outcomes. Operators need to know why an event failed, whether it can be retried, and which runbook applies.

## Decision

Use deterministic validation checks rather than model-generated judgments for operational routing.

## Consequences

- Findings are reproducible.
- Tests can cover each failure mode.
- AI can still assist documentation or summarization later, but routing remains deterministic.

