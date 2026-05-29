from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from core.models.base import Base


course_prerequisites = Table(
    "course_prerequisites",
    Base.metadata,
    Column(
        "course_id",
        Integer,
        ForeignKey("course.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "prerequisite_course_id",
        Integer,
        ForeignKey("course.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    CheckConstraint(
        "course_id <> prerequisite_course_id",
        name="ck_course_prerequisites_not_self",
    ),
)


class StudentDB(Base):
    __tablename__ = "student"
    __table_args__ = (
        CheckConstraint("gender IN ('男', '女')", name="ck_student_gender"),
        CheckConstraint("grade >= 2000 AND grade <= 2100", name="ck_student_grade"),
        CheckConstraint("gpa >= 0 AND gpa <= 4", name="ck_student_gpa_range"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    gender = Column(String(2), nullable=False)
    birth_date = Column(Date, nullable=False)
    department = Column(String(50), nullable=False, index=True)
    grade = Column(Integer, nullable=False, index=True)
    gpa = Column(Float, nullable=False, default=0.0)

    enrollments = relationship(
        "EnrollmentDB",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    grades = relationship(
        "GradeDB",
        back_populates="student",
        cascade="all, delete-orphan",
        overlaps="enrollment,grade",
    )
    courses = relationship(
        "CourseDB",
        secondary="enrollment",
        back_populates="students",
        viewonly=True,
    )


class UserDB(Base):
    __tablename__ = "app_user"
    __table_args__ = (
        CheckConstraint("role IN ('student', 'teacher', 'admin')", name="ck_user_role"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)
    display_name = Column(String(50), nullable=False)


class CourseDB(Base):
    __tablename__ = "course"
    __table_args__ = (
        UniqueConstraint(
            "course_code",
            "teacher",
            "schedule",
            name="uq_course_code_teacher_schedule",
        ),
        CheckConstraint("credit > 0", name="ck_course_credit_positive"),
        CheckConstraint("capacity > 0", name="ck_course_capacity_positive"),
        CheckConstraint("current_count >= 0", name="ck_course_current_count_non_negative"),
        CheckConstraint(
            "current_count <= capacity",
            name="ck_course_current_count_not_over_capacity",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_code = Column(String(20), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    credit = Column(Integer, nullable=False)
    teacher = Column(String(50), nullable=False, index=True)
    schedule = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    current_count = Column(Integer, nullable=False, default=0)

    enrollments = relationship(
        "EnrollmentDB",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    grades = relationship(
        "GradeDB",
        back_populates="course",
        cascade="all, delete-orphan",
        overlaps="enrollment,grade",
    )
    students = relationship(
        "StudentDB",
        secondary="enrollment",
        back_populates="courses",
        viewonly=True,
    )
    prerequisites = relationship(
        "CourseDB",
        secondary=course_prerequisites,
        primaryjoin=id == course_prerequisites.c.course_id,
        secondaryjoin=id == course_prerequisites.c.prerequisite_course_id,
        backref="dependent_courses",
    )


class EnrollmentDB(Base):
    __tablename__ = "enrollment"

    student_id = Column(
        Integer,
        ForeignKey("student.id", ondelete="CASCADE"),
        primary_key=True,
    )
    course_id = Column(
        Integer,
        ForeignKey("course.id", ondelete="CASCADE"),
        primary_key=True,
    )

    student = relationship("StudentDB", back_populates="enrollments")
    course = relationship("CourseDB", back_populates="enrollments")
    grade = relationship(
        "GradeDB",
        back_populates="enrollment",
        uselist=False,
        cascade="all, delete-orphan",
        overlaps="course,grades,student",
    )


class GradeDB(Base):
    __tablename__ = "grade"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_grade_student_course"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_grade_score_range"),
        ForeignKeyConstraint(
            ["student_id"],
            ["student.id"],
            ondelete="CASCADE",
            name="fk_grade_student",
        ),
        ForeignKeyConstraint(
            ["course_id"],
            ["course.id"],
            ondelete="CASCADE",
            name="fk_grade_course",
        ),
        ForeignKeyConstraint(
            ["student_id", "course_id"],
            ["enrollment.student_id", "enrollment.course_id"],
            ondelete="CASCADE",
            name="fk_grade_enrollment",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)

    __mapper_args__ = {"confirm_deleted_rows": False}

    student = relationship(
        "StudentDB",
        back_populates="grades",
        overlaps="enrollment,grade",
    )
    course = relationship(
        "CourseDB",
        back_populates="grades",
        overlaps="enrollment,grade",
    )
    enrollment = relationship(
        "EnrollmentDB",
        back_populates="grade",
        overlaps="course,grades,student",
    )
