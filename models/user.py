"""
Abstract base class defining a User.
"""
from abc import ABC, abstractmethod

class User(ABC):
    """Abstract base class representing a generic user in the system.
    
    This class demonstrates abstraction by inheriting from ABC, and encapsulation via property decorators.
    """
    def __init__(self, user_id: int, name: str, username: str, role: str):
        """Initializes a new User instance.
        
        Args:
            user_id (int): The unique database identifier.
            name (str): The real name of the user.
            username (str): The login credential.
            role (str): The permission role (e.g., student, teacher, admin).
        """
        self.__id = user_id
        self.__name = name
        self.__username = username
        self.__role = role

    # Read-only access to the user's database ID.
    @property
    def id(self) -> int:
        """Returns the user's unique database ID."""
        return self.__id

    # Read-only access to the user's full name.
    @property
    def name(self) -> str:
        """Returns the user's full name."""
        return self.__name

    # Read-only access to the login username.
    @property
    def username(self) -> str:
        """Returns the user's login username."""
        return self.__username

    # Read-only access to the user's role string.
    @property
    def role(self) -> str:
        """Returns the user's role (e.g. 'student', 'teacher', 'admin')."""
        return self.__role

    # Subclasses must implement this to supply their dashboard data dict.
    @abstractmethod
    def get_dashboard_data(self):
        """Returns a dict of data to display on the user's dashboard."""
        pass

    # Subclasses must implement this to declare what actions they can perform.
    @abstractmethod
    def get_permissions(self) -> list[str]:
        """Returns the list of permission strings granted to this user."""
        pass

    # Checks whether a given permission string is in the user's permission list.
    def has_permission(self, permission: str) -> bool:
        """Returns True if the user holds the specified permission.

        Args:
            permission (str): The permission string to test.

        Returns:
            bool: True if the permission exists in get_permissions().
        """
        return permission in self.get_permissions()

    # Subclasses must implement this to generate a formatted text report.
    @abstractmethod
    def generate_report(self):
        """Returns a formatted text report describing the user's activity or status."""
        pass

    # Constructs a User instance from a DB row (tuple or dict).
    @classmethod
    def from_db_row(cls, row):
        """Creates a User instance from a database row.

        Accepts either a dict (from a DictCursor) or a plain tuple.

        Args:
            row (dict | tuple): The database row data.

        Returns:
            User: A new User instance populated from the row.
        """
        if isinstance(row, dict):
            return cls(
                user_id=row['id'],
                name=row['name'],
                username=row['username'],
                role=row['role']
            )
        else:
            return cls(
                user_id=row[0],
                name=row[1],
                username=row[2],
                role=row[4]
            )

    # Returns a readable one-line summary of the user for display purposes.
    def __str__(self) -> str:
        """Returns a human-readable string: 'Role: Name (username)'."""
        return f"{self.role.capitalize()}: {self.name} ({self.username})"

    # Returns a detailed string useful for debugging in a REPL or log.
    def __repr__(self) -> str:
        """Returns a detailed string representation for debugging."""
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}', username='{self.username}', role='{self.role}')"
