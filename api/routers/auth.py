from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import get_session
from api.schemas import LoginRequest, LoginResponse, LoginUser
from api.security import get_current_user
from core.auth import AuthUser, create_access_token, hash_password, verify_password
from core.models.mysqlDB import UserDB

router = APIRouter(prefix="/api/auth", tags=["auth"])

DEFAULT_USERS = [
    ("student", "student123", "student", "学生用户"),
    ("teacher", "teacher123", "teacher", "教师用户"),
    ("admin", "admin123", "admin", "系统管理员"),
]


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    ensure_auth_table(session)
    ensure_default_users(session)
    user = session.scalar(select(UserDB).where(UserDB.username == data.username))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.role != data.role:
        raise HTTPException(status_code=403, detail="登录身份与账号角色不匹配")

    auth_user = AuthUser(
        username=user.username,
        role=user.role,
        display_name=user.display_name,
    )
    return LoginResponse(
        access_token=create_access_token(auth_user),
        user=LoginUser(
            username=auth_user.username,
            role=auth_user.role,
            display_name=auth_user.display_name,
        ),
    )


@router.get("/me", response_model=LoginUser)
def me(current_user: AuthUser = Depends(get_current_user)):
    return LoginUser(
        username=current_user.username,
        role=current_user.role,
        display_name=current_user.display_name,
    )


def ensure_default_users(session: Session) -> None:
    for username, password, role, display_name in DEFAULT_USERS:
        exists = session.scalar(select(UserDB.id).where(UserDB.username == username))
        if exists is not None:
            continue
        session.add(UserDB(
            username=username,
            password_hash=hash_password(password),
            role=role,
            display_name=display_name,
        ))
    session.flush()


def ensure_auth_table(session: Session) -> None:
    UserDB.__table__.create(bind=session.get_bind(), checkfirst=True)
