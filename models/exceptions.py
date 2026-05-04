"""
Custom exceptions for the ScholarTrack application.

Each exception inherits from an appropriate built-in base so callers can
catch them at either the specific or the generic level.
"""


class AuthenticationError(Exception):
    """Raised when a login attempt fails due to invalid credentials.

    Inherits from Exception so it can be caught alongside other general errors.
    """
    pass


class InvalidGradeError(ValueError):
    """Raised when a grade or GPA value falls outside the accepted range.

    Inherits from ValueError because an invalid grade is a kind of bad value,
    making it compatible with callers that already catch ValueError.

    Example:
        raise InvalidGradeError("GPA 5.0 is not in the 0.0–4.0 range.")
    """
    pass


class DatabaseError(Exception):
    """Raised when a database operation fails unexpectedly.

    Wrap low-level sqlite3 errors in this type so the rest of the application
    does not need to import sqlite3 just to handle DB failures.

    Example:
        raise DatabaseError("Could not connect to tracker.db.")
    """
    pass


class PermissionDeniedError(Exception):
    """Raised when a user tries to perform an action they are not authorised for.

    Provides a clear separation between authentication failures (wrong password)
    and authorisation failures (correct user, wrong role).
    """
    pass
