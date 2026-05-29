from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError


def business_error_to_http(error: ValueError) -> HTTPException:
    message = str(error)
    status_code = getattr(error, "status_code", None)
    if isinstance(status_code, int):
        return HTTPException(status_code=status_code, detail=message)
    if "不存在" in message:
        return HTTPException(status_code=404, detail=message)
    if "已存在" in message or "已经" in message or "重复" in message:
        return HTTPException(status_code=409, detail=message)
    return HTTPException(status_code=400, detail=message)


def integrity_error_to_http(error: IntegrityError) -> HTTPException:
    message = str(error.orig) if getattr(error, "orig", None) is not None else str(error)
    if "UNIQUE" in message.upper() or "DUPLICATE" in message.upper():
        return HTTPException(status_code=409, detail="数据已存在或违反唯一约束")
    if "FOREIGN KEY" in message.upper():
        return HTTPException(status_code=400, detail="关联数据不存在或违反外键约束")
    return HTTPException(status_code=400, detail="数据违反数据库约束")
