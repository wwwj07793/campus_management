# 自定义业务异常基类
class BusinessException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(self.message)

    def error_detail(self, index, student_id):
        print(f"第{index}行学号为{student_id}的同学导入失败")

# 常用业务异常
#可以用多态思想解决异常捕获问题，多态{
# 多态实现：父类接口， 多子类重写
# 多态使用：形参父类实例， 实参子类实例}

class StudentNotExistException(BusinessException):
    def __init__(self):
        super().__init__(404, "学生不存在")


class CourseNotExistException(BusinessException):
    def __init__(self):
        super().__init__(404, "课程不存在")


class CourseConflictException(BusinessException):
    def __init__(self):
        super().__init__(400, "选课冲突")


class DateError(BusinessException):
    def __init__(self, student_id):
        self.student_id = student_id
        super().__init__(400, "日期格式错误(2000-01-01)")


class GradeError(BusinessException):
    def __init__(self, student_id):
        self.student_id = student_id
        super().__init__(400, "年级格式错误(2025)")


class GenderError(BusinessException):
    def __init__(self, student_id):
        self.student_id = student_id
        super().__init__(400, "请输入(男/女)")
