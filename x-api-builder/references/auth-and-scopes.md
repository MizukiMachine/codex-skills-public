# Auth and Scopes Matrix

Use this matrix to choose token type before implementation.

## Token models
- App-only (Bearer token): service-level access for public data workflows.
- OAuth 1.0a user context: user delegated access, often needed for write/private contexts.
- OAuth 2.0 user context (PKCE/authorization code): user delegated access with explicit scopes.

## Credential mapping (X portal)
- OAuth 2.0 app credentials:
  - `X_CLIENT_ID` <- OAuth 2.0 Client ID
  - `X_CLIENT_SECRET` <- OAuth 2.0 Client Secret
- OAuth 1.0a app keys:
  - consumer key / consumer secret (do not map to `X_CLIENT_ID` / `X_CLIENT_SECRET`)
- App-only token:
  - bearer token for app-level requests (not a user-login substitute)

## Local OAuth URL rules
- Register both callback URLs in X app settings when developing locally:
  - `http://localhost:3000/api/x/oauth/callback`
  - `http://127.0.0.1:3000/api/x/oauth/callback`
- Keep callback URLs on `http` for local Next.js callback handlers unless your local server is actually TLS.
- Keep `redirect_uri` exact across authorize request, token exchange, and app settings.
- X app Website URL may require HTTPS validation; use `https://127.0.0.1:3000` for website metadata if needed.

## Practical decisions

### Public read workflows
- Typical choice: app-only bearer token.
- Example operations: public post/user lookup.

### User identity and user-owned operations
- Requires user-context token.
- Example operation: `GET /2/users/me`.

### Post write workflows
- Requires user-context token with write-capable scopes.
- Example operation: `POST /2/tweets`.

### Bookmarks
- `GET /2/users/:id/bookmarks` requires user context and OAuth2 scopes:
  - `bookmark.read`
  - `tweet.read`
  - `users.read`
- `POST`/`DELETE` bookmark endpoints require:
  - `bookmark.write`
  - `tweet.read`
  - `users.read`
- Path `:id` must match the authenticated user.

### Likes lookup
- `GET /2/tweets/:id/liking_users` and `GET /2/users/:id/liked_tweets` support user-context auth:
  - OAuth 2 user token with `like.read`, `tweet.read`, `users.read`, or
  - OAuth 1.0a user token.
- Do not assume app-only support from overview pages without checking endpoint OpenAPI.

### Likes manage
- `POST /2/users/:id/likes` and `DELETE /2/users/:id/likes/:tweet_id` require user-context auth:
  - OAuth 2 scopes: `like.write`, `tweet.read`, `users.read`, or
  - OAuth 1.0a user token.
- Path `:id` must match the authenticated user.

### Likes streams
- `GET /2/likes/firehose/stream` and `GET /2/likes/sample10/stream` use bearer-token auth in endpoint OpenAPI.
- Treat these as entitlement-gated products and validate access at startup.

## Common auth mistakes
- Using app-only token for `/2/users/me`.
- Missing one required scope on write operations.
- Treating OAuth1 and OAuth2 user-context tokens as interchangeable in app config.
- Not validating that user-owned path IDs match the authenticated principal.
- Assuming overview docs override endpoint-level OpenAPI security declarations.

## SDK mapping note
- TypeScript XDK `Client` supports bearer token and user-context credentials.
- Keep auth initialization explicit and test with endpoint-specific smoke checks.
