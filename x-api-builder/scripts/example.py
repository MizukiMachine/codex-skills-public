#!/usr/bin/env python3
"""Small helper to print an endpoint checklist for X API implementation reviews.

Usage:
  python scripts/example.py posts_lookup
  python scripts/example.py users_lookup
  python scripts/example.py create_post
"""

from __future__ import annotations

import sys

CHECKLISTS = {
    "posts_lookup": [
        "Choose GET /2/tweets/:id or GET /2/tweets (batch up to 100).",
        "Specify tweet.fields and expansions explicitly.",
        "Handle partial success: parse both data and errors.",
        "Respect x-rate-limit headers and 429 reset handling.",
    ],
    "users_lookup": [
        "Choose ID or username endpoints based on caller input quality.",
        "Use /2/users/me only with user-context auth.",
        "Specify user.fields and expansions explicitly.",
        "Handle protected or missing users without assuming hard failure.",
    ],
    "create_post": [
        "Require user-context auth and verify write scopes.",
        "Validate request body constraints and mutual exclusivity.",
        "Treat retries carefully for writes; add idempotency strategy.",
        "Track both rate-limit and billing impacts.",
    ],
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in CHECKLISTS:
        print("Expected one argument: posts_lookup | users_lookup | create_post")
        return 2

    key = sys.argv[1]
    print(f"Checklist: {key}")
    for item in CHECKLISTS[key]:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
