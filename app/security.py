from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def _sign(payload: bytes, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(signature).decode("utf-8")


def create_csrf_token(secret: str, client_identifier: str) -> str:
    ts = str(int(time.time()))
    nonce = secrets.token_urlsafe(16)
    raw = f"{ts}|{client_identifier}|{nonce}".encode("utf-8")
    body = base64.urlsafe_b64encode(raw).decode("utf-8")
    sig = _sign(raw, secret)
    return f"{body}.{sig}"


def validate_csrf_token(secret: str, client_identifier: str, token: str, max_age_seconds: int = 7200) -> bool:
    try:
        body, signature = token.split(".", 1)
        raw = base64.urlsafe_b64decode(body.encode("utf-8"))
        expected_sig = _sign(raw, secret)
        if not hmac.compare_digest(signature, expected_sig):
            return False
        ts_str, bound_identifier, _nonce = raw.decode("utf-8").split("|", 2)
        if bound_identifier != client_identifier:
            return False
        token_age = int(time.time()) - int(ts_str)
        return token_age <= max_age_seconds
    except Exception:
        return False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:;"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 40):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._hits: dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client = request.client.host if request.client else "unknown"
        now = time.time()
        q = self._hits[client]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Zu viele Anfragen. Bitte kurz warten.",
            )
        q.append(now)
        return await call_next(request)
