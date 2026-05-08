"""Tryke skip stub for test_number.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def number_entities() -> None:
    """Stub for test_number_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def number_set_value() -> None:
    """Stub for test_number_set_value."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def number_error() -> None:
    """Stub for test_number_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def number_entities_unavailable_on_error() -> None:
    """Stub for test_number_entities_unavailable_on_error."""

