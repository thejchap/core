"""Tryke skip stub for test_helpers.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def default_language_codes() -> None:
    """Stub for test_default_language_codes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def default_language_code() -> None:
    """Stub for test_default_language_code."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def best_matching_language_code() -> None:
    """Stub for test_best_matching_language_code."""

