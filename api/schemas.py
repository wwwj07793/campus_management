from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., pattern=r"^(student|teacher|admin)$")


class LoginUser(BaseModel):
    username: str
    role: str
    display_name: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: LoginUser

# ── Student ────────────────────────────────────────────────────────────────


class StudentCreate(BaseModel):
    student_id: str = Field(..., pattern=r"^\d{7}$", description="7位学号")
    name: str = Field(..., min_length=1, max_length=50)
    gender: str = Field(..., pattern=r"^(男|女)$")
    birth_date: date
    department: str = Field(..., min_length=1, max_length=50)
    grade: int = Field(..., ge=2000, le=2100)


class StudentUpdate(BaseModel):
    student_id: Optional[str] = Field(None, pattern=r"^\d{7}$")
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    gender: Optional[str] = Field(None, pattern=r"^(男|女)$")
    birth_date: Optional[date] = None
    department: Optional[str] = Field(None, min_length=1, max_length=50)
    grade: Optional[int] = Field(None, ge=2000, le=2100)

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        if all(v is None for v in self.__dict__.values()):
            raise ValueError("至少需要一个字段")
        return self


class StudentOut(BaseModel):
    student_id: str
    name: str
    gender: str
    birth_date: date
    department: str
    grade: int
    gpa: float

    model_config = {"from_attributes": True}


# ── Course ─────────────────────────────────────────────────────────────────


class CourseCreate(BaseModel):
    course_code: str = Field(..., pattern=r"^[A-Z]{2}\d{3}$")
    name: str = Field(..., min_length=1, max_length=100)
    credit: int = Field(..., gt=0)
    teacher: str = Field(..., min_length=1, max_length=50)
    schedule: str = Field(..., min_length=1, max_length=100)
    capacity: int = Field(..., gt=0)
    prerequisite_ids: Optional[list[int]] = None


class CourseUpdate(BaseModel):
    course_code: Optional[str] = Field(None, pattern=r"^[A-Z]{2}\d{3}$")
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    credit: Optional[int] = Field(None, gt=0)
    teacher: Optional[str] = Field(None, min_length=1, max_length=50)
    schedule: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(None, gt=0)

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        if all(v is None for v in self.__dict__.values()):
            raise ValueError("至少需要一个字段")
        return self


class CourseOut(BaseModel):
    id: int
    course_code: str
    name: str
    credit: int
    teacher: str
    schedule: str
    capacity: int
    current_count: int

    model_config = {"from_attributes": True}


# ── Enrollment ─────────────────────────────────────────────────────────────


class EnrollmentRequest(BaseModel):
    student_id: str = Field(..., pattern=r"^\d{7}$")
    course_code: str = Field(..., pattern=r"^[A-Z]{2}\d{3}$")
    teacher: str
    schedule: str


class EnrollmentOut(BaseModel):
    student_id: str
    course_code: str
    course_name: str
    teacher: str
    schedule: str

    model_config = {"from_attributes": True}


# ── Grade ──────────────────────────────────────────────────────────────────


class GradeCreate(BaseModel):
    student_id: str = Field(..., pattern=r"^\d{7}$")
    course_code: str = Field(..., pattern=r"^[A-Z]{2}\d{3}$")
    teacher: str
    schedule: str
    score: float = Field(..., ge=0, le=100)


class GradeOut(BaseModel):
    course_code: str
    course_name: str
    teacher: str
    schedule: str
    score: float

    model_config = {"from_attributes": True}


class StudentGradeOut(BaseModel):
    student_id: str
    student_name: str
    course_code: str
    course_name: str
    score: float

    model_config = {"from_attributes": True}


# ── Analytics ──────────────────────────────────────────────────────────────


class StudentCountsOut(BaseModel):
    total: int
    by_department: dict[str, int]
    by_grade: dict[int, int]


class TeacherStatsOut(BaseModel):
    teacher: str
    total_credit: int
    total_enrollments: int
    course_count: int
    enrollment_rate: float


class NumericStats(BaseModel):
    count: int
    max: Optional[float] = None
    min: Optional[float] = None
    average: Optional[float] = None
    std: Optional[float] = None
    var: Optional[float] = None
    pass_rate: Optional[float] = None
    excellent_rate: Optional[float] = None


class WarningStudent(BaseModel):
    student_id: str
    name: str
    department: str
    gpa: float
    failed_courses: int
