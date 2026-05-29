import re
from core.models.Student import DEPARTMENT_LIST, CS, WL, WY, SX, JJ, GL, DX, JX, FX, MS

def De_verify(fn):
    def inner(s, dict, *args, **kargs):
        is_valid = True
        if re.match(r'^\d{7}$', dict["student_id"]):
            pass
        else:
            print("该学号不合法")
            is_valid = False
        if dict["age"] > 15 and dict["age"] < 45:
            pass
        else:
            print("该年龄不合法")
            is_valid = False
        if dict["department"] in DEPARTMENT_LIST:
            pass
        else:
            print("该院系不合法")
            is_valid = False
        if is_valid:
            return fn(s, dict, *args, **kargs)
        else:
            print("该学生添加失败")
    return inner

def de_verify(fn):
    def inner(s, dict, *args, **kargs):
        is_valid = True
        if re.match(r'^\d{7}$', dict["student_id"]):
            pass
        else:
            is_valid = False
        if dict["age"] > 15 and dict["age"] < 45:
            pass
        else:
            is_valid = False
        if dict["department"] in DEPARTMENT_LIST:
            pass
        else:
            is_valid = False
        if is_valid:
            fn(s, dict, *args, **kargs)
        else:
            return False
    return inner

def De_repeat(fn):
    def inner(s, dict, *args, **kargs):
        student_id = str(dict["student_id"])
        if student_id in s.students_dict:
            print("该学生已存在")
        else:
            return fn(s, dict, *args, **kargs)
    return inner
