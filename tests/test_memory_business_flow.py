import csv  # 导入 csv 模块，用来读取 data_files 目录下的 CSV 测试数据。
import sys  # 导入 sys 模块，用来临时修改 Python 的模块搜索路径。
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path  # 导入 Path，用面向对象的方式处理文件路径。
from unittest.mock import patch


# 获取当前测试文件的绝对路径，然后向上找两级，得到项目根目录。
# 当前文件位置是：项目根目录 / tests / test_memory_business_flow.py
# parents[0] 是 tests 目录，parents[1] 是项目根目录。
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 把项目根目录加入 Python 模块搜索路径的最前面。
# 这样直接运行 python tests/test_memory_business_flow.py 时，也能导入 core 包。
sys.path.insert(0, str(PROJECT_ROOT))

# 从课程模型文件中导入 Course 类，用来创建课程对象。
from core.models.Course import Course

# 从学生模型文件中导入 Student 类，用来创建学生对象。
from core.models.Student import Student

# 从课程服务中导入 CourseManage，用来访问课程主数据字典和实时统计接口。
from core.legacy_services.Course import CourseManage

# 从成绩服务中导入 GradeManage，用来调用 GPA 自动计算逻辑。
from core.legacy_services.Grade import GradeManage

# 从学生服务中导入 StudentManage，用来访问学生主数据字典和数据视图接口。
from core.legacy_services.Student import StudentManage
from core.interpretation.statistics import gpa_statistics, score_statistics


# 这个测试文件的作用：
# 1. 不连接数据库，只用内存对象测试项目目前的核心业务。
# 2. 检查学生、课程、选课、成绩、GPA、统计视图是否能串起来。
# 3. 给后续数据库、API、硬件数据模块开发前提供一个基础验证脚本。

# 拼出测试数据目录：项目根目录 / data_files。
DATA_DIR = PROJECT_ROOT / "data_files"


def read_csv(filename):
    """读取 data_files 目录下指定名称的 CSV 文件，并返回字典列表。"""

    # 根据传入的文件名拼出完整路径。
    path = DATA_DIR / filename

    # 以只读模式打开 CSV 文件。
    # encoding="utf-8-sig" 可以兼容带 BOM 的 UTF-8 文件。
    # newline="" 是 csv 模块推荐写法，避免换行符处理出问题。
    with path.open("r", encoding="utf-8-sig", newline="") as file:

        # csv.DictReader 会把每一行转换成字典。
        # 例如表头 student_id,name 会变成 {"student_id": "...", "name": "..."}。
        reader = csv.DictReader(file)

        # 把 reader 转成 list，方便后面多次遍历和统计长度。
        return list(reader)


def reset_memory_store():
    """清空内存里的核心主数据，保证每个测试都从干净状态开始。"""

    # 清空学生主字典：student_id -> Student 对象。
    StudentManage.students_dict.clear()

    # 清空课程主字典：course_id -> Course 对象列表。
    CourseManage.all_courses_dict.clear()

    # 清空等待队列字典，用于选课容量满时的候补队列。
    CourseManage.deque_dict.clear()


def load_students():
    """把学生 CSV 数据加载成 Student 对象，并放入学生主字典。"""

    # 逐行读取学生测试数据。
    for row in read_csv("students_memory_test.csv"):

        # 用当前 CSV 行创建一个学生对象。
        student = Student(
            student_id=row["student_id"],  # 从 CSV 读取学号。
            name=row["name"],  # 从 CSV 读取姓名。
            gender=row["gender"],  # 从 CSV 读取性别。
            birth_date=row["birth_date"],  # 从 CSV 读取生日。
            department=row["department"],  # 从 CSV 读取院系。
            grade=int(row["grade"]),  # 从 CSV 读取年级，并转成整数。
        )

        # 把学生对象放入学生主字典，键是学号。
        StudentManage.students_dict[student.student_id] = student


def load_courses():
    """把课程 CSV 数据加载成 Course 对象，并放入课程主字典。"""

    # 逐行读取课程测试数据。
    for row in read_csv("courses_memory_test.csv"):

        # 先修课字段可能是空字符串，也可能是 AI001|PY001 这种格式。
        # split("|") 会按竖线切分，if item 会过滤空字符串。
        prerequisites = [
            item
            for item in row["prerequisites"].split("|")
            if item
        ]

        # 用当前 CSV 行创建一个课程对象。
        course = Course(
            course_id=row["course_id"],  # 课程编号，例如 AI001。
            name=row["name"],  # 课程名，例如 人工智能导论。
            credit=int(row["credit"]),  # 学分需要从字符串转成整数。
            teacher=row["teacher"],  # 任课教师。
            schedule=row["schedule"],  # 上课时间。
            capacity=int(row["capacity"]),  # 课程容量需要转成整数。
            prerequisites=prerequisites,  # 先修课程列表。
        )

        # all_courses_dict 的结构是：course_id -> [Course, Course, ...]。
        # 用列表是为了支持同一门课有不同教师或不同上课时间。
        CourseManage.all_courses_dict.setdefault(course.id, []).append(course)


