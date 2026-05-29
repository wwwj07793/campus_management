from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from api.deps import Repos, get_repos, get_services
from api.errors import business_error_to_http, integrity_error_to_http
from api.security import require_roles
from api.schemas import GradeCreate, GradeOut, StudentGradeOut
from core.services.backend_services import BackendServices

router = APIRouter(prefix="/api/grades", tags=["grades"])
any_user = require_roles("student", "teacher", "admin")
teacher_or_admin = require_roles("teacher", "admin")


def _build_grade_out(grade) -> GradeOut:
    return GradeOut(
        course_code=grade.course.course_code,
        course_name=grade.course.name,
        teacher=grade.course.teacher,
        schedule=grade.course.schedule,
        score=grade.score,
    )


def _record_grade(data: GradeCreate, services: BackendServices) -> GradeOut:
    try:
        grade = services.grades.record_grade(
            student_id=data.student_id,
            course_code_value=data.course_code,
            teacher=data.teacher,
            schedule=data.schedule,
            score=data.score,
        )
    except ValueError as e:
        raise business_error_to_http(e)
    except IntegrityError as e:
        raise integrity_error_to_http(e)
    return _build_grade_out(grade)


@router.post("", response_model=GradeOut, status_code=201)
def record_grade(
    data: GradeCreate,
    _current_user=Depends(teacher_or_admin),
    services: BackendServices = Depends(get_services),
):
    return _record_grade(data, services)


@router.put("", response_model=GradeOut)
def update_grade(
    data: GradeCreate,
    _current_user=Depends(teacher_or_admin),
    services: BackendServices = Depends(get_services),
):
    return _record_grade(data, services)


@router.delete("", status_code=204)
def delete_grade(
    student_id: str = Query(..., pattern=r"^\d{7}$"),
    course_code: str = Query(..., pattern=r"^[A-Z]{2}\d{3}$"),
    teacher: str = Query(...),
    schedule: str = Query(...),
    _current_user=Depends(teacher_or_admin),
    services: BackendServices = Depends(get_services),
):
    try:
        deleted = services.grades.delete_grade(
            student_id=student_id,
            course_code_value=course_code,
            teacher=teacher,
            schedule=schedule,
        )
    except ValueError as e:
        raise business_error_to_http(e)
    except IntegrityError as e:
        raise integrity_error_to_http(e)
    if not deleted:
        raise HTTPException(status_code=404, detail="成绩不存在")


@router.get("/students/{student_id}", response_model=list[GradeOut])
def list_student_grades(
    student_id: str,
    _current_user=Depends(any_user),
    repos: Repos = Depends(get_repos),
):
    if repos.student.get_by_student_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")

    grades = repos.grade.list_by_student_number(student_id)
    return [_build_grade_out(g) for g in grades]


@router.get("/courses/{course_code}", response_model=list[StudentGradeOut])
def list_course_grades(
    course_code: str,
    _current_user=Depends(any_user),
    repos: Repos = Depends(get_repos),
):
    sections = repos.course.list_by_code(course_code)
    if not sections:
        raise HTTPException(status_code=404, detail="课程不存在")

    result: list[StudentGradeOut] = []
    for section in sections:
        for g in repos.grade.list_by_course_id(section.id):
            result.append(StudentGradeOut(
                student_id=g.student.student_id,
                student_name=g.student.name,
                course_code=section.course_code,
                course_name=section.name,
                score=g.score,
            ))
    return result
