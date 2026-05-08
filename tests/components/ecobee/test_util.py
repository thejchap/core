"""Tryke skip stub for test_util.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ecobee_date_with_valid_input() -> None:
    """Stub for test_ecobee_date_with_valid_input."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ecobee_date_with_invalid_input() -> None:
    """Stub for test_ecobee_date_with_invalid_input."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ecobee_time_with_valid_input() -> None:
    """Stub for test_ecobee_time_with_valid_input."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ecobee_time_with_invalid_input() -> None:
    """Stub for test_ecobee_time_with_invalid_input."""

