import re
from collections import defaultdict

from core.models.Student import DEPARTMENT_LIST, GRADE_LIST
from core.interpretation.input_helpers import choose_dimension, choose_many
from core.interpretation.statistics import print_gpa_statistics, print_score_statistics


def _student_object(student, students):
    if hasattr(student, "enrolled_courses"):
        return student
    return students.get(str(student))


def departments_for_course(data_view, course_id):
    departments = set()
    for course in data_view.courses.get(str(course_id), []):
        for student in course.enrolled_students:
            student_obj = _student_object(student, data_view.students)
            if student_obj is not None:
                departments.add(student_obj.department)
    return departments


def grades_for_course(data_view, course_id, departments=None):
    grades = set()
    departments = set(departments or [])
    for course in data_view.courses.get(str(course_id), []):
        for student in course.enrolled_students:
            student_obj = _student_object(student, data_view.students)
            if student_obj is None:
                continue
            if departments and student_obj.department not in departments:
                continue
            grades.add(student_obj.grade)
    return grades


def teachers_for_course(data_view, course_id):
    return {
        course.teacher
        for course in data_view.courses.get(str(course_id), [])
    }


def scores_for_course_by_scope(data_view, course_id, departments=None, grades=None):
    scores = []
    departments = set(departments or [])
    grades = set(grades or [])

    for course in data_view.courses.get(str(course_id), []):
        for student in course.enrolled_students:
            student_obj = _student_object(student, data_view.students)
            if student_obj is None:
                continue
            if departments and student_obj.department not in departments:
                continue
            if grades and student_obj.grade not in grades:
                continue
            scores.append(student_obj.enrolled_courses.get(str(course_id)))
    return scores


def students_by_teacher_for_course(data_view, course_id):
    teacher_students = defaultdict(list)
    for course in data_view.courses.get(str(course_id), []):
        for student in course.enrolled_students:
            student_obj = _student_object(student, data_view.students)
            if student_obj is not None:
                teacher_students[course.teacher].append(student_obj)
    return teacher_students


def scores_for_course_by_teachers(data_view, course_id, teachers):
    scores = []
    teachers = set(teachers or [])
    for teacher, students in students_by_teacher_for_course(data_view, course_id).items():
        if teachers and teacher not in teachers:
            continue
        for student in students:
            scores.append(student.enrolled_courses.get(str(course_id)))
    return scores


def gpas_by_scope(data_view, departments=None, grades=None):
    return data_view.gpas_for_scope(departments=departments, grades=grades)


def gpas_by_teachers(data_view, teachers):
    gpas = []
    teachers = set(teachers or [])
    for teacher in teachers:
        for course in data_view.courses_by_teacher().get(teacher, []):
            for student in course.enrolled_students:
                student_obj = _student_object(student, data_view.students)
                if student_obj is not None:
                    gpas.append(student_obj.gpa)
    return gpas


def input_id():
    course_id = input("请输入您想查询的课程id：").strip()
    if not re.match(r"^[A-Z]{2}\d{3}$", course_id):
        print("课程id不合法")
        return None
    return course_id


def d_range(manager, course_id):
    return departments_for_course(manager.data_view(), course_id)


def g_range(manager, course_id, department_list):
    return grades_for_course(manager.data_view(), course_id, department_list)


def input_d_for_course(manager, course_id, department_set):
    find_dict = {}
    departments = choose_many(
        "院系",
        department_set,
        "请选择您想查询的院系，可按空格跳过院系选择(院系A, 院系B, ...)：",
    )
    if departments:
        find_dict["department"] = departments

    grades = g_range(manager, course_id, find_dict.get("department", department_set))
    if not grades:
        print("未找到对应的年级")
        return find_dict

    selected_grades = choose_many(
        "年级",
        grades,
        "请选择您想查询的年级，可按空格跳过年级选择：",
    )
    if selected_grades:
        find_dict["grade"] = selected_grades
    return find_dict


def get_d_g_score(manager, course_id, find_dict):
    scores = scores_for_course_by_scope(
        manager.data_view(),
        course_id,
        departments=find_dict.get("department"),
        grades=find_dict.get("grade"),
    )
    departments = find_dict.get("department")
    grades = find_dict.get("grade")
    if departments and grades:
        print(f"{','.join(departments)}第{','.join(map(str, grades))}该课程的成绩统计分析如下：")
    elif departments:
        print(f"{','.join(departments)}该课程的成绩统计分析如下：")
    elif grades:
        print(f"{','.join(map(str, grades))}该课程的成绩统计分析如下：")
    return scores


