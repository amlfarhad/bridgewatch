#!/usr/bin/env bash
set -euo pipefail

export BRIDGEWATCH_BASE_RETRY_SECONDS=-1
if command -v bridgewatch >/dev/null 2>&1; then
  BRIDGEWATCH="bridgewatch"
else
  BRIDGEWATCH="python3 -m bridgewatch.cli"
fi

$BRIDGEWATCH reset
$BRIDGEWATCH seed
$BRIDGEWATCH run-once
$BRIDGEWATCH retry
$BRIDGEWATCH summary
