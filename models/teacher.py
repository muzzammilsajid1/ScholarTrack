"""
Teacher model class.
"""
from models.user import User

class Teacher(User):
    """Represents an instructor user in the system.
    
    This class demonstrates inheritance by sub-classing User, and encapsulation by managing department and subjects privately.
    """
    def __init__(self, teacher_id: int, name: str, username: str, department: str):
        """Initializes a Teacher instance.
        
        Args:
            teacher_id (int): The unique database identifier.
            name (str): The real name of the teacher.
            username (str): The login credential.
            department (str): The teacher's academic department.
        """
        super().__init__(user_id=teacher_id, name=name, username=username, role='teacher')
        self.__department = department
        self.__subjects = []

    # Read-only access to the teacher's academic department.
    @property
    def department(self) -> str:
        """Returns the teacher's department name."""
        return self.__department

    # Read-only access to the list of subjects assigned to this teacher.
    @property
    def subjects(self) -> list:
        """Returns the list of subjects managed by this teacher."""
        return self.__subjects

    # Allows the subjects list to be replaced (e.g. after a DB refresh).
    @subjects.setter
    def subjects(self, value: list):
        """Replaces the teacher's subjects list.

        Args:
            value (list): The new list of subjects.
        """
        self.__subjects = value

    # Returns the data dict displayed on the teacher's dashboard.
    def get_dashboard_data(self) -> dict:
        """Returns a dict of the teacher's name, department, and assigned subjects."""
        return {
            "name": self.name,
            "department": self.department,
            "subjects": self.subjects
        }

    # Returns the list of actions a teacher is allowed to perform.
    def get_permissions(self) -> list[str]:
        """Returns the permissions granted to a teacher."""
        return ["view_all_students", "edit_grades", "view_reports"]

    # Builds a plain-text report listing all subjects and their class averages.
    def generate_report(self) -> str:
        """Returns a formatted text report of the teacher's subject assignments."""
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

    # Constructs a Teacher object directly from a DB row tuple or dict.
    @classmethod
    def from_db_row(cls, row):
        """Creates a Teacher instance from a database row.

        Accepts either a dict (from a DictCursor) or a plain tuple.

        Args:
            row (tuple | dict): The database row data.

        Returns:
            Teacher: A new Teacher instance populated from the row.
        """
        if isinstance(row, dict):
            return cls(
                teacher_id=row['id'],
                name=row['name'],
                username=row['username'],
                department=row.get('department', 'General')
            )
        else:
            return cls(
                teacher_id=row[0],
                name=row[1],
                username=row[2],
                department=row[3] if len(row) > 3 else 'General'
            )
