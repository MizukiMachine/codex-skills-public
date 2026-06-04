---
name: x-api-builder
description: "X APIを使った本番向け統合を構築する。投稿、ユーザー、いいね、ブックマーク、ストリーム、認証スコープ、フィールド展開、従量課金管理で使う。"
metadata:
  short-description: "本番向けX API統合ビルダー"
---

# X API Builder

Build reliable X API integrations that survive real production constraints: auth mismatch, partial responses, rate limits, and billing surprises.

## Philosophy: Contract-First Integration

Treat X API work as a contract system, not a quick HTTP-call task. A correct integration is one that stays correct under changing data, auth context, and platform limits.

**Before implementing, ask:**
- Which contract am I targeting: REST endpoint, SDK method, or both?
- What auth context is required for this exact operation and fields?
- What are the operational constraints: rate window, retries, partial errors, cost model?
- How will this degrade when data is missing, protected, deleted, or partially returned?

**Core principles:**
1. Verify first, code second: derive behavior from current docs/OpenAPI, then implement.
2. Scope is data access: fields and expansions are permissions and payload decisions, not cosmetics.
3. Production over demo: include retry, observability, partial-failure handling, and budget awareness from day one.

## Workflow

### 1. Define Integration Shape
- Choose endpoint family and auth model first.
- Pin required response fields and expansions before writing business logic.
- Decide if the integration is lookup, user-owned mutation, or long-lived stream ingestion.
- For Posts/Users features, decide whether you need single-item lookup, batch lookup, or write operations.
- Use `references/posts-users-playbook.md` to select canonical endpoint patterns.

### 2. Resolve Auth and Scopes
- Confirm whether app-only is sufficient or user-context is mandatory.
- For write operations like create post, require user-context permissions and scopes.
- For `/2/users/me`, require user-context only.
- For user-owned Likes/Bookmarks writes, ensure path user IDs match the authenticated user.
- For Likes Streams, validate bearer-token access and stream product entitlement before coding.
- Keep credential families explicit:
  - OAuth 2.0 app credentials: `X_CLIENT_ID` + `X_CLIENT_SECRET`.
  - OAuth 1.0a app keys: consumer key/secret (different family).
  - App-only bearer token: service token, not user login.
- For local OAuth dev in X portal, register both callback URLs:
  - `http://localhost:3000/api/x/oauth/callback`
  - `http://127.0.0.1:3000/api/x/oauth/callback`
- Keep `redirect_uri` byte-for-byte identical across authorize + token exchange + app settings.
- If X portal requires Website URL validation for local apps, use `https://127.0.0.1:3000` for website metadata and keep callback URLs on `http`.
- Use `references/auth-and-scopes.md` to map operation to token type.

### 3. Design Request/Response Contract
- Request only needed fields (`tweet.fields`, `user.fields`, etc.) and explicit expansions.
- Build parser logic that tolerates partial success in batch endpoints (`data` plus `errors`).
- Handle missing includes safely.
- Normalize IDs as strings end-to-end.
- For mutation endpoints, model boolean result envelopes (`liked`, `bookmarked`) and error arrays.
- For likes streams, model event payload and include-aware expansions separately.

### 4. Add Operational Guardrails
- Implement rate-limit-aware retry with header-driven reset handling.
- Distinguish idempotent retries (safe) from write retries (needs dedupe strategy).
- Log request metadata needed for debugging and billing analysis.
- For streams, implement reconnect + bounded backfill and enforce valid partition ranges.
- Use `references/rate-limits-and-billing.md` for baseline limits and cost behavior.

### 5. Map to TypeScript XDK When Needed
- Prefer official SDK methods when building TypeScript services.
- Keep method usage aligned with endpoint semantics.
- Use `references/typescript-xdk-mapping.md` for REST-to-XDK mapping.

