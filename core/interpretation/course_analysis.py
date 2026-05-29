from collections import defaultdict

from core.interpretation.input_helpers import choose_many, choose_one
from core.interpretation.statistics import print_gpa_statistics, print_score_statistics


def _student_object(student, students):
    if hasattr(student, "enrolled_courses"):
        return student
    return students.get(str(student))


def teacher_stat(manager):
    return manager.current_teacher_statistics()


def teacher_input(manager, prompt="请输入您想查询成绩统计分析的教师"):
    return choose_one("教师", manager.current_teacher_dict().keys(), prompt)


def teacher_range(manager, teacher):
    id_students_dict = defaultdict(list)
    for course in manager.current_teacher_dict()[teacher]:
        for student in course.enrolled_students:
            student_obj = _student_object(student, manager.data_view().students)
            if student_obj is not None:
                id_students_dict[course.id].append(student_obj)
    return id_students_dict


def teacher_course_id_input(teacher, id_students_dict):
    return choose_many(
        "课程id",
        id_students_dict.keys(),
        "请输入您想查询的课程id(id1, id2, id3...)：",
    )


def id_input(teacher, id_students_dict):
    return teacher_course_id_input(teacher, id_students_dict)


def get_t_store(find_list, id_students_dict):
    scores = []
    for course_id in find_list:
        for student in id_students_dict[course_id]:
            scores.append(student.enrolled_courses.get(course_id))
    print("所选教师课程的成绩统计分析如下：")
    return scores


def t_score_stat(manager):
    teacher = teacher_input(manager)
    if not teacher:
        return
    id_students_dict = teacher_range(manager, teacher)
    if not id_students_dict:
        print("未找到对应的课程id")
        return
    find_list = teacher_course_id_input(teacher, id_students_dict)
    if not find_list:
        return
    scores = get_t_store(find_list, id_students_dict)
    if scores:
        return print_score_statistics(scores)
    print("分数统计分析失败")


def all_get_t_store(manager, teacher):
    scores = []
    for course in manager.current_teacher_dict()[teacher]:
        for student in course.enrolled_students:
            student_obj = _student_object(student, manager.data_view().students)
            if student_obj is not None:
                scores.append(student_obj.enrolled_courses.get(course.id))
    return scores


def all_t_score_stat(manager):
    teacher = teacher_input(manager)
    if not teacher:
        return
    return print_score_statistics(all_get_t_store(manager, teacher))


def teacher_input_gpa(manager):
    return teacher_input(manager, prompt="请输入您想查询绩点统计分析的教师")


def get_t_store_gpa(manager, teacher):
    gpas = []
    for course in manager.current_teacher_dict()[teacher]:
        for student in course.enrolled_students:
            student_obj = _student_object(student, manager.data_view().students)
            if student_obj is not None:
                gpas.append(student_obj.gpa)
    print(f"{teacher}相关学生的绩点统计分析如下：")
    return gpas


def t_gpa_stat(manager):
    teacher = teacher_input_gpa(manager)
    if not teacher:
        return
    gpas = get_t_store_gpa(manager, teacher)
    if gpas:
        return print_gpa_statistics(gpas)
    print("绩点统计分析失败")
