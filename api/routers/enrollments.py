from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from api.deps import Repos, get_repos, get_services
from api.errors import business_error_to_http, integrity_error_to_http
from api.security import require_roles
from api.schemas import EnrollmentOut, EnrollmentRequest, StudentOut
from core.services.backend_services import BackendServices

router = APIRouter(prefix="/api/enrollments", tags=["enrollments"])
any_user = require_roles("student", "teacher", "admin")


@router.post("", response_model=EnrollmentOut, status_code=201)
def enroll(
    data: EnrollmentRequest,
    _current_user=Depends(any_user),
    services: BackendServices = Depends(get_services),
):
    try:
        enrollment = services.enrollments.enroll(
            student_id=data.student_id,
            course_code_value=data.course_code,
            teacher=data.teacher,
            schedule=data.schedule,
        )
    except ValueError as e:
        raise business_error_to_http(e)
    except IntegrityError as e:
        raise integrity_error_to_http(e)

    course = enrollment.course
    return EnrollmentOut(
        student_id=enrollment.student.student_id,
        course_code=course.course_code,
        course_name=course.name,
        teacher=course.teacher,
        schedule=course.schedule,
    )


@router.delete("", status_code=204)
def drop(
    student_id: str = Query(..., pattern=r"^\d{7}$"),
    course_code: str = Query(..., pattern=r"^[A-Z]{2}\d{3}$"),
    teacher: str = Query(...),
    schedule: str = Query(...),
    _current_user=Depends(any_user),
    services: BackendServices = Depends(get_services),
):
    try:
        if not services.enrollments.drop(
            student_id=student_id,
            course_code_value=course_code,
            teacher=teacher,
            schedule=schedule,
        ):
            raise HTTPException(status_code=404, detail="选课记录不存在")
    except ValueError as e:
        raise business_error_to_http(e)
    except IntegrityError as e:
        raise integrity_error_to_http(e)


@router.post("/drop", status_code=204)
def drop_with_body(
    data: EnrollmentRequest,
    _current_user=Depends(any_user),
    services: BackendServices = Depends(get_services),
):
    try:
        if not services.enrollments.drop(
            student_id=data.student_id,
            course_code_value=data.course_code,
            teacher=data.teacher,
            schedule=data.schedule,
        ):
            raise HTTPException(status_code=404, detail="选课记录不存在")
    except ValueError as e:
        raise business_error_to_http(e)
    except IntegrityError as e:
        raise integrity_error_to_http(e)


@router.get("/students/{student_id}", response_model=list[EnrollmentOut])
def list_student_enrollments(
    student_id: str,
    _current_user=Depends(any_user),
    repos: Repos = Depends(get_repos),
):
    student = repos.student.get_by_student_id(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")

    enrollments = repos.enrollment.list_by_student_number(student_id)
    return [
        EnrollmentOut(
            student_id=student_id,
            course_code=e.course.course_code,
            course_name=e.course.name,
            teacher=e.course.teacher,
            schedule=e.course.schedule,
        )
        for e in enrollments
    ]


@router.get("/courses/{course_code}", response_model=list[StudentOut])
def list_course_students(
    course_code: str,
    _current_user=Depends(any_user),
    repos: Repos = Depends(get_repos),
):
    sections = repos.course.list_by_code(course_code)
    if not sections:
        raise HTTPException(status_code=404, detail="课程不存在")

    result: list[StudentOut] = []
    seen: set[str] = set()
    for section in sections:
        for e in repos.enrollment.list_by_course_id(section.id):
            if e.student.student_id not in seen:
                seen.add(e.student.student_id)
                result.append(e.student)
    return result
