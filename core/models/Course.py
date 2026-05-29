from collections import deque, defaultdict
import operator

class Course:
    def __init__(self, course_id, name, credit, teacher, schedule, capacity, prerequisites=None):
        self.id = course_id
        self.course_id = course_id
        self.name = name
        self.credit = credit
        self.teacher = teacher
        self.schedule = schedule
        self.capacity = capacity
        self.prerequisites = prerequisites or []
        self.enrolled_student = set()
        self.enrolled_students = self.enrolled_student
        self._current_count = 0

    @property
    def current_count(self):
        return self._current_count

    @current_count.setter
    def current_count(self, value):
        self._current_count = value

    @property
    def course_count(self):
        return self._current_count

    @course_count.setter
    def course_count(self, value):
        self._current_count = value
