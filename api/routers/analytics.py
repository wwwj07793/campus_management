from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import Repos, get_data_view, get_repos
from api.security import require_roles
from api.schemas import (
    NumericStats,
    StudentCountsOut,
    TeacherStatsOut,
    WarningStudent,
)
from core.interpretation.data_views import CampusDataView
from core.interpretation.statistics import gpa_statistics, score_statistics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
teacher_or_admin = require_roles("teacher", "admin")


@router.get("/overview", response_model=StudentCountsOut)
def overview(
    _current_user=Depends(teacher_or_admin),
    dv: CampusDataView = Depends(get_data_view),
):
    return dv.student_counts()


@router.get("/warnings", response_model=list[WarningStudent])
def warnings(
    _current_user=Depends(teacher_or_admin),
    repos: Repos = Depends(get_repos),
    dv: CampusDataView = Depends(get_data_view),
):
    result: list[WarningStudent] = []
    for student in repos.student.list_all():
        grades = repos.grade.list_by_student_id(student.id)
        failed = sum(1 for g in grades if g.score < 60)
        if failed > 0 or student.gpa < 2.0:
            result.append(WarningStudent(
                student_id=student.student_id,
                name=student.name,
                department=student.department,
                gpa=round(student.gpa, 2),
                failed_courses=failed,
            ))
    return result


@router.get("/gpa-distribution", response_model=NumericStats)
def gpa_distribution(
    department: str | None = None,
    grade: int | None = None,
    _current_user=Depends(teacher_or_admin),
    dv: CampusDataView = Depends(get_data_view),
):
    departments = [department] if department else None
    grades = [grade] if grade else None
    gpas = dv.gpas_for_scope(departments=departments, grades=grades)
    return gpa_statistics(gpas)


@router.get("/score-distribution", response_model=NumericStats)
def score_distribution(
    course_code: str,
    department: str | None = None,
    grade: int | None = None,
    _current_user=Depends(teacher_or_admin),
    dv: CampusDataView = Depends(get_data_view),
):
    departments = [department] if department else None
    grades_list = [grade] if grade else None
    scores = dv.scores_for_course(course_code, departments=departments, grades=grades_list)
    return score_statistics(scores)


@router.get("/teacher-statistics", response_model=list[TeacherStatsOut])
def teacher_statistics(
    _current_user=Depends(teacher_or_admin),
    dv: CampusDataView = Depends(get_data_view),
):
    stats = dv.teacher_statistics()
    return [
        TeacherStatsOut(
            teacher=teacher,
            total_credit=data[0],
            total_enrollments=data[1],
            course_count=data[2],
            enrollment_rate=round(data[3], 4),
        )
        for teacher, data in stats.items()
    ]
