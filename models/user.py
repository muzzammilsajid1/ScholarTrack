# Base class defining core attributes and methods for all system users
# Abstraction: acts as a blueprint forcing subclasses to implement role-specific permissions
# Encapsulation: bundles shared identity attributes so subclasses don't repeat them

from abc import ABC, abstractmethod

class User(ABC):
    def __init__(self, user_id, name, username, role):
        self.id = user_id
        self.name = name
        self.username = username
        self.role = role

    # Force subclasses to explicitly define their unique system privileges
    @abstractmethod
    def get_permissions(self):
        pass

    # Provide a unified way for any client code to verify access rights
    def has_permission(self, permission):
        return permission in self.get_permissions()
