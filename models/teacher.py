# Represents a faculty member who manages subjects and records grades
# Inheritance: Teacher extends User to reuse shared fields like username
# Polymorphism: implements Teacher-specific overrides for dashboard data and reports
from models.user import User

class Teacher(User):
    def __init__(self, user_id, name, username, department):
        super().__init__(user_id=user_id, name=name, username=username, role='teacher')
        self.department = department
        self.subjects = []
