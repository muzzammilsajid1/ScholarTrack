# Represents a system administrator with broad privileges and analytical views
# Inheritance: Admin extends User to avoid duplicating shared properties
# Polymorphism: Admin overrides methods to supply global statistics rather than individual data
# Encapsulation: Admin hides regex rules inside a simple validate_username utility method
import re
from models.user import User

class Admin(User):
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

    # Extract required metrics so the dashboard can render without knowing the internal structure
    def get_dashboard_data(self):
        return {
            "total_students": self.system_stats.get("total_students", 0),
            "total_teachers": self.system_stats.get("total_teachers", 0),
            "total_subjects": self.system_stats.get("total_subjects", 0),
            "at_risk_students": self.system_stats.get("at_risk_students", 0)
        }

    # Grant maximum system-level actions required to manage the LMS
    def get_permissions(self):
        return ["view_all_students", "edit_grades", "view_reports", "manage_users", "generate_pdf", "view_logs"]

    # Assemble high-level KPIs into a readable block for external consumption
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

    # Provide a static utility so any module can enforce uniform username rules
    @staticmethod
    def validate_username(username):
        if not isinstance(username, str):
            return False
        return bool(re.match(r'^\w{3,20}$', username))
