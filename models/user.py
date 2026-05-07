# Base class defining core attributes and methods for all system users
# Abstraction: acts as a blueprint forcing subclasses to implement specific behaviors
# Encapsulation: bundles shared identity attributes so subclasses don't repeat them

class User:
    def __init__(self, user_id, name, username, role):
        self.id = user_id
        self.name = name
        self.username = username
        self.role = role

    # Allow subclasses to provide the exact data their specific view requires
    def get_dashboard_data(self):
        pass

    # Force subclasses to explicitly define their unique system privileges
    def get_permissions(self):
        pass

    # Provide a unified way for any client code to verify access rights
    def has_permission(self, permission):
        return permission in self.get_permissions()

    # Enable polymorphic reporting where each role outputs its own custom layout
    def generate_report(self):
        pass