def find_course(course_id, teacher, schedule):
    """根据课程号、教师和上课时间，在课程主字典中找到对应课程对象。"""

    # CourseManage.all_courses_dict.get(course_id, []) 会取出该课程编号下的课程列表。
    # 如果课程编号不存在，就返回空列表，避免 KeyError。
    for course in CourseManage.all_courses_dict.get(course_id, []):

        # 同时匹配教师和上课时间，才能确定是哪一个课程对象。
        if course.teacher == teacher and course.schedule == schedule:

            # 找到后直接返回课程对象。
            return course

    # 如果循环结束还没找到，说明测试数据或加载逻辑有问题。
    raise AssertionError(f"未找到课程: {course_id}, {teacher}, {schedule}")


def load_enrollments():
    """根据选课 CSV 数据，建立学生和课程之间的双向关系。"""

    # 逐行读取选课关系测试数据。
    for row in read_csv("enrollments_memory_test.csv"):

        # 根据学号从学生主字典中找到学生对象。
        student = StudentManage.students_dict[row["student_id"]]

        # 根据课程号、教师、时间找到具体课程对象。
        course = find_course(row["course_id"], row["teacher"], row["schedule"])

        # 在学生对象里记录已选课程。
        # 这里先把成绩设为 None，表示已经选课但还没有录入成绩。
        student.enrolled_courses[course.id] = None

        # 在课程对象里记录已选学生。
        # 这里存 student_id，而不是整个学生对象，方便之后统计和比对。
        course.enrolled_students.add(student.student_id)

        # 课程当前人数加 1。
        course.current_count += 1


def load_grades_and_update_gpa():
    """读取成绩 CSV，写入学生对象，并重新计算每个学生的 GPA。"""

    # 创建成绩管理对象，用来调用 GPA_auto。
    grade_manager = GradeManage()

    # 逐行读取成绩测试数据。
    for row in read_csv("grades_memory_test.csv"):

        # 根据学号找到学生对象。
        student = StudentManage.students_dict[row["student_id"]]

        # 把该课程成绩写入学生的 enrolled_courses 字典。
        # 例如 student.enrolled_courses["AI001"] = 92.0。
        student.enrolled_courses[row["course_id"]] = float(row["score"])

    # 遍历所有学生，给每个有成绩的学生重新计算 GPA。
    for student in StudentManage.students_dict.values():

        # 从学生已选课程中筛选出已经录入成绩的课程。
        scored_courses = {
            course_id: score
            for course_id, score in student.enrolled_courses.items()
            if score is not None
        }

        # 如果这个学生至少有一门课有成绩，就计算 GPA。
        if scored_courses:

            # GPA_auto 会根据课程学分和成绩计算绩点，并写回 student.gpa。
            grade_manager.GPA_auto(scored_courses, student)


def build_memory_demo_data():
    """按真实业务顺序装配一整套内存测试数据。"""

    # 第一步：清空旧数据，避免上一次测试残留。
    reset_memory_store()

    # 第二步：加载学生主数据。
    load_students()

    # 第三步：加载课程主数据。
    load_courses()

    # 第四步：建立选课关系。
    load_enrollments()

    # 第五步：录入成绩并计算 GPA。
    load_grades_and_update_gpa()


def test_student_and_course_data_loaded():
    """测试 1：确认学生和课程基础数据能正确加载。"""

    # 构建完整内存测试数据。
    build_memory_demo_data()

    # 检查学生主字典中是否正好有 10 个学生。
    assert len(StudentManage.students_dict) == 10

    # 检查指定学生是否存在。
    assert "2025001" in StudentManage.students_dict

    # 检查指定课程是否存在。
    assert "AI001" in CourseManage.all_courses_dict

    # PY001 在测试数据里有两个教师版本，所以列表长度应该是 2。
    assert len(CourseManage.all_courses_dict["PY001"]) == 2


def test_enrollment_relationships_created():
    """测试 2：确认学生选课后，学生和课程两边的数据都更新了。"""

    # 构建完整内存测试数据。
    build_memory_demo_data()

    # 取出测试学生 2025001。
    student = StudentManage.students_dict["2025001"]

    # 找到 AI001 这门由李老师在周一1-2节上的课程。
    ai_course = find_course("AI001", "李老师", "周一1-2节")

    # 学生的已选课程中应该包含 AI001。
    assert "AI001" in student.enrolled_courses

    # 课程的已选学生集合中应该包含该学生学号。
    assert student.student_id in ai_course.enrolled_students

    # 课程当前人数应该大于 0，说明人数统计被更新。
    assert ai_course.current_count > 0


