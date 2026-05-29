from __future__ import annotations

from core.auth import AuthUser, create_access_token


def auth_headers(role: str = "teacher", username: str | None = None) -> dict[str, str]:
    display_names = {
        "student": "学生用户",
        "teacher": "教师用户",
        "admin": "系统管理员",
    }
    user = AuthUser(
        username=username or role,
        role=role,
        display_name=display_names.get(role, role),
    )
    return {"Authorization": f"Bearer {create_access_token(user)}"}
