# Posts and Users Playbook

This file focuses on practical endpoint choices for common features.

## Posts lookup

### Single post
- Endpoint: `GET /2/tweets/:id`
- Use when showing one specific post.
- Supports `tweet.fields`, `expansions`, `user.fields`, `media.fields`, `poll.fields`, `place.fields`.

### Batch posts
- Endpoint: `GET /2/tweets`
- Parameter: `ids` list, max 100 IDs per request.
- Use when rendering feeds or reconciling many known post IDs.
- Expect partial success (`data` + `errors`).

### Post edit semantics
- Lookup returns most recent version.
- Use `edit_history_tweet_ids` to reason about revisions.
- Model this in storage if historical consistency matters.

## Create or edit post
- Endpoint: `POST /2/tweets`
- Creates new post, or edits existing post when `edit_options.previous_post_id` is provided.
- Requires user-context auth and write-capable scopes.

### Common request constraints
- `media.media_ids`: min 1, max 4
- `media.tagged_user_ids`: max 10
- Poll options: 2 to 4
- Poll duration: 5 to 10080 minutes
- Several properties are mutually exclusive (for example poll/media/card/quote combinations)

## Users lookup

### By ID
- Single: `GET /2/users/:id`
- Batch: `GET /2/users` (max 100 IDs)

### By username
- Single: `GET /2/users/by/username/:username`
- Batch: `GET /2/users/by` (max 100 usernames)

### Authenticated user
- Endpoint: `GET /2/users/me`
- User-context auth only.
- Use for "current user" identity checks and account-specific flows.

## Bookmarks (user-owned and private)

### Get bookmarks
- Endpoint: `GET /2/users/:id/bookmarks`
- Returns bookmarked Posts for the authenticated user.
- Path ID must match the authenticated user.
- `max_results` range: 1 to 100.

### Add bookmark
- Endpoint: `POST /2/users/:id/bookmarks`
- Body: `tweet_id`
- Path ID must match the authenticated user.
- Response includes `data.bookmarked` boolean.

### Remove bookmark
- Endpoint: `DELETE /2/users/:id/bookmarks/:tweet_id`
- Path ID must match the authenticated user.
- Response includes `data.bookmarked` boolean.

## Likes lookup and manage

### Liking users for a post
- Endpoint: `GET /2/tweets/:id/liking_users`
- `max_results` range: 1 to 100.
- Important constraint: returns a maximum of 100 users per Post for all time.

### Liked posts for a user
- Endpoint: `GET /2/users/:id/liked_tweets`
- `max_results` range: 5 to 100.
- Supports pagination with `pagination_token`.

### Like and unlike
- Endpoints:
  - `POST /2/users/:id/likes`
  - `DELETE /2/users/:id/likes/:tweet_id`
- Path ID must match the authenticated user.
- Mutation responses include `data.liked` boolean.

## Likes streams (real-time event ingestion)

### Firehose stream
- Endpoint: `GET /2/likes/firehose/stream`
- Required query: `partition` in range 1 to 20.
- Optional query: `backfill_minutes` in range 0 to 5.

### Sampled stream
- Endpoint: `GET /2/likes/sample10/stream`
- Required query: `partition` in range 1 to 2.
- Optional query: `backfill_minutes` in range 0 to 5.

### Stream contract notes
- Parse `data`, `includes`, and `errors` independently.
- Use explicit expansions (`liked_tweet_id`, `liked_tweet_author_id`) only when needed.
- Field naming can differ across doc sections (`liked_tweet_author_id` vs `tweet_author_id`); validate against live payloads before locking parsers.

## Field and expansion strategy
- Start from business need, then map minimum fields.
- Only request expansions you consume.
- Guard against missing `includes` blocks even when expansions are requested.

## Error shape guidance
- 404 for not found/protected in many single-lookup cases.
- Batch lookup may omit failed items from `data` and add details under `errors`.
- Mutation endpoints can return success booleans plus `errors`; handle both.
- Stream responses can include `errors` while connection remains active; do not treat every error payload as terminal.
