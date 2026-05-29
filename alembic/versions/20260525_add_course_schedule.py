"""add course schedule to existing databases

Revision ID: 20260525_add_course_schedule
Revises: 4a191847e3e9
Create Date: 2026-05-25
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260525_add_course_schedule"
down_revision: Union[str, Sequence[str], None] = "4a191847e3e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _unique_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {
        constraint["name"]
        for constraint in inspector.get_unique_constraints(table_name)
        if constraint.get("name")
    }


def _index_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {
        index["name"]
        for index in inspector.get_indexes(table_name)
        if index.get("name")
    }


def upgrade() -> None:
    if "schedule" not in _column_names("course"):
        op.add_column(
            "course",
            sa.Column(
                "schedule",
                sa.String(length=100),
                nullable=False,
                server_default="未安排",
            ),
        )
        op.alter_column("course", "schedule", server_default=None)

    unique_names = _unique_names("course")
    if "course_code" in unique_names:
        op.drop_constraint("course_code", "course", type_="unique")

    if "uq_course_code_teacher_schedule" not in _unique_names("course"):
        op.create_unique_constraint(
            "uq_course_code_teacher_schedule",
            "course",
            ["course_code", "teacher", "schedule"],
        )

    if "ix_course_course_code" not in _index_names("course"):
        op.create_index("ix_course_course_code", "course", ["course_code"])

    if "ix_course_teacher" not in _index_names("course"):
        op.create_index("ix_course_teacher", "course", ["teacher"])


def downgrade() -> None:
    if "uq_course_code_teacher_schedule" in _unique_names("course"):
        op.drop_constraint("uq_course_code_teacher_schedule", "course", type_="unique")
    if "ix_course_course_code" in _index_names("course"):
        op.drop_index("ix_course_course_code", table_name="course")
    if "ix_course_teacher" in _index_names("course"):
        op.drop_index("ix_course_teacher", table_name="course")
    if "schedule" in _column_names("course"):
        op.drop_column("course", "schedule")
    if "course_code" not in _unique_names("course"):
        op.create_unique_constraint("course_code", "course", ["course_code"])
