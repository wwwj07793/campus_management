from __future__ import annotations

from collections.abc import Callable

from fastapi import Header, HTTPException

from core.auth import AuthUser, decode_access_token


def get_current_user(authorization: str | None = Header(None)) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    token = authorization.split(" ", 1)[1].strip()
    try:
        return decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def require_roles(*allowed_roles: str) -> Callable[[str | None], AuthUser]:
    allowed = set(allowed_roles)

    def dependency(authorization: str | None = Header(None)) -> AuthUser:
        user = get_current_user(authorization)
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="当前角色无权执行此操作")
        return user

    return dependency
