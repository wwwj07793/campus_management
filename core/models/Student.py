from collections import defaultdict
CS = "计算机科学与技术学院"
WL = "文学院"
WY = "外国语学院"
SX = "数学与统计学院"
JJ = "经济学院"
GL = "管理学院"
DX = "电子信息工程学院"
JX = "机械工程学院"
FX = "法学院"
MS = "美术学院"
DEPARTMENT_LIST = [CS, WL, WY, SX, JJ, GL, DX, JX, FX, MS]
FI = "2025级"
SE = "2024级"
TH = "2023级"
FO = "2022级"
GRADE_LIST = [FI, SE, TH, FO]
class Student:
    def __init__(self, student_id, name, gender, birth_date, department, grade):
        self.id = student_id
        self.student_id = student_id
        self.name = name
        self.gender = gender
        self.birth_date = birth_date
        self.department = department
        self.grade = grade
        self.enrolled_course = {}
        self.enrolled_courses = self.enrolled_course
        self.entrolled_course = self.enrolled_course
        self.gpa = 0.0

    