### 6. Validate with Scenario Matrix
- Validate with these cases before shipping:
- Public object lookup success.
- Missing, deleted, or protected object.
- Batch request with mixed valid and invalid IDs.
- Rate-limit response and reset-aware retry path.
- Auth mismatch (app-only vs user-context).
- Field or expansion mismatch.
- User-owned endpoint with mismatched path ID (should fail).
- Likes lookup cap behavior (`/2/tweets/:id/liking_users` max 100 users lifetime).
- Stream reconnection with `backfill_minutes` and partition bounds.

## Output Guidance

When implementing X API features, produce outputs that include:
- Clear endpoint or SDK method choice and auth rationale.
- Concrete request examples with fields and expansions.
- Error, partial success, and retry behavior.
- Notes on rate limits and billing implications.
- If relevant, REST and TypeScript XDK versions side by side.

## Anti-Patterns to Avoid

❌ **Endpoint-first coding without auth model**
Why bad: creates immediate 401/403 failures and hidden permission bugs.
Better: lock auth context and scopes before code structure.

❌ **Mixing localhost and 127.0.0.1 in one OAuth flow**
Why bad: causes redirect URI mismatch on token exchange.
Better: register both callbacks in X, then use one host consistently per session.

❌ **Using HTTPS callback URLs for local PKCE flow by default**
Why bad: local setup often runs HTTP callback endpoints, causing callback mismatch.
Better: use `http://localhost:3000/api/x/oauth/callback` and/or `http://127.0.0.1:3000/api/x/oauth/callback` as configured.

❌ **Assuming full success in batch responses**
Why bad: X batch endpoints can return mixed `data` and `errors`.
Better: explicitly handle partial success and propagate unresolved IDs.

❌ **Requesting all fields by default**
Why bad: payload bloat, permission failures, and higher processing cost.
Better: request only required fields and expansions.

❌ **Confusing rate limits with billing**
Why bad: you can stay under request limits and still overspend.
Better: track both request frequency and billable resource usage.

❌ **Trusting stale pricing snippets**
Why bad: overview pages and secondary sources can lag current pricing model.
Better: treat pricing docs plus Developer Console as source of truth at implementation time.

❌ **Ignoring edit history semantics for posts**
Why bad: downstream systems mis-handle updated content.
Better: model `edit_history_tweet_ids` and "latest version returned" behavior.

❌ **Using generic retries for all writes**
Why bad: can duplicate actions or produce ambiguous state.
Better: apply idempotency strategy and explicit conflict handling.

❌ **Assuming all likes are pageable forever**
Why bad: `liking_users` is capped at 100 users per Post for all time.
Better: model this cap explicitly and route full-fidelity needs to stream/analytics pipelines.

❌ **Treating stream partitions as optional knobs**
Why bad: likes stream partitions are required and range-limited by endpoint.
Better: validate partition and backfill constraints at config load time.

## Variation Guidance

**IMPORTANT**: Implementations should vary based on product context, not converge on one pattern.
- Internal analytics backend: optimize batch lookup, throughput, and observability.
- User-facing app: prioritize latency, graceful fallback, and human-readable errors.
- Write-heavy workflows: emphasize scope checks, idempotency, and conflict handling.
- Cost-sensitive workflows: minimize fields and expansions, maximize caching and dedupe.

Avoid converging on one default stack or one "favorite" endpoint pattern when workload shape differs.

## References

- Endpoint and payload choices: `references/posts-users-playbook.md`
- Auth decision matrix and scopes: `references/auth-and-scopes.md`
- Rate-limit and billing operations: `references/rate-limits-and-billing.md`
- TypeScript XDK mapping: `references/typescript-xdk-mapping.md`
- Implementation checklist: `references/build-workflow.md`
- Source links and verification anchors: `references/api_reference.md`

## Empowered Execution

You are expected to produce integration code that is defensible in production review.
- Challenge ambiguous requirements that hide auth, rate-limit, or billing risk.
- Prefer explicit contracts over implicit assumptions.
- Make tradeoffs visible and choose reliability over short-term convenience.

## Remember

Codex can build X API integrations that are both fast and robust. Aim for correctness under change, not just first-response success.
