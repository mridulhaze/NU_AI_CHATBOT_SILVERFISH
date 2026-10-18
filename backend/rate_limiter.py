import os
import time
from collections import defaultdict
from fastapi import Request, HTTPException

class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int = None):
        if requests_per_minute is not None:
            self.limit = requests_per_minute
        else:
            self.limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
        self.requests = defaultdict(list)

    def check_rate_limit(self, client_ip: str):
        if self.limit <= 0:
            return
        now = time.time()
        window_start = now - 60.0
        
        # Clean timestamps older than 1 minute
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]
        
        if len(self.requests[client_ip]) >= self.limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please wait a moment before sending more messages."
            )
        
        self.requests[client_ip].append(now)

rate_limiter = InMemoryRateLimiter()
