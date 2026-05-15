# Stale Event

## Signal

An event arrived outside the expected freshness window.

## Impact

Stale records can make dashboards, operational reports, and downstream decisions appear current when they are not.

## Response

1. Check the event timestamp and source system.
2. Compare freshness against the configured threshold.
3. Review recent upstream delivery delays.
4. Retry if the event is otherwise valid.
5. Trend repeated stale events by source system.