def caculate_output(score_list):
    return print_score_statistics(score_list)


def t_range(manager, course_id):
    return students_by_teacher_for_course(manager.data_view(), course_id)


def input_t(course_id, teacher_students):
    return choose_many(
        "教师",
        teacher_students.keys(),
        "请输入您想查询的教师(教师1, 教师2, 教师3...)：",
    )


def get_t_score(find_list, teacher_students):
    scores = []
    for teacher in find_list:
        for student in teacher_students[teacher]:
            scores.extend(student.enrolled_courses.values())
    print(f"{','.join(find_list)}该课程的成绩统计分析如下：")
    return scores


def course_score_stat(manager):
    course_id = input_id()
    if not course_id:
        return
    dimension = choose_dimension(
        ["学院和年级", "教师"],
        "请输入您想查询的维度(学院和年级/教师)：",
    )
    if not dimension:
        return

    if dimension == "学院和年级":
        departments = d_range(manager, course_id)
        if not departments:
            print("未找到对应的院系")
            return
        find_dict = input_d_for_course(manager, course_id, departments)
        scores = get_d_g_score(manager, course_id, find_dict)
    else:
        teacher_students = t_range(manager, course_id)
        if not teacher_students:
            print("未找到对应教师")
            return
        teachers = input_t(course_id, teacher_students)
        if not teachers:
            return
        scores = scores_for_course_by_teachers(
            manager.data_view(), course_id, teachers)

    if scores:
        return caculate_output(scores)
    print("分数统计分析失败")


def input_d(manager=None, course_id=None, department_set=None):
    if manager is not None and course_id is not None and department_set is not None:
        return input_d_for_course(manager, course_id, department_set)

    find_dict = {}
    departments = choose_many(
        "院系",
        DEPARTMENT_LIST,
        "请选择您想查询的院系，可按空格跳过院系选择(院系A, 院系B, ...)：",
    )
    if departments:
        find_dict["department"] = departments

    grades = choose_many(
        "年级",
        GRADE_LIST,
        "请选择您想查询的年级，可按空格跳过年级选择：",
    )
    if grades:
        find_dict["grade"] = grades
    return find_dict


def get_d_g_gpa(manager, find_dict):
    gpas = gpas_by_scope(
        manager.data_view(),
        departments=find_dict.get("department"),
        grades=find_dict.get("grade"),
    )
    departments = find_dict.get("department")
    grades = find_dict.get("grade")
    if departments and grades:
        print(f"{','.join(departments)}第{','.join(map(str, grades))}的绩点统计分析如下：")
    elif departments:
        print(f"{','.join(departments)}的绩点统计分析如下：")
    elif grades:
        print(f"{','.join(map(str, grades))}的绩点统计分析如下：")
    return gpas


def gpa_caculate_output(gpas_list):
    return print_gpa_statistics(gpas_list)


def t_list():
    from core.legacy_services.Course import CourseManage

    return list(CourseManage.current_teacher_dict().keys())


def input_t_gpa(teacher_list):
    return choose_many(
        "教师",
        teacher_list,
        "请输入您想查询的教师(教师1, 教师2, 教师3...)：",
    )


def get_t_gpa(manager, find_list):
    gpas = gpas_by_teachers(manager.data_view(), find_list)
    print(f"{','.join(find_list)}的绩点统计分析如下：")
    return gpas


def gpa_stat(manager):
    dimension = choose_dimension(
        ["学院和年级", "教师"],
        "请输入您想查询的维度(学院和年级/教师)：",
    )
    if not dimension:
        return

    if dimension == "学院和年级":
        find_dict = input_d()
        if not find_dict:
            return
        gpas = get_d_g_gpa(manager, find_dict)
    else:
        teachers = t_list()
        if not teachers:
            print("未找到对应教师")
            return
        find_list = input_t_gpa(teachers)
        if not find_list:
            return
        gpas = get_t_gpa(manager, find_list)

    if gpas:
        return gpa_caculate_output(gpas)
    print("绩点统计分析失败")
