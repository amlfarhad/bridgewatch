# Retry Exhausted

## Signal

An event reached the maximum retry attempt limit.

## Impact

The record is blocked and needs owner review before any replay.

## Response

1. Review retry history and original validation findings.
2. Confirm whether the upstream issue has been corrected.
3. Decide whether to manually replay, block permanently, or create a source-system fix ticket.
4. Document the decision in the incident notes.

