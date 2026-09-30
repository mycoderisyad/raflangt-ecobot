"""Bearer-token authentication for the future standalone admin UI."""

import hmac
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.schemas import AdminIdentity, LoginRequest, TokenResponse
from src.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
_bearer = HTTPBearer(auto_error=False)
_lock = threading.Lock()
_login_attempts: dict[str, deque[float]] = defaultdict(deque)


def _enforce_login_rate(request: Request) -> None:
    now = time.monotonic()
    key = request.client.host if request.client else "unknown"
    with _lock:
        attempts = _login_attempts[key]
        while attempts and now - attempts[0] >= 3600:
            attempts.popleft()
        if not attempts:
            _login_attempts.pop(key, None)
            attempts = _login_attempts[key]
        recent_minute = sum(now - attempt < 60 for attempt in attempts)
        if recent_minute >= 5 or len(attempts) >= 20:
            raise HTTPException(
                status_code=429, detail="Terlalu banyak percobaan login"
            )
        attempts.append(now)
        if len(_login_attempts) > 4096:
            stale = [
                ip
                for ip, stamps in _login_attempts.items()
                if not stamps or now - stamps[-1] >= 3600
            ]
            for ip in stale:
                _login_attempts.pop(ip, None)


def _auth_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kedaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AdminIdentity:
    settings = get_settings().app
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _auth_error()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.api_secret_key,
            algorithms=["HS256"],
            issuer="ecobot",
            audience="ecobot-admin",
        )
        subject = payload.get("sub")
        if subject != settings.admin_username:
            raise _auth_error()
        return AdminIdentity(username=subject)
    except jwt.InvalidTokenError as exc:
        raise _auth_error() from exc


AdminDep = Annotated[AdminIdentity, Depends(require_admin)]


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request) -> TokenResponse:
    _enforce_login_rate(request)
    settings = get_settings().app
    user_ok = hmac.compare_digest(
        body.username.encode(), settings.admin_username.encode()
    )
    pass_ok = hmac.compare_digest(
        body.password.encode(), settings.admin_password.encode()
    )
    if not (user_ok and pass_ok):
        logger.warning(
            "Admin login rejected from %s",
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=401, detail="Username atau password salah")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.jwt_ttl_seconds)
    token = jwt.encode(
        {
            "sub": settings.admin_username,
            "iss": "ecobot",
            "aud": "ecobot-admin",
            "iat": now,
            "exp": expires_at,
        },
        settings.api_secret_key,
        algorithm="HS256",
    )
    return TokenResponse(access_token=token, expires_in=settings.jwt_ttl_seconds)


@router.get("/me", response_model=AdminIdentity)
def identity(admin: AdminDep) -> AdminIdentity:
    return admin
