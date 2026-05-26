# Source of Truth Links

Use these links when implementing or verifying behavior.

## Core pages
- X API intro: `https://docs.x.com/x-api/introduction`
- LLM index: `https://docs.x.com/llms.txt`
- Pricing: `https://docs.x.com/x-api/getting-started/pricing`
- Usage and billing details: `https://docs.x.com/x-api/fundamentals/post-cap`
- Rate limits: `https://docs.x.com/x-api/fundamentals/rate-limits`

## Posts
- Post lookup intro: `https://docs.x.com/x-api/posts/lookup/introduction`
- Get post by ID: `https://docs.x.com/x-api/posts/get-post-by-id`
- Get posts by IDs: `https://docs.x.com/x-api/posts/get-posts-by-ids`
- Create or edit post: `https://docs.x.com/x-api/posts/create-post`
- Post lookup integration guide: `https://docs.x.com/x-api/posts/lookup/integrate`
- Get liking users: `https://docs.x.com/x-api/posts/get-liking-users`

## Bookmarks
- Bookmarks intro: `https://docs.x.com/x-api/posts/bookmarks/introduction`
- Get bookmarks: `https://docs.x.com/x-api/users/get-bookmarks`
- Create bookmark: `https://docs.x.com/x-api/users/create-bookmark`
- Delete bookmark: `https://docs.x.com/x-api/users/delete-bookmark`

## Likes
- Likes intro: `https://docs.x.com/x-api/posts/likes/introduction`
- Get liked posts: `https://docs.x.com/x-api/users/get-liked-posts`
- Like post: `https://docs.x.com/x-api/users/like-post`
- Unlike post: `https://docs.x.com/x-api/users/unlike-post`

## Likes Streams
- Stream all likes: `https://docs.x.com/x-api/stream/stream-all-likes`
- Stream sampled likes: `https://docs.x.com/x-api/stream/stream-sampled-likes`

## Users
- User lookup intro: `https://docs.x.com/x-api/users/lookup/introduction`
- Get user by ID: `https://docs.x.com/x-api/users/get-user-by-id`
- Get users by IDs: `https://docs.x.com/x-api/users/get-users-by-ids`
- Get user by username: `https://docs.x.com/x-api/users/get-user-by-username`
- Get users by usernames: `https://docs.x.com/x-api/users/get-users-by-usernames`
- Get my user: `https://docs.x.com/x-api/users/get-my-user`
- User lookup integration guide: `https://docs.x.com/x-api/users/lookup/integrate`

## TypeScript XDK
- Overview: `https://docs.x.com/xdks/typescript/overview`
- Install: `https://docs.x.com/xdks/typescript/install`
- Authentication: `https://docs.x.com/xdks/typescript/authentication`
- Posts client reference: `https://docs.x.com/xdks/typescript/reference/classes/PostsClient`
- Users client reference: `https://docs.x.com/xdks/typescript/reference/classes/UsersClient`
- Stream client reference: `https://docs.x.com/xdks/typescript/reference/classes/StreamClient`

## Verification discipline
- Re-check these pages before finalizing implementation if the task depends on changing policy, pricing, or limits.
- Treat dated snippets from secondary sources as non-authoritative.
- If conflicts appear across docs, prefer dedicated endpoint and fundamentals pages over overview marketing pages.

## Note on temporal stability
This reference set was curated on February 9, 2026. Re-verify current values for rate limits, pricing, and auth requirements during implementation.
