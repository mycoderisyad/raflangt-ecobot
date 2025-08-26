import os
from functools import wraps
from flask import request, jsonify


def _load_valid_keys():
    raw = (
        os.getenv("ADMIN_API_KEYS")
        or os.getenv("API_KEYS")
        or os.getenv("ADMIN_API_KEY")
    )
    if not raw:
        return set()
    return set(k.strip() for k in raw.split(",") if k.strip())


def require_api_key(view_func):
    """Decorator that requires a valid API key in the request headers.

    Checks the following in order:
      - X-API-Key header
      - Authorization: ApiKey <key>
      - Authorization: Bearer <key>

    If no valid keys are configured on the server, returns 500 to indicate misconfiguration.
    """

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        valid_keys = _load_valid_keys()
        if not valid_keys:
            return (
                jsonify(
                    {"status": "error", "message": "Server API key not configured"}
                ),
                500,
            )

        # Try common headers
        auth = (
            request.headers.get("X-API-Key")
            or request.headers.get("X-API-KEY")
            or request.headers.get("Authorization")
        )
        key = None
        if auth:
            auth = auth.strip()
            # Authorization: ApiKey <key> or Bearer <key>
            parts = auth.split(None, 1)
            if len(parts) == 2 and parts[0].lower() in ("apikey", "bearer"):
                key = parts[1].strip()
            else:
                # header might be the raw key
                key = auth

        if not key or key not in valid_keys:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        return view_func(*args, **kwargs)

    return wrapped
