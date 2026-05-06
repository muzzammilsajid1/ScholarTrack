# Base class defining a User.

class User:
    # Initializes a new User instance.
    def __init__(self, user_id, name, username, role):
        self.id = user_id
        self.name = name
        self.username = username
        self.role = role

    # Subclasses must implement this to supply their dashboard data dict.
    def get_dashboard_data(self):
        pass

    # Subclasses must implement this to declare what actions they can perform.
    def get_permissions(self):
        pass

    # Checks whether a given permission string is in the user's permission list.
    def has_permission(self, permission):
        return permission in self.get_permissions()

    # Subclasses must implement this to generate a formatted text report.
    def generate_report(self):
        pass
