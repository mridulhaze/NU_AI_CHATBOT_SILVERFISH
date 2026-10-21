import os
import time
from collections import defaultdict
from typing import Optional
from fastapi import HTTPException

class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int = None):
        if requests_per_minute is not None:
            self.limit = requests_per_minute
        else:
            self.limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
        self.requests = defaultdict(list)

    def reset_ip(self, client_ip: str):
        """Resets the request counter for a client IP upon successful CAPTCHA verification."""
        if client_ip in self.requests:
            self.requests[client_ip] = []

    def check_rate_limit(self, client_ip: str, captcha_token: Optional[str] = None):
        if self.limit <= 0:
            return

        # Check if client presented a valid CAPTCHA token
        if captcha_token:
            from backend.services.captcha_service import captcha_service
            if captcha_service.is_token_valid(captcha_token, client_ip):
                # Verified human gets elevated/unrestricted limit
                return

        now = time.time()
        window_start = now - 60.0
        
        # Clean timestamps older than 1 minute
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]
        
        if len(self.requests[client_ip]) >= self.limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please solve the security verification to continue."
            )
        
        self.requests[client_ip].append(now)

rate_limiter = InMemoryRateLimiter()
