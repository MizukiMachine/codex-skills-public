# Rate Limits and Billing

Rate limits and billing are separate control planes.

## Core rule
- Rate limits control request frequency.
- Billing controls paid usage/resources.
- You can be within rate limits and still incur significant cost.

## Request workflows (lookup and mutations)
- Treat each endpoint + auth context as its own rate bucket.
- Read limits and reset behavior from response headers, not static assumptions.
- For user-owned mutations (likes/bookmarks), enforce idempotent behavior in your app before retrying.

## Stream workflows (long-lived connections)
- Streams are connection-oriented, not short request bursts.
- Design for reconnect loops, heartbeat/keepalive handling, and backfill on resume.
- For likes streams:
  - `backfill_minutes` max is 5.
  - firehose `partition` range is 1 to 20.
  - sample10 `partition` range is 1 to 2.
- Validate stream config at boot and fail fast on invalid partitions.

## Header-driven control
Inspect on every response:
- `x-rate-limit-limit`
- `x-rate-limit-remaining`
- `x-rate-limit-reset`

Use `x-rate-limit-reset` to schedule retries after 429 responses.

## Billing behavior guidance
- Pricing model is credit-based pay-per-usage.
- Deduplication is documented per UTC day window for repeated resources.
- Exact endpoint pricing should be pulled from current pricing docs plus Developer Console before final cost estimates.
- Stream ingestion can dominate spend through sustained throughput; monitor by stream endpoint and partition.

## Cost-control tactics
- Request minimum fields and expansions.
- Batch where possible.
- Cache aggressively for repeated lookups.
- Track per-endpoint cost and hit rate.
- Alert on budget and credit thresholds.
- Use sampled streams when full firehose fidelity is not required.

## Implementation pattern
- Add rate-aware retry middleware.
- Add usage/cost telemetry by endpoint.
- Fail safely when budget guardrails trip.
- For streams, add reconnect metrics and dropped-event estimates.
