from core.models.Student import DEPARTMENT_LIST, GRADE_LIST
from core.interpretation.input_helpers import choose_many, choose_one
from core.interpretation.statistics import print_gpa_statistics, print_score_statistics


def num_stat(manager):
    counts = manager.data_view().student_counts()
    return counts["total"]


def st_stat(manager):
    return manager.data_view().student_indexes()


def find_stat(manager, total):
    if total == 0:
        print("暂时还无学生数据，请先添加学生数据")
        return

    print("请输入您想查看的(院系-年级)的统计分析数据：")
    department = choose_one("院系", DEPARTMENT_LIST, "院系: ")
    grade = choose_one("年级", GRADE_LIST, "年级：")

    if not department and not grade:
        return

    counts = manager.data_view().student_counts()
    by_department = counts["by_department"]
    by_grade = counts["by_grade"]
    by_department_grade = counts["by_department_grade"]

    if not department and grade:
        for item_department, num in by_department.items():
            print(f"{item_department}共有{num}名学生，占总学生数{round((num / total) * 100, 3) if total else 0.0}%")
    elif department and not grade:
        for item_grade, num in by_grade.items():
            print(f"{item_grade}共有{num}名学生，占总学生数{round((num / total) * 100, 3) if total else 0.0}%")
    else:
        for item_department, grades in by_department_grade.items():
            for item_grade, num in grades.items():
                department_total = by_department[item_department]
                grade_total = by_grade[item_grade]
                print(
                    f"在{item_department}学生中{item_grade}学生有{num}人，"
                    f"占总学生{round((num / total) * 100, 3) if total else 0.0}%，"
                    f"占{item_department}学生{round((num / department_total) * 100, 3) if department_total else 0.0}%，"
                    f"占{item_grade}学生{round((num / grade_total) * 100, 3) if grade_total else 0.0}%"
                )


def g_d_nu_statc(manager):
    total = num_stat(manager)
    return find_stat(manager, total)


def g_d_input():
    result = {}
    departments = choose_many(
        "院系",
        DEPARTMENT_LIST,
        "请选择您想查询的院系，可按空格跳过院系选择(院系A, 院系B, ...)：",
    )
    if departments:
        result["department"] = departments

    grades = choose_many(
        "年级",
        GRADE_LIST,
        "请选择您想查询的年级，可按空格跳过年级选择：",
    )
    if grades:
        result["grade"] = grades
    return result


def d_g_range(manager, d_g_dict):
    return manager.data_view().students_by_course_for_scope(
        departments=d_g_dict.get("department"),
        grades=d_g_dict.get("grade"),
    )


def course_id_input(course_id_dict):
    return choose_many(
        "课程id",
        course_id_dict.keys(),
        "请输入您想查询的课程id(id1, id2, id3...)：",
    )


def id_input(course_id_dict):
    return course_id_input(course_id_dict)


def get_d_g_store(find_list, course_id_dict):
    scores = []
    for course_id in find_list:
        for student in course_id_dict[course_id]:
            scores.append(student.enrolled_courses.get(course_id))
    return scores


def d_g_score_stat(manager):
    d_g_dict = g_d_input()
    if not d_g_dict:
        return
    course_id_dict = d_g_range(manager, d_g_dict)
    if not course_id_dict:
        print("未找到对应的课程院系和年级")
        return
    find_list = course_id_input(course_id_dict)
    if not find_list:
        return
    scores = get_d_g_store(find_list, course_id_dict)
    if scores:
        return print_score_statistics(scores)
    print("分数统计分析失败")


def all_get_d_g_store(course_id_dict):
    scores = []
    for course_id, students in course_id_dict.items():
        scores.extend(get_d_g_store([course_id], {course_id: students}))
    return scores


def all_d_g_score_stat(manager):
    d_g_dict = g_d_input()
    if not d_g_dict:
        return
    course_id_dict = d_g_range(manager, d_g_dict)
    if not course_id_dict:
        print("未找到对应的课程院系和年级")
        return
    scores = all_get_d_g_store(course_id_dict)
    if scores:
        return print_score_statistics(scores)
    print("分数统计分析失败")


def get_d_g_store_gpa(manager, d_g_dict):
    return manager.data_view().gpas_for_scope(
        departments=d_g_dict.get("department"),
        grades=d_g_dict.get("grade"),
    )


def d_g_gpa_stat(manager):
    d_g_dict = g_d_input()
    if not d_g_dict:
        return
    gpas = get_d_g_store_gpa(manager, d_g_dict)
    if gpas:
        return print_gpa_statistics(gpas)
    print("绩点统计分析失败")
