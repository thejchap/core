"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def smoke_test_setup_component() -> None:
    """Stub for test_smoke_test_setup_component."""

