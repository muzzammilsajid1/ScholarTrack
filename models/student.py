# Represents a student entity within the academic tracking system
# Inheritance: Student extends User to inherit common identity attributes without repeating code
# Polymorphism: overrides abstract User methods to return student-specific dashboard data and privileges
from models.user import User

class Student(User):
    def __init__(self, student_id, name, username, semester, department):
        super().__init__(user_id=student_id, name=name, username=username, role='student')
        self.semester = semester
        self.department = department
        self.gpa = 0.0
        self.grades = []

    # Define the exact actions this specific role is allowed to perform system-wide
    def get_permissions(self):
        return ["view_own_grades", "view_own_report", "get_ai_feedback"]

    # Translate numeric GPA into human-readable tiers to simplify UI logic
    def get_performance_label(self):
        if self.gpa >= 3.5:
            return "Excellent"
        elif self.gpa >= 3.0:
            return "Good"
        elif self.gpa >= 2.0:
            return "Average"
        else:
            return "At Risk"

    # Format internal state into a generic dictionary so the view layer can bind to it
    def get_dashboard_data(self):
        return {
            "name": self.name,
            "gpa": self.gpa,
            "semester": self.semester,
            "department": self.department,
            "grades": self.grades
        }

    # Construct a standardized text layout of academic standing for easy export
    def generate_report(self):
        report_lines = [
            f"--- Performance Report ---",
            f"Student: {self.name} ({self.username})",
            f"Department: {self.department} | Semester: {self.semester}",
            f"Current Cumulative GPA: {self.gpa:.2f}",
            "--- Grades ---"
        ]
        
        if not self.grades:
            report_lines.append("No grades available.")
        else:
            for grade in self.grades:
                if isinstance(grade, tuple) and len(grade) >= 5:
                    report_lines.append(f"[{grade[2]}] {grade[1]}: {grade[3]} ({grade[4]})")
                elif isinstance(grade, dict):
                    report_lines.append(f"[{grade.get('code')}] {grade.get('name')}: {grade.get('score')} ({grade.get('letter')})")
                else:
                    report_lines.append(str(grade))
                    
        return "\n".join(report_lines)
