from .Student import StudentManage
from .Course import CourseManage
from core.interpretation import grade_analysis
import csv
import re
students_dict = StudentManage.students_dict
all_courses_dict = CourseManage.all_courses_dict
id_input = CourseManage.id_input


class GradeManage:
    @classmethod
    def data_view(s):
        return CourseManage.data_view()

    @classmethod
    def score_to_GPA(s, score):
        if score >= 95 and score <= 100:
            score = 4.0
        elif score >= 90 and score <= 94:
            score = 3.7
        elif score >= 85 and score <= 89:
            score = 3.3
        elif score >= 80 and score <= 84:
            score = 3.0
        elif score >= 80 and score <= 84:
            score = 3.0
        elif score >= 75 and score <= 79:
            score = 2.7
        elif score >= 70 and score <= 74:
            score = 2.3
        elif score >= 65 and score <= 69:
            score = 2.0
        elif score >= 60 and score <= 64:
            score = 1.0
        elif score < 60:
            score = 0
        return score

    def GPA_auto(s, course_dict, student):
        total_credit = 0
        total_score = 0
        for course_id, score in course_dict.items():
            course = (all_courses_dict[str(course_id)])[0]
            credit = course.credit
            total_credit += credit
            score = s.score_to_GPA(float(score))
            total_score += score * credit
        GPA = total_score / total_credit if total_credit != 0 else 0.0
        student.gpa = GPA

    def grade_input(s):
        student_id = id_input()
        if student_id == None:
            return
        else:
            print("请将各科成绩填入对应科目， 可按换行跳过某科目")
            student = students_dict[str(student_id)]
            val_list = []
            course_dict = student.enrolled_courses
            for course_id, score in course_dict.items():
                if not (float(score) >= 0 and float(score) <= 100):
                    course = (all_courses_dict[str(course_id)])[0]
                    name = course.name
                    while True:
                        score = input(f"{name}：").strip()
                        if score:
                            score = float(score)
                            if score >= 0 and score <= 100:
                                course_dict[str(course_id)] = score
                                val_list.append(True)
                                break
                            else:
                                print("成绩不合法")
                                continue
                        else:
                            val_list.append(False)
                            break
                else:
                    val_list.append(True)
            if not False in val_list:
                s.GPA_auto(course_dict, student)

    def gr_add_generator(s, file_path):
        with open(file_path, 'r', encoding='utf8') as f:
            reader = csv.DictReader(f)
            for index, row in enumerate(reader, 1):
                isval = True
                student_id = row.get("student_id")
                if not re.match(r'^\d{7}$', student_id or ""):  # 尝试拆解验证逻辑
                    isval = False
                course_id = row.get("course_id")
                if not re.match(r'^[A-Z]{2}\d{3}$', course_id or ""):
                    isval = False
                score = row.get("score")
                try:
                    score = float(score)
                except (TypeError, ValueError):
                    isval = False
                if isval and not (score >= 0 and score <= 100):
                    isval = False
                if isval == True:
                    row["score"] = score
                    yield row
                else:
                    yield (index, student_id, course_id)

    def gr_adds(s, file_path):
        success_count = 0
        fail_count = 0
        fail_detail = []
        for row in s.gr_add_generator(file_path):
            if isinstance(row, dict):
                success_count += 1
                student_id = row["student_id"]
                course_id = row["course_id"]
                score = row["score"]
                student = students_dict[str(student_id)]
                pre_score = (student.enrolled_courses)[str(course_id)]
                try:
                    pre_score = float(pre_score)
                except (TypeError, ValueError):
                    pre_score = None
                if pre_score is None or not (pre_score >= 0 and pre_score <= 100):
                    (student.enrolled_courses)[course_id] = score
                else:
                    continue
            elif isinstance(row, tuple):
                fail_count += 1
                fail_detail.append(row)
        print(f"导入成功{success_count}条成绩， 导入失败{fail_count}条成绩")
        print(f"失败细节如下：")
        for detail in fail_detail:
            print(f"第{detail[0]}行学号为{detail[1]}的学生的课程id为{detail[2]}的课程导入失败")

    def modify_bef_show(s):
        student_id = id_input()
        if student_id == None:
            return
        else:
            student = students_dict[str(student_id)]
            GPA = student.gpa
            if GPA == 0.0:
                print("请先录入该学生成绩：")
                return None
            else:
                print("以下是该学生修改前的成绩单：")
                course_dict = student.enrolled_courses
                for course_id in course_dict:
                    score = course_dict[str(course_id)]
                    print(f"{course_id}：{score}分，", end='')
                return student

    def grade_modify(s, student):
        course_dict = student.enrolled_courses
        while True:
            course_id_list = [i.strip() for i in input(
                f"请输入您想修改的课程id({','.join(course_id_list)}，每个课程id之间用逗号分隔：").replace('，', ',').split(',') if i.strip()]
            if course_id_list:
                isval = True
                for course_id in course_id_list:
                    if not re.match(r'^[A_Z]{2}\d{3}&', str(course_id)):
                        isval = False
                if isval == False:
                    print("课程id不合法")
                    continue
                else:
                    break
            else:
                return
        for course_id in course_id_list:
            while True:
                isinput = True
                score = input(f"{course_id}：").strip()
                if score:
                    if not (score >= 0 and score <= 100):
                        print("成绩不合法")
                        continue
                    else:
                        break
                else:
                    isinput = False
                    break
            if isinput:
                course_dict[course_id] = score

    def modify_aft_show(s, student):
        course_dict = student.enrolled_courses
        print("以下是该学生修改后成绩单：")
        for course_id in course_dict:
            score = course_dict[str(course_id)]
            print(f"{course_id}：{score}分，", end='')
        while True:
            judge = ("是否提交该成绩单(是/否)：")
            if judge:
                if judge == '是' and judge == '否':
                    break
                else:
                    continue
            else:
                return
        if judge == '是':
            s.GPA_auto(course_dict, student)
        elif judge == '否':
            s.grade_modify(course_dict)

    def modify(s):
        student = s.modify_bef_show()
        s.grade_modify(student)
        s.modify_sft_show(student)

    def find_warn(s):
        student_id = id_input()
        if student_id == None:
            return
        else:
            student = students_dict[str(student_id)]
            course_dict = student.enrolled_courses
            GPA = student.gpa
            print(f"GPA:{GPA}")
            if GPA < 2.0:
                print(
                    "检测到你的GPA低于2.0预警线，将面临学业预警、评优评先资格受限的风险，请重点重修低绩点课程，也可咨询学业导师制定成绩提升计划！")
            for course_id in course_dict:
                course = all_courses_dict[str(course_id)]
                name = course.name
                score = course_dict[str(course_id)]
                print(f"{name}:{score}")
                if score < 60:
                    print("检测到您该课程成绩低于60分，该课程挂科，无法获取对应学分。请及时联系任课老师核对成绩，并提前了解补考/重修相关安排！")

    # 分数段占比，绘图，同一门课不同学院/不同年级/不同教师，绩点统计
    # 统计分析首先保证数据源基础且唯一，将常用的容器封装成函数转变成局部容器，遍历逻辑用生成器和迭代器优化(这里依赖了之前模块的新容器，且没用生成器，优化实在工作量巨大，之后注意)
    # 生成器的用途：将步骤间的临时容器换成生成器，用时间换空间
    def input_id(s):
        return grade_analysis.input_id()

    def d_range(s, course_id):
        return grade_analysis.d_range(s, course_id)

    def g_range(s, course_id, department_list):
        return grade_analysis.g_range(s, course_id, department_list)

    def input_d_for_course(s, course_id, t_department_set):
        return grade_analysis.input_d_for_course(
            s, course_id, t_department_set)

    def get_d_g_score(s, course_id, find_dict):
        return grade_analysis.get_d_g_score(s, course_id, find_dict)

    def caculate_output(s, score_list):
        return grade_analysis.caculate_output(score_list)

    def t_range(s, course_id):
        return grade_analysis.t_range(s, course_id)

    def input_t(s, course_id, t_teacher_dict):
        return grade_analysis.input_t(course_id, t_teacher_dict)

    def get_t_score(s, find_list, t_teacher_dict):
        return grade_analysis.get_t_score(find_list, t_teacher_dict)

    def course_score_stat(s):
        return grade_analysis.course_score_stat(s)
# 还要加入gpa的成绩统计分析

    def input_d(s, course_id=None, t_department_set=None):
        return grade_analysis.input_d(s, course_id, t_department_set)

    def get_d_g_gpa(s, find_dict):
        return grade_analysis.get_d_g_gpa(s, find_dict)

    def gpa_caculate_output(s, gpas_list):
        return grade_analysis.gpa_caculate_output(gpas_list)

    def t_list(s):
        return grade_analysis.t_list()

    def input_t_gpa(s, teacher_list):
        return grade_analysis.input_t_gpa(teacher_list)

    def get_t_gpa(s, find_list):
        return grade_analysis.get_t_gpa(s, find_list)

    def gpa_stat(s):
        return grade_analysis.gpa_stat(s)
