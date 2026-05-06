# Admin model class.
import re
from models.user import User

class Admin(User):
    # Initializes an Admin instance.
    def __init__(self, admin_id, name, username, access_level=1):
        super().__init__(user_id=admin_id, name=name, username=username, role='admin')
        
        if not isinstance(access_level, int) or not (1 <= access_level <= 3):
            raise PermissionError(f"Access level {access_level} is invalid. Must be between 1 and 3.")
        self.access_level = access_level
        
        self.system_stats = {
            "total_students": 0,
            "total_teachers": 0,
            "total_subjects": 0,
            "at_risk_students": 0
        }

    # Returns the system statistics dict for display on the admin dashboard.
    def get_dashboard_data(self):
        return {
            "total_students": self.system_stats.get("total_students", 0),
            "total_teachers": self.system_stats.get("total_teachers", 0),
            "total_subjects": self.system_stats.get("total_subjects", 0),
            "at_risk_students": self.system_stats.get("at_risk_students", 0)
        }

    # Returns the full list of actions an admin is permitted to perform.
    def get_permissions(self):
        return ["view_all_students", "edit_grades", "view_reports", "manage_users", "generate_pdf", "view_logs"]

    # Produces a formatted plain-text summary of system-wide statistics.
    def generate_report(self):
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

    # Validates that a username is 3–20 word characters.
    @staticmethod
    def validate_username(username):
        if not isinstance(username, str):
            return False
        return bool(re.match(r'^\w{3,20}$', username))
