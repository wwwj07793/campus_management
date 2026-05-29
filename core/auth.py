from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass

from config import AUTH_SECRET

DEFAULT_TOKEN_TTL_SECONDS = 60 * 60 * 8
SECRET_KEY = AUTH_SECRET


@dataclass(frozen=True)
class AuthUser:
    username: str
    role: str
    display_name: str


def hash_password(password: str, salt: str | None = None) -> str:
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_value.encode("utf-8"),
        120_000,
    )
    return f"pbkdf2_sha256${salt_value}${base64.urlsafe_b64encode(digest).decode('ascii')}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt, expected = password_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    actual = hash_password(password, salt)
    return hmac.compare_digest(actual, password_hash)


def create_access_token(user: AuthUser, ttl_seconds: int = DEFAULT_TOKEN_TTL_SECONDS) -> str:
    payload = {
        "username": user.username,
        "role": user.role,
        "display_name": user.display_name,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_text = _b64(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    signature = _sign(payload_text)
    return f"{payload_text}.{signature}"


def decode_access_token(token: str) -> AuthUser:
    try:
        payload_text, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("令牌格式错误") from exc
    if not hmac.compare_digest(_sign(payload_text), signature):
        raise ValueError("令牌签名无效")

    payload = json.loads(_unb64(payload_text).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("登录已过期")
    return AuthUser(
        username=payload["username"],
        role=payload["role"],
        display_name=payload["display_name"],
    )


def _sign(payload_text: str) -> str:
    digest = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload_text.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64(digest)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)
