"""
Database ORM models.

Warning: you should not import any aiogram objects here, including other modules that import aiogram objects.
Aiogram imports and installs uvloop, which is not compatible with aerich (migration tool used).
See https://github.com/tortoise/aerich/issues/129.
"""

from .invite import JourneyInvite
from .journey import Journey, JourneyLocation, JourneyNote
from .user import User

__all__ = ["JourneyInvite", "Journey", "JourneyLocation", "JourneyNote", "User"]
