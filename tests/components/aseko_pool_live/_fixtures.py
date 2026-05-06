"""Tryke fixtures for Aseko Pool Live."""

from datetime import datetime

from aioaseko import User
from tryke import fixture


@fixture
def user() -> User:
    """Aseko User fixture."""
    return User(
        user_id="a_user_id",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        name="John",
        surname="Doe",
        language="any_language",
        is_active=True,
    )
