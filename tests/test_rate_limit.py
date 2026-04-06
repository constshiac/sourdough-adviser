from collections import defaultdict, deque
from time import time

RATE_LIMIT = 5    # lowered so you can see the limit hit quickly
WINDOW_SECS = 10  # short window for testing

_request_log = defaultdict(deque)

def check_rate_limit(key: str):
    now = time()
    window_start = now - WINDOW_SECS
    timestamps = _request_log[key]

    # Drop old timestamps
    while timestamps and timestamps[0] < window_start:
        timestamps.popleft()

    print(f"  Key: '{key}' | Timestamps in window: {list(timestamps)}")

    if len(timestamps) >= RATE_LIMIT:
        print(f"  ❌ BLOCKED — {len(timestamps)} requests already in window")
        return False

    timestamps.append(now)
    print(f"  ✅ ALLOWED — now {len(timestamps)} requests in window")
    return True

# Simulate 7 requests from the same key
print("=== Simulating 7 requests ===")
for i in range(1, 8):
    print(f"\nRequest {i}:")
    check_rate_limit("user:local")