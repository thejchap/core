"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def local_awair_sensors() -> None:
    """Stub for test_local_awair_sensors."""

