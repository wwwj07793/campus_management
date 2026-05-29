from datetime import datetime
from core.exceptions.base_exc import (
    StudentNotExistException,
    CourseNotExistException,
    CourseConflictException,
    DateError,
    GradeError,
    GenderError,
    BusinessException
)

#验证合法性，抛出异常实例
def val_birth_date(birth_date, student_id):
    try:
        return datetime.strptime(birth_date, "%Y-%m-%d").date()
    except ValueError:
        raise DateError(student_id)

def val_gender(gender, student_id):
    if gender != "男" and gender != "女":
        raise GenderError(student_id)

def val_grade(grade, student_id):
    try:
        grade = int(grade)
    except (TypeError, ValueError):
        raise GradeError(student_id)
    if grade < 2000 or grade > 2100:
        raise GradeError(student_id)
    return grade
    
def st_val_dict(dict, student_id):
    gender = dict["gender"]
    if gender != "男" and gender != "女":
        raise GenderError(student_id)
    try:
        birth_date = dict["birth_date"]
        datetime.strptime(birth_date, "%Y-%m-%d")
    except:
        raise DateError(student_id)
    try:
        grade = int(dict["grade"])
    except (TypeError, ValueError):
        raise GradeError(student_id)
    if grade < 2000 or grade > 2100:
        raise GradeError(student_id)

