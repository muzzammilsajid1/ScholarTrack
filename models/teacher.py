# Teacher model class.
from models.user import User

class Teacher(User):
    # Initializes a Teacher instance.
    def __init__(self, teacher_id, name, username, department):
        super().__init__(user_id=teacher_id, name=name, username=username, role='teacher')
        self.department = department
        self.subjects = []

    # Returns the data dict displayed on the teacher's dashboard.
    def get_dashboard_data(self):
        return {
            "name": self.name,
            "department": self.department,
            "subjects": self.subjects
        }

    # Returns the list of actions a teacher is allowed to perform.
    def get_permissions(self):
        return ["view_all_students", "edit_grades", "view_reports"]

    # Builds a plain-text report listing all subjects and their class averages.
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
