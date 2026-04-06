from collections import defaultdict, deque
from time import time
from fastapi import Request, HTTPException

# Configuration
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60


# In-memory store: {client_id: deque of request timestamps}
_request_log: dict[str, deque] = defaultdict(deque)


def get_rate_limit_key(request: Request, user_id: str | None = None) -> str:
    if user_id:
        return f"user:{user_id}"
    forwarded_for = request.headers.get("X-Forwarded-For")
    ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.client.host
    return f"ip:{ip}"


def check_rate_limit(request: Request, user_id: str | None = None):
    key = get_rate_limit_key(request, user_id)
    now = time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    timestamps = _request_log[key]
    
    # Drop timestamps outside current window
    while timestamps and timestamps[0] < window_start:
        timestamps.popleft()

    if len(timestamps) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW_SECONDS}."
        )

    timestamps.append(now)

