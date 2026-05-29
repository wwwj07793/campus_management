from ..models.Student import Student
import operator
from ..models.Course import Course
from collections import deque, defaultdict
from .Student import StudentManage
from core.interpretation import course_analysis
from core.interpretation.data_views import CampusDataView
from core.interpretation.statistics import print_gpa_statistics, print_score_statistics
import re
# 高耦合：相互依赖度高
# 业务->功能模块->实现步骤（解耦）
#    拆分      拆分
# 核心数据只存一份；派生数据不要长期存；需要时通过函数临时算出来

students_dict = StudentManage.students_dict


def caculate_output(scores_list):
    return print_score_statistics(scores_list)


def gpa_caculate_output(gpas_list):
    return print_gpa_statistics(gpas_list)


class CourseManage:
    all_courses_dict = {}  # id: 对象列表
    max_credit = 25
    min_credit = 12
    deque_dict = {}  # (id, 教师, 课程时间安排): 队列(学生id)
    op_map = {
        "<": operator.le,
        "==": operator.eq
    }

    @classmethod
    def data_view(s):
        return CampusDataView(StudentManage.students_dict, s.all_courses_dict)

    @classmethod
    def current_teacher_dict(s):
        return s.data_view().courses_by_teacher()

    @classmethod
    def current_teacher_statistics(s):
        return s.data_view().teacher_statistics()

    @classmethod
    def id_input(s):
        while True:
            student_id = str(input("请输入学号：")).strip()
            if student_id:
                if re.match(r'^\d{7}$', student_id):
                    if student_id not in students_dict:
                        print("该学生不存在")
                        continue
                    else:
                        return student_id
                else:
                    print("学号格式不合法")
                    continue
            else:
                return None

    def select_range(s, student_id):
        if student_id:
            courses_id_list = []
            or_courses_list = []
            grade = students_dict[str(student_id)].grade
            department = students_dict[str(student_id)].department
            for g, d in s.g_d_course_dict.keys():
                if d == department and g == grade:
                    id = str(s.g_d_course_dict[(g, d)])
                    courses_id_list.append(id)
            for id in courses_id_list:
                or_courses_list.extend(s.all_courses_dict[id])
            return or_courses_list
        else:
            print("学生不存在")

    def verify(s, student_id, or_courses_list, result_list, opera):
        courses_dict = {}
        total_credit = 0
        total_credit = sum([i.credit for i in result_list])
        for course in or_courses_list:
            val_course = True
            result_id_list = [i.id for i in result_list]
            if not set(course.prerequisites).issubset(set(result_id_list)):
                val_course = False
            if opera(course.course_count, course.capacity):
                val_course = False
            for re_course in result_list:
                if course.id == re_course.id or course.schedule == re_course.schedule:
                    val_course = False
                    break
            if total_credit + course.credit > s.max_credit:
                val_course = False
            if val_course:
                courses_dict[str(course.id)].append(course)
                print(
                    f"课程id：{course.id} 课程名：{course.name} 学分：{course.credit} 执教教师:{course.teacher} 上课时间安排：{course.schedule} 已选人数：({course.course_count}/{course.capacity}) ")
        return courses_dict

    def input_select(s, courses_dict):
        while True:
            input_str = input(
                "请输入您想选择的课程信息((课程id，教师姓名，上课时间安排)每门课间用|分隔)：").strip()
            courses_list = input_str.replace('，', ',').split("|")
            if input_str:
                if courses_list:
                    val_list = []
                    for course_id, teacher, schedule in courses_list:
                        val_include = False
                        if course_id in courses_dict:
                            course_list = courses_dict[str(course_id)]
                            for course in course_list:
                                if course.teacher == teacher and course.schedule == schedule:
                                    val_include = True
                                    val_list.append(val_include)
                    if False in val_list:
                        print("课程id未在可选范围内")
                        continue
                    else:
                        total_credit = 0
                        for course_id in courses_list:
                            course_list = courses_dict[str(course_id)]
                            for course in course_list:
                                total_credit += course.credit
                        if total_credit < s.min_credit:
                            print(
                                f"目前总学分为{total_credit}，学分未达最低的{s.min_credit}学分")
                            total_credit = 0
                            continue
                        elif total_credit > s.max_credit:
                            print(
                                f"目前总学分为{total_credit}，学分超出最高的{s.max_credit}学分")
                            total_credit = 0
                            continue
                        else:
                            break
                else:
                    print("输入格式错误，正确格式如下：(a, b, c)|(e, f, g)")
                    continue
            else:
                return (None, None)
        return (courses_list, total_credit)

    def select(s, or_courses_list, student_id):
        student = students_dict[str(student_id)]
        result_list = list(student.entrolled_course.values())
        print("以下是您可选择的课程：")
        courses_dict = s.verify(
            student_id, or_courses_list, result_list, s.op_map['=='])
        tuple = s.input_select(courses_dict)
        if tuple[0] == None and tuple[1] == None:
            print("未输入有效课程")
            return
        courses_list = tuple[0]
        total_credit = tuple[1]
        for course_id, teacher, schedule in courses_list:
            course_list = courses_dict[str(course_id)]
            for course in course_list:
                if course.teacher == teacher and course.schedule == schedule:
                    student = students_dict[str(student_id)]
                    course.course_count += 1
                    course.enrolled_students.add(student)
                    student.entrolled_course[course.id] = None
        print(f"选课成功，总学分为{total_credit}")

    def select_class(s):
        student_id = s.id_input()
        if student_id == None:
            return
        else:
            or_courses_list = s.select_range(student_id)
            s.select(or_courses_list, student_id)

    def automate_add(s, course_id, teacher, schedule):
        key = str((course_id, teacher, schedule))
        student_deque = s.deque_dict.get(key, deque())
        if student_deque:
            student = student_deque.popleft()
            courses_list = s.all_courses_dict[str(course_id)]
            for course in courses_list:
                if course.teacher == teacher and course.schedule == schedule:
                    student.entrolled_course[course.id] = None
                    course.entolled_students.add(student)
                    course.current_count += 1
        else:
            return

    def drop(s, student_id):
        total_credit = 0
        courses_id_list = []
        print("您已选择的课程如下：")
        student = students_dict[str(student_id)]
        courses_list = s.data_view().courses_for_student(student)
        if courses_list:
            for course in courses_list.values():
                total_credit += course.credit
                courses_id_list.append(course.id)
                print(f"课程id：{course.id} 课程名：{course.name} 学分：{course.credit} 执教教师:{course.teacher} 上课时间安排：{course.schedule} 已选人数：({course.course_count}/{course.capacity}) ")
            while True:
                course_id_list = [i.strip() for i in input(
                    "请输入您想删除的课程id：").replace('，', ',').split(',') if i.strip()]
                if course_id_list:
                    if not set(course_id_list).issubset(set(courses_id_list)):
                        print("课程id未在您已选择的课程内")
                        continue
                    else:
                        break
                else:
                    return
            for course_id in course_id_list:
                course = courses_list[str(course_id)]
                total_credit -= course.credit
                course.enrolled_students.discard(
                    students_dict[str(student_id)])
                course.course_count -= 1
                student.entrolled_course.pop(str(course_id), None)
                student_deque = s.deque_dict.get(str(course_id), deque())
                if student_deque:
                    s.automate_add(course_id, course.teacher, course.schedule)
            print(f"退课成功，您目前的总学分为{total_credit}")
            return total_credit
        else:
            print("您的选课目前为空，请先选课")

    def drop_class(s):
        student_id = s.id_input()
        if student_id == None:
            return
        else:
            total_credit = s.drop(student_id)
            if total_credit < s.min_credit:
                print(f"学分未达最低的{s.min_credit}学分，还需选择其他课程")
            else:
                return
            or_courses_list = s.select_range(student_id)
            s.select(or_courses_list, student_id)

    def submit_wait(s):
        student_id = s.id_input()
        if student_id == None:
            return
        else:
            student = students_dict[str(student_id)]
            result_list = list(student.entrolled_course.values())
            or_courses_list = s.select_range(s, student_id)
            if not result_list:
                print("请先完成选课，再进行候补")
                return
            print("下列是您可候补的课程：")
            courses_dict = s.vertify(
                student_id, or_courses_list, result_list, s.op_map['<'])
            tuple = s.input_select(courses_dict)
            if tuple[0] == None and tuple[1] == None:
                print("未选择候补课程")
                return
            courses_list = tuple[0]
            total_credit = tuple[1]
            for tuple in courses_list:
                student = students_dict[student_id]
                student_deque = s.deque_dict.setdefault(tuple, deque())
                student_deque.append(student)
            print(f"候补申请提交成功，所有候补皆成功后的学分为{total_credit}")

    def teacher_stat(s):
        return course_analysis.teacher_stat(s)

    def teacher_input(s):
        return course_analysis.teacher_input(s)

    def teacher_range(s, teacher):
        return course_analysis.teacher_range(s, teacher)

    def teacher_course_id_input(s, teacher, id_students_dict):
        return course_analysis.teacher_course_id_input(teacher, id_students_dict)

    def get_t_store(s, find_list, id_students_dict):
        return course_analysis.get_t_store(find_list, id_students_dict)

    def t_score_stat(s):
        return course_analysis.t_score_stat(s)

    def all_get_t_store(s, teacher):
        return course_analysis.all_get_t_store(s, teacher)

    def all_t_score_stat(s):
        return course_analysis.all_t_score_stat(s)
# 加上gpa统计分析

    def teacher_input_gpa(s):
        return course_analysis.teacher_input_gpa(s)

    def get_t_store_gpa(s, teacher):
        return course_analysis.get_t_store_gpa(s, teacher)

    def t_gpa_stat(s):
        return course_analysis.t_gpa_stat(s)
