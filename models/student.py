# Represents a student entity within the academic tracking system
# Inheritance: Student extends User to inherit common identity attributes without repeating code
# Polymorphism: overrides abstract User methods to return student-specific dashboard data and privileges
from models.user import User

class Student(User):
    def __init__(self, user_id, student_id, name, username, semester, department):
        super().__init__(user_id=user_id, name=name, username=username, role='student')
        self.student_id = student_id
        self.semester = semester
        self.department = department
        self.gpa = 0.0
        self.grades = []