def test_grade_and_gpa_calculation():
    """测试 3：确认成绩能写入，GPA 能自动计算。"""

    # 构建完整内存测试数据。
    build_memory_demo_data()

    # 取出一个成绩较好的学生。
    high_student = StudentManage.students_dict["2025001"]

    # 取出一个存在低分预警风险的学生。
    warning_student = StudentManage.students_dict["2025007"]

    # 2025001 的 AI001 成绩在 CSV 中是 92。
    assert high_student.enrolled_courses["AI001"] == 92

    # 这个学生多门成绩较好，所以 GPA 应该大于 3.0。
    assert high_student.gpa > 3.0

    # 2025007 的 PY001 成绩在 CSV 中是 45，用于测试不及格场景。
    assert warning_student.enrolled_courses["PY001"] == 45

    # 45 分对应绩点较低，所以 GPA 应该低于 2.0。
    assert warning_student.gpa < 2.0


def test_realtime_data_view_statistics():
    """测试 4：确认 data_view 可以实时生成派生统计数据。"""

    # 构建完整内存测试数据。
    build_memory_demo_data()

    # 获取统一数据视图对象。
    view = StudentManage.data_view()

    # 实时统计学生数量、院系人数、年级人数。
    counts = view.student_counts()

    # 实时生成教师 -> 课程列表 的映射。
    teacher_courses = CourseManage.current_teacher_dict()

    # 实时生成教师统计数据。
    teacher_stats = CourseManage.current_teacher_statistics()

    # 实时获取电子信息工程学院 2025 级学生的 GPA 列表。
    gpas = view.gpas_for_scope(
        departments=["电子信息工程学院"],
        grades=[2025],
    )

    # 总学生数应该是 10。
    assert counts["total"] == 10

    # 电子信息工程学院在测试数据中有 3 个学生。
    assert counts["by_department"]["电子信息工程学院"] == 3

    # 李老师应该存在于教师课程映射里。
    assert "李老师" in teacher_courses

    # 李老师至少教授 2 个课程对象：AI001 和 ML201。
    assert teacher_stats["李老师"][2] >= 2

    # 电子信息工程学院 2025 级有 3 个学生，所以 GPA 列表长度为 3。
    assert len(gpas) == 3


def test_low_score_warning_students_can_be_found():
    """测试 5：确认能从成绩中找出需要学业预警的学生。"""

    # 构建完整内存测试数据。
    build_memory_demo_data()

    # 准备一个列表，用来保存需要预警的学生学号。
    warning_students = []

    # 遍历所有学生对象。
    for student in StudentManage.students_dict.values():

        # 判断该学生是否存在任意一门低于 60 分的课程。
        has_failed_course = any(
            score is not None and float(score) < 60
            for score in student.enrolled_courses.values()
        )

        # 如果有不及格课程，或者 GPA 低于 2.0，就加入预警名单。
        if has_failed_course or student.gpa < 2.0:
            warning_students.append(student.student_id)

    # 2025004 在测试数据中有 58 和 54，应该被预警。
    assert "2025004" in warning_students

    # 2025007 在测试数据中有 45，应该被预警。
    assert "2025007" in warning_students


def test_interpretation_statistics_are_independent():
    """测试 6：确认统计分析已经可以通过独立的数据解释层完成。"""

    score_stats = score_statistics([92, 88, 45, None, "bad"])
    gpa_stats = gpa_statistics([3.7, 3.2, 1.0, None, "bad"])

    assert score_stats["count"] == 3
    assert score_stats["max"] == 92
    assert score_stats["min"] == 45
    assert score_stats["pass_rate"] == 2 / 3

    assert gpa_stats["count"] == 3
    assert gpa_stats["max"] == 3.7
    assert gpa_stats["min"] == 1.0
    assert gpa_stats["pass_rate"] == 2 / 3


def test_student_service_uses_interpretation_layer():
    """测试 7：确认学生业务层统计接口能调用解释层并返回派生结果。"""

    build_memory_demo_data()

    student_manager = StudentManage()
    total = student_manager.num_stat()
    indexes = student_manager.st_stat()
    course_students = student_manager.d_g_range({
        "department": ["电子信息工程学院"],
        "grade": [2025],
    })
    scores = student_manager.all_get_d_g_store(course_students)
    gpas = student_manager.get_d_g_store_gpa({
        "department": ["电子信息工程学院"],
        "grade": [2025],
    })

    assert total == 10
    assert len(indexes["by_department"]["电子信息工程学院"]) == 3
    assert "AI001" in course_students
    assert 92 in scores
    assert len(gpas) == 3


