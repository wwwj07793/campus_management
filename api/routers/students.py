from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError

from api.deps import get_services
from api.errors import business_error_to_http, integrity_error_to_http
from api.security import require_roles
from api.schemas import StudentCreate, StudentOut, StudentUpdate
from core.services.backend_services import BackendServices

router = APIRouter(prefix="/api/students", tags=["students"])
teacher_or_admin = require_roles("teacher", "admin")


@router.post("", response_model=StudentOut, status_code=201)
def create_student(
    data: StudentCreate,
    _current_user=Depends(teacher_or_admin),
    services: BackendServices = Depends(get_services),
):
    try:
        student = services.students.create_student(
            student_id=data.student_id,
            name=data.name,
            gender=data.gender,
            birth_date=data.birth_date,
            department=data.department,
            grade=data.grade,
        )
    except ValueError as e:
        raise business_error_to_http(e)
    except IntegrityError as e:
        raise integrity_error_to_http(e)
    return student


@router.get("", response_model=list[StudentOut])
def list_students(
    student_id: str | None = None,
    name: str | None = None,
    department: str | None = None,
    grade: int | None = None,
    _current_user=Depends(teacher_or_admin),
    services: BackendServices = Depends(get_services),
):
    return services.students.search_students(
        student_id=student_id,
        name=name,
        department=department,
        grade=grade,
    )


@router.get("/{student_id}", response_model=StudentOut)
def get_student(
    student_id: str,
    _current_user=Depends(teacher_or_admin),
    services: BackendServices = Depends(get_services),
):
    student = services.students.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student


@router.put("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: str,
    data: StudentUpdate,
    _current_user=Depends(teacher_or_admin),
    services: BackendServices = Depends(get_services),
):
    fields = data.model_dump(exclude_none=True)
    try:
        student = services.students.update_student(student_id, **fields)
    except ValueError as e:
        raise business_error_to_http(e)
    except IntegrityError as e:
        raise integrity_error_to_http(e)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student


@router.delete("/{student_id}", status_code=204)
def delete_student(
    student_id: str,
    _current_user=Depends(teacher_or_admin),
    services: BackendServices = Depends(get_services),
):
    if not services.students.delete_student(student_id):
        raise HTTPException(status_code=404, detail="学生不存在")
