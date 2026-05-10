# Represents a system administrator with broad privileges
# Inheritance: Admin extends User to avoid duplicating shared properties
# Encapsulation: Admin hides regex rules inside a simple validate_username utility method
import re
from models.user import User

class Admin(User):
    def __init__(self, user_id, name, username, access_level=1):
        super().__init__(user_id=user_id, name=name, username=username, role='admin')

    # Grant maximum system-level actions required to manage the LMS
    def get_permissions(self):
        return ["view_all_students", "edit_grades", "view_reports", "manage_users", "generate_pdf", "view_logs"]

    # Provide a static utility so any module can enforce uniform username rules
    @staticmethod
    def validate_username(username):
        if not isinstance(username, str):
            return False
        return bool(re.match(r'^\w{3,20}$', username))
