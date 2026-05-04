"""
Admin model class.
"""
import re
from models.user import User

class Admin(User):
    """Represents a system administrator with global permissions.
    
    This class demonstrates inheritance by sub-classing User, and encapsulation through validated access levels.
    """
    def __init__(self, admin_id: int, name: str, username: str, access_level: int = 1):
        """Initializes an Admin instance.
        
        Args:
            admin_id (int): The unique database identifier.
            name (str): The real name of the admin.
            username (str): The login credential.
            access_level (int, optional): Numeric security authority level rating from 1 to 3. Defaults to 1.
        """
        super().__init__(user_id=admin_id, name=name, username=username, role='admin')
        self.access_level = access_level
        
        self.system_stats = {
            "total_students": 0,
            "total_teachers": 0,
            "total_subjects": 0,
            "at_risk_students": 0
        }

    # Read-only access to the admin's clearance level (1–3).
    @property
    def access_level(self) -> int:
        """Returns the admin's numeric access clearance level (1 = lowest, 3 = highest)."""
        return self.__access_level

    # Validates and sets the access level; rejects values outside 1–3.
    @access_level.setter
    def access_level(self, value: int):
        """Sets the admin's access level after validating it is between 1 and 3.

        Args:
            value (int): The desired access level.

        Raises:
            PermissionError: If the value is not an integer in the range 1–3.
        """
        if not isinstance(value, int) or not (1 <= value <= 3):
            raise PermissionError(f"Access level {value} is invalid. Must be between 1 and 3.")
        self.__access_level = value

    # Returns the system statistics dict for display on the admin dashboard.
    def get_dashboard_data(self) -> dict:
        """Returns a dict of current system statistics for the admin dashboard."""
        return {
            "total_students": self.system_stats.get("total_students", 0),
            "total_teachers": self.system_stats.get("total_teachers", 0),
            "total_subjects": self.system_stats.get("total_subjects", 0),
            "at_risk_students": self.system_stats.get("at_risk_students", 0)
        }

    # Returns the full list of actions an admin is permitted to perform.
    def get_permissions(self) -> list[str]:
        """Returns all permissions granted to the admin role."""
        return ["view_all_students", "edit_grades", "view_reports", "manage_users", "generate_pdf", "view_logs"]

    # Produces a formatted plain-text summary of system-wide statistics.
    def generate_report(self) -> str:
        """Returns a formatted plain-text administration report with system statistics."""
        return (
            f"=== System Administration Report ===\n"
            f"Admin: {self.name} ({self.username})\n"
            f"Access Level: {self.access_level}\n"
            f"------------------------------------\n"
            f"Total Enrolled Students: {self.system_stats['total_students']}\n"
            f"Active Teaching Staff:   {self.system_stats['total_teachers']}\n"
            f"Total Subjects Offered:  {self.system_stats['total_subjects']}\n"
            f"Identified At-Risk:      {self.system_stats['at_risk_students']}\n"
            f"===================================="
        )

    # Validates that a username is 3–20 word characters using a regex check.
    @staticmethod
    def validate_username(username: str) -> bool:
        """Returns True if the username is 3–20 alphanumeric/underscore characters.

        Args:
            username (str): The username string to validate.

        Returns:
            bool: True if the username matches the allowed pattern.
        """
        if not isinstance(username, str):
            return False
        return bool(re.match(r'^\w{3,20}$', username))

    # Constructs an Admin object directly from a DB row tuple or dict.
    @classmethod
    def from_db_row(cls, row):
        """Creates an Admin instance from a database row.

        Accepts either a dict (from a DictCursor) or a plain tuple.

        Args:
            row (tuple | dict): The database row data.

        Returns:
            Admin: A new Admin instance populated from the row.
        """
        if isinstance(row, dict):
            return cls(
                admin_id=row['id'],
                name=row['name'],
                username=row['username'],
                access_level=row.get('access_level', 1)
            )
        else:
            return cls(
                admin_id=row[0],
                name=row[1],
                username=row[2],
                access_level=row[3] if len(row) > 3 else 1
            )
