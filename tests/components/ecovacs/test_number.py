"""Tryke skip stub for test_number.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def number_entities() -> None:
    """Stub for test_number_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def disabled_by_default_number_entities() -> None:
    """Stub for test_disabled_by_default_number_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def volume_maximum() -> None:
    """Stub for test_volume_maximum."""

