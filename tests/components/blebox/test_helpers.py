"""Tryke skip stub for test_helpers.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def get_maybe_authenticated_session_none() -> None:
    """Stub for test_get_maybe_authenticated_session_none."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def get_maybe_authenticated_session_auth() -> None:
    """Stub for test_get_maybe_authenticated_session_auth."""

