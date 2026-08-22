import time

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rate_limit = requests_per_minute
        self.clients = {}

    async def check(self, request: Request):
        client_ip = request.client.host
        current_time = time.time()
        
        if client_ip not in self.clients:
            self.clients[client_ip] = []
            
        # Clean old requests
        self.clients[client_ip] = [t for t in self.clients[client_ip] if current_time - t < 60]
        
        if len(self.clients[client_ip]) >= self.rate_limit:
            raise HTTPException(status_code=429, detail="Too Many Requests")
            
        self.clients[client_ip].append(current_time)
        return True

rate_limiter = RateLimiter()
