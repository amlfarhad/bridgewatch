# Missing Reference

## Signal

An event references a customer, order, or downstream entity that is not available in the current batch.

## Impact

Routing the record may create incomplete reporting, orphaned payments, or broken customer context.

## Response

1. Confirm the referenced entity ID in the failed event payload.
2. Search the source batch for the missing entity.
3. Check whether the upstream system delivered records out of order.
4. Retry once the referenced entity arrives.
5. Escalate to the source-system owner if repeated batches are missing the same entity.

