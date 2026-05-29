"""version one

Revision ID: 4a191847e3e9
Revises:
Create Date: 2026-03-22 17:56:28.659708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4a191847e3e9"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("credit", sa.Integer(), nullable=False),
        sa.Column("teacher", sa.String(length=50), nullable=False),
        sa.Column("schedule", sa.String(length=100), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("current_count", sa.Integer(), nullable=False),
        sa.CheckConstraint("capacity > 0", name="ck_course_capacity_positive"),
        sa.CheckConstraint(
            "current_count >= 0",
            name="ck_course_current_count_non_negative",
        ),
        sa.CheckConstraint(
            "current_count <= capacity",
            name="ck_course_current_count_not_over_capacity",
        ),
        sa.CheckConstraint("credit > 0", name="ck_course_credit_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "course_code",
            "teacher",
            "schedule",
            name="uq_course_code_teacher_schedule",
        ),
    )
    op.create_index(op.f("ix_course_course_code"), "course", ["course_code"])
    op.create_index(op.f("ix_course_teacher"), "course", ["teacher"])

    op.create_table(
        "student",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("gender", sa.String(length=2), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("department", sa.String(length=50), nullable=False),
        sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("gpa", sa.Float(), nullable=False),
        sa.CheckConstraint("gender IN ('男', '女')", name="ck_student_gender"),
        sa.CheckConstraint("gpa >= 0 AND gpa <= 4", name="ck_student_gpa_range"),
        sa.CheckConstraint("grade >= 2000 AND grade <= 2100", name="ck_student_grade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id"),
    )
    op.create_index(op.f("ix_student_department"), "student", ["department"])
    op.create_index(op.f("ix_student_grade"), "student", ["grade"])
    op.create_index(op.f("ix_student_student_id"), "student", ["student_id"])

    op.create_table(
        "course_prerequisites",
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("prerequisite_course_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "course_id <> prerequisite_course_id",
            name="ck_course_prerequisites_not_self",
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["course.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["prerequisite_course_id"],
            ["course.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("course_id", "prerequisite_course_id"),
    )

    op.create_table(
        "enrollment",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["course.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["student.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("student_id", "course_id"),
    )

    op.create_table(
        "grade",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_grade_score_range"),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["course.id"],
            name="fk_grade_course",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id", "course_id"],
            ["enrollment.student_id", "enrollment.course_id"],
            name="fk_grade_enrollment",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["student.id"],
            name="fk_grade_student",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "course_id", name="uq_grade_student_course"),
    )


def downgrade() -> None:
    op.drop_table("grade")
    op.drop_table("enrollment")
    op.drop_table("course_prerequisites")
    op.drop_index(op.f("ix_student_student_id"), table_name="student")
    op.drop_index(op.f("ix_student_grade"), table_name="student")
    op.drop_index(op.f("ix_student_department"), table_name="student")
    op.drop_table("student")
    op.drop_index(op.f("ix_course_teacher"), table_name="course")
    op.drop_index(op.f("ix_course_course_code"), table_name="course")
    op.drop_table("course")