def test_course_service_uses_interpretation_layer():
    """测试 8：确认课程业务层教师统计接口能调用解释层。"""

    build_memory_demo_data()

    course_manager = CourseManage()
    teacher_stats = course_manager.teacher_stat()
    teacher_courses = course_manager.teacher_range("李老师")
    scores = course_manager.all_get_t_store("李老师")
    output = StringIO()
    with redirect_stdout(output):
        gpas = course_manager.get_t_store_gpa("李老师")

    assert teacher_stats["李老师"][2] >= 2
    assert "AI001" in teacher_courses
    assert 92 in scores
    assert any(gpa > 3.0 for gpa in gpas)


def test_grade_service_uses_interpretation_layer_direct_interfaces():
    """测试 9：确认成绩业务层分析接口能调用解释层直接取分数和 GPA。"""

    build_memory_demo_data()

    grade_manager = GradeManage()
    departments = grade_manager.d_range("AI001")
    grades = grade_manager.g_range("AI001", ["电子信息工程学院"])
    output = StringIO()
    with redirect_stdout(output):
        scores = grade_manager.get_d_g_score(
            "AI001",
            {"department": ["电子信息工程学院"], "grade": [2025]},
        )
    teacher_students = grade_manager.t_range("AI001")
    output = StringIO()
    with redirect_stdout(output):
        teacher_scores = grade_manager.get_t_score(["李老师"], teacher_students)
    output = StringIO()
    with redirect_stdout(output):
        gpas = grade_manager.get_d_g_gpa({"department": ["电子信息工程学院"]})

    assert "电子信息工程学院" in departments
    assert 2025 in grades
    assert 92 in scores
    assert "李老师" in teacher_students
    assert 92 in teacher_scores
    assert len(gpas) == 3


def test_grade_service_analysis_flows_with_patched_input():
    """测试 10：确认成绩业务层交互式统计入口能完整调用解释层流程。"""

    build_memory_demo_data()

    grade_manager = GradeManage()

    with patch("builtins.input", side_effect=["AI001", "学院和年级", "", ""]):
        output = StringIO()
        with redirect_stdout(output):
            score_stats = grade_manager.course_score_stat()

    with patch("builtins.input", side_effect=["学院和年级", "电子信息工程学院", ""]):
        output = StringIO()
        with redirect_stdout(output):
            gpa_stats = grade_manager.gpa_stat()

    assert score_stats["count"] > 0
    assert score_stats["max"] >= 90
    assert gpa_stats["count"] == 3
    assert gpa_stats["average"] > 0


def test_device_environment_mock_data_loaded():
    """测试 11：确认软硬结合模拟数据能读取，并能识别异常环境数据。"""

    # 读取教室环境模拟数据。
    rows = read_csv("device_environment_memory_test.csv")

    # 筛选异常记录：
    # 1. status 字段直接标记为 abnormal；
    # 2. 或者温度大于等于 35 摄氏度。
    abnormal_rows = [
        row
        for row in rows
        if row["status"] == "abnormal" or float(row["temperature"]) >= 35
    ]

    # 测试数据中共有 9 条教室环境记录。
    assert len(rows) == 9

    # 第一条异常记录的设备编号应该是 DEV-A102。
    assert abnormal_rows[0]["device_id"] == "DEV-A102"

    # 第一条异常记录对应的教室应该是 A102。
    assert abnormal_rows[0]["classroom"] == "A102"


if __name__ == "__main__":
    # 这里是手动运行入口。
    # 如果 pytest 暂时不能用，就可以直接运行：
    # python tests/test_memory_business_flow.py

    # 把所有测试函数放进一个列表，方便按顺序执行。
    test_functions = [
        test_student_and_course_data_loaded,
        test_enrollment_relationships_created,
        test_grade_and_gpa_calculation,
        test_realtime_data_view_statistics,
        test_low_score_warning_students_can_be_found,
        test_interpretation_statistics_are_independent,
        test_student_service_uses_interpretation_layer,
        test_course_service_uses_interpretation_layer,
        test_grade_service_uses_interpretation_layer_direct_interfaces,
        test_grade_service_analysis_flows_with_patched_input,
        test_device_environment_mock_data_loaded,
    ]

    # 逐个执行测试函数。
    for test_function in test_functions:

        # 调用当前测试函数；如果断言失败，程序会在这里报错停止。
        test_function()

        # 如果没有报错，就打印当前测试通过。
        print(f"通过：{test_function.__name__}")

    # 所有测试都执行完后，打印最终成功信息。
    print("内存版完整业务流程测试全部通过")
