from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from api.deps import Repos, get_repos, get_services
from api.errors import business_error_to_http, integrity_error_to_http
from api.security import require_roles
from api.schemas import CourseCreate, CourseOut, CourseUpdate
from core.services.backend_services import BackendServices

router = APIRouter(prefix="/api/courses", tags=["courses"])
any_user = require_roles("student", "teacher", "admin")
teacher_or_admin = require_roles("teacher", "admin")


@router.post("", response_model=CourseOut, status_code=201)
def create_course(
    data: CourseCreate,
    _current_user=Depends(teacher_or_admin),
    services: BackendServices = Depends(get_services),
):
    try:
        course = services.courses.create_course(
            course_code=data.course_code,
            name=data.name,
            credit=data.credit,
            teacher=data.teacher,
            schedule=data.schedule,
            capacity=data.capacity,
            prerequisite_ids=data.prerequisite_ids,
        )
    except ValueError as e:
        raise business_error_to_http(e)
    except IntegrityError as e:
        raise integrity_error_to_http(e)
    return course


@router.get("", response_model=list[CourseOut])
def list_courses(
    code: str | None = Query(None, alias="code"),
    teacher: str | None = Query(None, alias="teacher"),
    _current_user=Depends(any_user),
    repos: Repos = Depends(get_repos),
):
    if code:
        return repos.course.list_by_code(code)
    if teacher:
        return repos.course.list_by_teacher(teacher)
    return repos.course.list_all()


@router.get("/{course_id}", response_model=CourseOut)
def get_course(
    course_id: int,
    _current_user=Depends(any_user),
    repos: Repos = Depends(get_repos),
):
    course = repos.course.get_by_id(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


@router.put("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    data: CourseUpdate,
    _current_user=Depends(teacher_or_admin),
    services: BackendServices = Depends(get_services),
):
    fields = data.model_dump(exclude_none=True)
    try:
        course = services.courses.update_course(course_id, **fields)
    except ValueError as e:
        raise business_error_to_http(e)
    except IntegrityError as e:
        raise integrity_error_to_http(e)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


@router.delete("/{course_id}", status_code=204)
def delete_course(
    course_id: int,
    _current_user=Depends(teacher_or_admin),
    services: BackendServices = Depends(get_services),
):
    try:
        deleted = services.courses.delete_course(course_id)
    except ValueError as e:
        raise business_error_to_http(e)
    except IntegrityError as e:
        raise integrity_error_to_http(e)
    if not deleted:
        raise HTTPException(status_code=404, detail="课程不存在")
