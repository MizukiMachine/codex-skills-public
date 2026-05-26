# Build Workflow

Use this workflow when implementing or reviewing X API integrations.

## 1. Scope the feature
- Define whether the feature is read-only, write, or mixed.
- Define whether the feature is request/response, stream ingestion, or both.
- Identify whether it is Posts-centric, Users-centric, or both.
- Decide if single-object or batch endpoints are needed.

## 2. Choose endpoint and auth model
- Pick the exact REST endpoint.
- Confirm auth requirement for that endpoint and requested fields.
- Confirm required scopes for user-context flows.
- Confirm credential family for the flow:
  - OAuth2 client ID/secret for PKCE user login.
  - OAuth1 keys and app bearer token are separate and not interchangeable.

## 2.5 Validate X portal app settings
- Register local callback URLs:
  - `http://localhost:3000/api/x/oauth/callback`
  - `http://127.0.0.1:3000/api/x/oauth/callback`
- Keep callback scheme as `http` for local dev callbacks unless local TLS is configured.
- Keep `redirect_uri` exact and stable in both authorize and token requests.
- If Website URL requires HTTPS in portal validation, set website metadata to `https://127.0.0.1:3000`.

## 3. Pin request contract
- Declare required fields and expansions explicitly.
- Avoid default payload assumptions.
- Validate request parameter bounds (for example batch size limits).
- Validate endpoint-specific constraints (for example likes stream partition ranges and backfill limits).

## 4. Implement parser contract
- Parse `data`, `includes`, and `errors` independently.
- For batch operations, treat partial success as normal behavior.
- Return unresolved IDs and failure reasons, not just generic errors.

## 5. Add operational protections
- Implement rate-limit handling via response headers.
- Use retry with backoff for transient and 429 scenarios.
- Protect write paths with idempotency strategy.
- Add stream reconnect policy and bounded backfill strategy for long-lived streams.

## 6. Add observability
- Log endpoint, auth mode, request IDs, rate-limit headers, and status.
- Track response size and latency per endpoint.
- Add counters for partial success and retries.

## 7. Validate scenarios
- Public lookup success.
- Protected/deleted/not-found object.
- Batch mixed validity.
- Auth mismatch.
- Rate limit hit and reset.
- Write failure and retry path.
- User-owned path ID mismatch (`/2/users/:id/...` with non-matching authenticated user).
- Likes lookup cap behavior (`liking_users` max 100 users lifetime).
- Stream disconnect and resume with valid `backfill_minutes`.
- Stream partition misconfiguration (fail fast before runtime).

## 8. Verify before merge
- Re-check current docs if the implementation depends on dynamic policy/pricing.
- Confirm output behavior against real response examples.
