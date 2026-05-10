# Base class defining core attributes and methods for all system users
# Abstraction: acts as a blueprint forcing subclasses to implement role-specific permissions
# Encapsulation: bundles shared identity attributes so subclasses don't repeat them

class User:
    def __init__(self, user_id, name, username, role):
        self.id = user_id
        self.name = name
        self.username = username
        self.role = role
