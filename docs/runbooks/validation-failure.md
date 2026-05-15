# Validation Failure

## Signal

An event fails a required field, status, region, owner, or schema check.

## Impact

Validation failures can prevent safe routing to downstream systems.

## Response

1. Review the failed check and field path.
2. Confirm whether the issue is recoverable.
3. If recoverable, queue retry after source correction.
4. If not recoverable, block the event and escalate with payload context.
5. Add recurring patterns to the integration backlog.

