"""Tryke skip stub for test_binary_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_connection_sensor() -> None:
    """Stub for test_remote_connection_sensor."""

