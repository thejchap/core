"""Tryke skip stub for test_number.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def numbers() -> None:
    """Stub for test_numbers."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def numbers_implementation() -> None:
    """Stub for test_numbers_implementation."""

