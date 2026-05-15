# Operating Model

Bridgewatch is designed for a small IT or platform team supporting integrations across business systems.

## Roles

- **Operator:** reviews dashboard status, runs validations, processes retries, and follows runbooks.
- **Service owner:** owns business rules and validates whether a failed record can be corrected or replayed.
- **Platform engineer:** maintains adapters, database schema, API service, and deployment pipeline.
- **Business stakeholder:** receives concise status summaries and impact notes.

## Daily Workflow

1. Review open incidents and queued retry items.
2. Run validation after each new batch or deployment.
3. Triage high-severity findings first.
4. Use runbooks to separate recoverable upstream data issues from non-retryable schema or configuration failures.
5. Document recurring failures as candidate process improvements.

## Escalation Policy

- **Critical:** immediate owner review, blocked routing, incident required.
- **High:** incident required, retry only when the finding is recoverable.
- **Medium:** queue retry or monitor depending on freshness and data quality impact.
- **Low:** document and trend.

