"""
Student model class.
"""
from models.user import User
from models.exceptions import InvalidGradeError

class Student(User):
    """Represents a student user within the system.
    
    This class demonstrates inheritance by sub-classing User, and encapsulation by protecting properties like GPA.
    """
    def __init__(self, student_id: int, name: str, username: str, semester: int, department: str):
        """Initializes a Student instance.
        
        Args:
            student_id (int): The unique database identifier.
            name (str): The real name of the student.
            username (str): The login credential.
            semester (int): The current semester numeral.
            department (str): The student's department.
        """
        super().__init__(user_id=student_id, name=name, username=username, role='student')
        self.__semester = semester
        self.__department = department
        self.__gpa = 0.0
        self.__grades = []

    @property
    def semester(self) -> int:
        """Retrieves the student's semester.
        
        Returns:
            int: The current semester.
        """
        return self.__semester

    @property
    def department(self) -> str:
        """Retrieves the student's department.
        
        Returns:
            str: The department name.
        """
        return self.__department

    @property
    def gpa(self) -> float:
        """Retrieves the student's cumulative GPA.
        
        Returns:
            float: The GPA value.
        """
        return self.__gpa

    @gpa.setter
    def gpa(self, value: float):
        """Sets the student's cumulative GPA safely.
        
        Args:
            value (float): The new GPA value.
            
        Raises:
            InvalidGradeError: If the GPA is not between 0.0 and 4.0.
        """
        if not (0.0 <= value <= 4.0):
            raise InvalidGradeError(f"GPA {value} must be between 0.0 and 4.0")
        self.__gpa = value

    @property
    def grades(self) -> list:
        """Retrieves the student's grade records.
        
        Returns:
            list: The list of grade entries.
        """
        return self.__grades

    @grades.setter
    def grades(self, value: list):
        """Sets the student's grade records list.
        
        Args:
            value (list): The list of grades.
        """
        self.__grades = value

    # Returns the list of actions this role is allowed to perform.
    def get_permissions(self) -> list[str]:
        """Returns the permissions granted to a student.

        Returns:
            list[str]: A list of permission strings for the student role.
        """
        return ["view_own_grades", "view_own_report", "get_ai_feedback"]

    # Maps the student's GPA to a human-readable performance category.
    @property
    def performance_label(self) -> str:
        """Returns a performance label string based on the student's GPA.

        Returns:
            str: One of 'Excellent', 'Good', 'Average', or 'At Risk'.
        """
        if self.gpa >= 3.5:
            return "Excellent"
        elif self.gpa >= 3.0:
            return "Good"
        elif self.gpa >= 2.0:
            return "Average"
        else:
            return "At Risk"

    # Returns a dict of key student data for the dashboard view.
    def get_dashboard_data(self) -> dict:
        """Returns the data dictionary shown on the student's dashboard.

        Returns:
            dict: Keys are name, gpa, semester, department, and grades.
        """
        return {
            "name": self.name,
            "gpa": self.gpa,
            "semester": self.semester,
            "department": self.department,
            "grades": self.grades
        }

    # Builds a plain-text performance report for this student.
    def generate_report(self) -> str:
        """Returns a formatted plain-text report of the student's grades and GPA.

        Returns:
            str: Multi-line report string.
        """
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

    # Allows sorting students by GPA using the < operator.
    def __lt__(self, other) -> bool:
        """Compares two Student objects by GPA (ascending order).

        Args:
            other (Student): The student to compare against.

        Returns:
            bool: True if this student's GPA is lower than the other's.
        """
        if not isinstance(other, Student):
            return NotImplemented
        return self.gpa < other.gpa

    # Checks whether two Student objects represent the same person.
    def __eq__(self, other) -> bool:
        """Checks equality between two Student objects based on their ID."""
        if not isinstance(other, Student):
            return NotImplemented
        return self.id == other.id

    # Makes Student instances hashable so they can be stored in sets or dict keys.
    def __hash__(self) -> int:
        """Returns hash based on the student's class and ID."""
        return hash(("Student", self.id))

    # Constructs a Student object directly from a DB row tuple or dict.
    @classmethod
    def from_db_row(cls, row):
        """Creates a Student instance from a database row.

        Accepts either a dict (from a DictCursor) or a plain tuple.

        Args:
            row (tuple | dict): The database row data.

        Returns:
            Student: A new Student instance populated from the row.
        """
        if isinstance(row, dict):
            return cls(
                student_id=row['id'],
                name=row['name'],
                username=row['username'],
                semester=row['semester'],
                department=row['department']
            )
        else:
            return cls(
                student_id=row[0],
                name=row[1],
                username=row[2],
                semester=row[3],
                department=row[4]
            )
