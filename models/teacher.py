# Represents a faculty member who manages subjects and records grades
# Inheritance: Teacher extends User to reuse shared fields like username
# Polymorphism: implements Teacher-specific overrides for dashboard data and reports
from models.user import User

class Teacher(User):
    def __init__(self, teacher_id, name, username, department):
        super().__init__(user_id=teacher_id, name=name, username=username, role='teacher')
        self.department = department
        self.subjects = []

    # Package internal instance state so the view layer can display it without tight coupling
    def get_dashboard_data(self):
        return {
            "name": self.name,
            "department": self.department,
            "subjects": self.subjects
        }

    # Explicitly list the privileges this role requires for authorization checks
    def get_permissions(self):
        return ["view_all_students", "edit_grades", "view_reports"]

    # Generate a formatted text summary of assigned subjects to simplify printing
    def generate_report(self):
        report_lines = [
            f"--- Teacher Report ---",
            f"Instructor: {self.name} ({self.username})",
            f"Department: {self.department}",
            "--- Subject Class Averages ---"
        ]
        
        if not self.subjects:
            report_lines.append("No subjects assigned currently.")
        else:
            for subject in self.subjects:
                if isinstance(subject, dict):
                    name = subject.get('name', 'Unknown Subject')
                    code = subject.get('code', 'N/A')
                    students = subject.get('students_count', 0)
                    avg = subject.get('average', 0.0)
                    
                    report_lines.append(f"[{code}] {name}")
                    report_lines.append(f"  - Active Students: {students}")
                    report_lines.append(f"  - Class Average:   {avg:.2f}")
                else:
                    report_lines.append(str(subject))
                    
        return "\n".join(report_lines)
