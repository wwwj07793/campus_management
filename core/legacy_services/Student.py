import csv
import re
from datetime import date, datetime
from core.models.Student import Student
from core.interpretation.data_views import CampusDataView
from core.interpretation import student_analysis
from core.interpretation.statistics import print_gpa_statistics, print_score_statistics
from core.models.Student import DEPARTMENT_LIST, CS, WL, WY, SX, JJ, GL, DX, JX, FX, MS, GRADE_LIST, FI, SE, TH, FO
from utils.decorators.decorators import De_verify, De_repeat, de_verify
from utils.validators import val_gender, val_birth_date, val_grade, val_dict
from core.exceptions.base_exc import (

    StudentNotExistException,
    CourseNotExistException,
    CourseConflictException,
    DateError,
    GradeError,
    GenderError,
    BusinessException
)

def caculate_output(scores_list):
    return print_score_statistics(scores_list)


def gpa_caculate_output(gpas_list):
    return print_gpa_statistics(gpas_list)


class StudentManage:
    students_dict = {}

    @classmethod
    def data_view(s):
        from .Course import CourseManage
        return CampusDataView(s.students_dict, CourseManage.all_courses_dict)

    @classmethod
    def st_inout(s):
        student_id = input("请输入学号: ").strip()
        name = input("请输入姓名: ").strip()
        try:
            gender = input("请输入性别(男/女): ")
            val_gender(gender, student_id)
        except GenderError as g:
            print(f"{g.core}, {g.message}")
            is_valid = False
        try:
            birth_date = input("请输入生日(2000-01-01): ").strip()
            birth_date = val_birth_date(birth_date, student_id)
            current_date = date.today()
            age = current_date.year - birth_date.year
            if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
                age -= 1
        except DateError as d:
            print(f"{d.core}, {d.message}")
            is_valid = False
        try:
            grade = input("请输入年级(2025): ").strip()
            grade = val_grade(grade, student_id)
        except GradeError as g:
            print(f"{g.core}, {g.message}")
            is_valid = False
        department = input("请输入院系: ").strip()
        return {
            "student_id": student_id,
            "name": name,
            "gender": gender,
            "age": age,
            "birth_date": birth_date,
            "department": department,
            "grade": grade,
        }

    @De_repeat
    @De_verify
    def st_add(s, dict):
        student_id = str(dict["student_id"])
        student = Student(dict["student_id"], dict["name"], dict["gender"],
                          dict["birth_date"], dict["department"], dict["grade"])
        s.students_dict[student_id] = student
        print("学生添加成功")

    @de_verify
    def val_decora(s, dict):
        return True

    def st_add_generator(s, file_path):
        with open(file_path, 'r', encoding='utf8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if s.val_decora(row):
                    try:
                        student_id = row.get("student_id")
                        val_dict(row, student_id)
                        # 重写装饰器，对齐异常处理
                        yield Student(student_id=row["student_id"],  name=row["name"], department=row["department"], gender=row["gender"], birth_date=row["birth_date"], grade=row["grade"])
                    except BusinessException as b:
                        yield b
                else:
                    yield student_id

    def st_adds(s, file_path):
        success_count = 0
        fail_count = 0
        fail_detail = {}
        for index, data in enumerate(s.st_add_generator(file_path), 1):
            if isinstance(data, Student):
                s.students_dict[str(data.student_id)] = data
                success_count += 1
            else:
                fail_count += 1
                fail_detail[str(index)] = data
        print(f"导入成功{success_count}个学生， 导入失败{fail_count}个学生")
        print(f"失败细节如下：")
        for index in fail_detail:
            data = fail_detail[index]
            if isinstance(data, BusinessException):
                print(data.error_detail(
                    index, data.student_id))
            else:
                print(f"第{index}行学号为{data}的同学导入失败")

    def st_co_find(s):
        if s.students_dict:
            count = 0
            find_dict = {}
            result_list = []
            print("请输入筛选条件，可直接按空格跳过某条件")
            while True:
                student_id = str(input("学号: ").strip())
                if student_id:
                    if re.match(r"^\d{7}$", student_id):
                        find_dict["student_id"] = student_id
                        break
                    else:
                        print("学号不合法")
                        continue
                else:
                    break
            name = input("姓名: ").strip()
            if name:
                find_dict["name"] = name
            else:
                pass
            while True:
                gender = input("性别: ").strip()
                if gender:
                    if gender == '男' or gender == '女':
                        find_dict["gender"] = gender
                        break
                    else:
                        print("性别不合法")
                        continue
                else:
                    break
            while True:
                birth_date = input("生日: ").strip()
                if birth_date:
                    try:
                        pre_date = datetime.strptime(
                            birth_date, "%Y-%m-%d").date()
                    except ValueError:
                        print("生日格式不合法")
                        continue
                    else:
                        find_dict["birth_date"] = birth_date
                        break
                else:
                    break
            while True:
                department = input("院系: ").strip()
                if department:
                    if department in DEPARTMENT_LIST:
                        find_dict["department"] = department
                        break
                    else:
                        print("院系不合法")
                        continue
                else:
                    break
            while True:
                grade = input("年级：")
                if grade:
                    if grade in GRADE_LIST:
                        find_dict["grade"] = grade
                        break
                    else:
                        print("年级不合法")
                        continue
                else:
                    break
            if find_dict:
                for student_id, student in s.students_dict.items():
                    if ("student_id" not in find_dict or student.student_id == find_dict["student_id"]) and ("name" not in find_dict or student.name == find_dict["name"]) and ("gender" not in find_dict or student.gender == find_dict["gender"]) and ("birth_date" not in find_dict or student.age == find_dict["birth_date"]) and ("department" not in find_dict or student.department == find_dict["department"] and ("grade" not in find_dict or student.grade == find_dict["grade"])):
                        result_list.append((student.student_id, student.name, student.gender,
                                            student.birth_date, student.grade, student.department))
                        count += 1
                print(f"共查询到{count}条记录, 如下: ")
                for student in result_list:
                    print(f"{student}")
        else:
            print("暂时还无学生数据，请先添加学生数据")

    def st_delete(s):
        if s.students_dict:
            while True:
                print("请输入要删除学生的学号: ")
                student_id = str(input().strip())
                if student_id:
                    if re.match(r"^\d{7}$", student_id):
                        if student_id not in s.students_dict:
                            print("学号不存在")
                            continue
                        else:
                            break
                    else:
                        print("学号格式不合法")
                        continue
                else:
                    return
            del s.students_dict[student_id]
        else:
            print("暂时还无学生数据，请先添加学生数据")

    def st_dim_find(s):
        if s.students_dict:
            count = 0
            find_dict = {}
            result_list = []
            print("请输入筛选条件(学号,姓名,院系)，可直接按空格跳过某条件: ")
            while True:
                student_id = input("学号: ").strip()
                if student_id:
                    if re.match(r'^\d{1,7}$', student_id):
                        find_dict["student_id"] = student_id
                        break
                    else:
                        print("学号不合法")
                        continue
                else:
                    break
            name = input("姓名: ")
            if name:
                find_dict["name"] = name
            else:
                pass
            while True:
                department = input("院系: ").strip()
                if department:
                    if re.match(r'^[\u4e00-\u9fa5]$', department):
                        find_dict["department"] = department
                        break
                    else:
                        print("院系不合法")
                        continue
                else:
                    break
            if find_dict:
                for student_id, student in s.students_dict.items():
                    if ("student_id" not in find_dict or re.search(rf'\d*{find_dict["student_id"]}\d*', student.student_id)) and ("name" not in find_dict or re.search(rf'*{re.escape(find_dict["name"])}*', student.name)) and ("department" not in find_dict or re.search(rf'*{find_dict["department"]}*', student.department)):
                        result_list.append((student.student_id, student.name, student.gender,
                                            student.birth_date, student.grade, student.department))
                        count += 1
                print(f"共查询到{count}条记录, 如下: ")
                for student in result_list:
                    print(f"{student}")
        else:
            print("暂时还无学生数据，请先添加学生数据")

    def st_modify(s):
        if s.students_dict:
            while True:
                print("请输入要改学生的学号: ")
                student_id = str(input().strip())
                if student_id:
                    if re.match(r"^\d{7}$", student_id):
                        if student_id not in s.students_dict:
                            print("学号不存在")
                            continue
                        else:
                            break
                    else:
                        print("学号格式不合法")
                        continue
                else:
                    return
            while True:
                print("请输入要修改的模块: ")
                model = input().strip()
                if model:
                    if model in ["姓名", "名字", "学号", "性别", "生日", "院系", "年级"]:
                        break
                    else:
                        continue
                else:
                    break
            if model == "姓名" or model == "名字":
                re_name = input().strip()
                s.students_dict[student_id].name = re_name
            elif model == "学号":
                while True:
                    re_student_id = str(input("请输入改变后的学号: ").strip())
                    if re_student_id:
                        if re.match(r"^\d{7}$", re_student_id):
                            name = s.students_dict[student_id].name
                            gender = s.students_dict[student_id].gender
                            birth_date = s.students_dict[student_id].birth_date
                            department = s.students_dict[student_id].department
                            grade = s.students_dict[student_id].grade
                            student = Student(re_student_id, name,
                                              gender, birth_date, department, grade)
                            del s.students_dict[student_id]
                            s.students_dict[re_student_id] = student
                            print("修改成功")
                            break
                        else:
                            print("学号不合法")
                            continue
                    else:
                        break
            elif model == "性别":
                while True:
                    re_gender = input().strip()
                    if re_gender:
                        if re_gender == '男' or re_gender == '女':
                            s.students_dict[student_id].gender = re_gender
                            print("修改成功")
                            break
                        else:
                            print("性别不合法")
                            continue
                    else:
                        break
            elif model == "生日":
                while True:
                    re_birth_date = input().strip()
                    if re_birth_date:
                        try:
                            pre_date = datetime.strptime(
                                re_birth_date, "%Y-%m-%d").date()
                        except ValueError:
                            print("生日格式不合法(2000-01-01)")
                        else:
                            current_date = date.today()
                            re_age = current_date.year - pre_date.year
                            if (current_date.month, current_date.day) < (pre_date.month, pre_date.day):
                                re_age -= 1
                                if re_age > 15 and re_age < 45:
                                    s.students_dict[student_id].birth_date = re_birth_date
                                    print("修改成功")
                                    break
                                else:
                                    print("年龄不合法")
                                    continue
                    else:
                        break
            elif model == "院系":
                while True:
                    re_department = input().strip()
                    if re_department:
                        if re_department in DEPARTMENT_LIST:
                            s.students_dict[student_id].department = re_department
                            print("修改成功")
                            break
                        else:
                            print("院系不合法")
                            continue
                    else:
                        break
            elif model == "年级":
                while True:
                    re_grade = input().strip()
                    if re_grade:
                        if re_grade in GRADE_LIST:
                            s.students_dict[student_id].grade = re_grade
                            print("修改成功")
                            break
                        else:
                            print("年级不合法")
                            continue
                    else:
                        break

            else:
                print("模块名不合法，请输入：学号，姓名，性别，年龄，院系，年级")
        else:
            print("暂时还无学生数据，请先添加学生数据")

    def num_stat(s):
        return student_analysis.num_stat(s)

    def st_stat(s):
        return student_analysis.st_stat(s)

    def find_stat(s, total):
        return student_analysis.find_stat(s, total)

    def g_d_nu_statc(s):
        return student_analysis.g_d_nu_statc(s)

    def g_d_input(s):
        return student_analysis.g_d_input()

    def d_g_range(s, d_g_dict):
        return student_analysis.d_g_range(s, d_g_dict)
    def id_input(s, course_id_dict):
        return student_analysis.id_input(course_id_dict)

    def get_d_g_store(s, find_list, course_id_dict):
        return student_analysis.get_d_g_store(find_list, course_id_dict)

    def d_g_score_stat(s):
        return student_analysis.d_g_score_stat(s)

    def all_get_d_g_store(s, course_id_dict):
        return student_analysis.all_get_d_g_store(course_id_dict)

    def all_d_g_score_stat(s):
        return student_analysis.all_d_g_score_stat(s)
# 加上gpa统计分析

    def get_d_g_store_gpa(s, d_g_dict):
        return student_analysis.get_d_g_store_gpa(s, d_g_dict)

    def d_g_gpa_stat(s):
        return student_analysis.d_g_gpa_stat(s)

