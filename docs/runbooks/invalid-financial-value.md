# Invalid Financial Value

## Signal

An order or payment event contains a zero, negative, or otherwise invalid amount.

## Impact

Invalid values can distort reconciliation, revenue reporting, and exception handling.

## Response

1. Confirm the event amount and currency.
2. Compare the event with the source-system transaction.
3. Determine whether the issue is data entry, transformation logic, or missing adjustment context.
4. Retry only after corrected source data is available.

