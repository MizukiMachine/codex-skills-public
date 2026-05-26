# TypeScript XDK Mapping

Official package: `@xdevplatform/xdk`

## Client initialization
- App-only: `new Client({ bearerToken })`
- User-context: `new Client({ accessToken })` or OAuth helper objects

## Common endpoint mappings

### Posts lookup and write
- `GET /2/tweets/:id` -> `client.posts.getById(id, options?)`
- `GET /2/tweets` -> `client.posts.getByIds(ids, options?)`
- `POST /2/tweets` -> `client.posts.create(body)`
- `DELETE /2/tweets/:id` -> `client.posts.delete(id)`
- `GET /2/tweets/:id/liking_users` -> `client.posts.getLikingUsers(id, options?)`

### Users lookup
- `GET /2/users/:id` -> `client.users.getById(id, options?)`
- `GET /2/users` -> `client.users.getByIds(ids, options?)`
- `GET /2/users/by/username/:username` -> `client.users.getByUsername(username, options?)`
- `GET /2/users/by` -> `client.users.getByUsernames(usernames, options?)`
- `GET /2/users/me` -> `client.users.getMe(options?)`

### Likes and bookmarks (user-owned)
- `GET /2/users/:id/bookmarks` -> `client.users.getBookmarks(id, options?)`
- `POST /2/users/:id/bookmarks` -> `client.users.createBookmark(id, body)`
- `DELETE /2/users/:id/bookmarks/:tweet_id` -> `client.users.deleteBookmark(id, tweetId)`
- `GET /2/users/:id/liked_tweets` -> `client.users.getLikedPosts(id, options?)`
- `POST /2/users/:id/likes` -> `client.users.likePost(id, body)`
- `DELETE /2/users/:id/likes/:tweet_id` -> `client.users.unlikePost(id, tweetId)`

### Likes streams
- `GET /2/likes/firehose/stream` -> `client.stream.likesFirehose(partition, options?)`
- `GET /2/likes/sample10/stream` -> `client.stream.likesSample10(partition, options?)`

## Option strategy
- Keep `tweetFields`, `userFields`, `mediaFields`, `expansions` explicit.
- Do not assume defaults include required fields.
- For stream methods, pass explicit options for backfill and expansions only when needed.

## Production notes
- Validate SDK version against current API docs before large upgrades.
- For critical paths, support fallback to raw REST calls if SDK lag appears.
- Parse partial successes in batch responses exactly as with REST usage.
- Ensure user-owned methods use the authenticated user's ID in path arguments.
