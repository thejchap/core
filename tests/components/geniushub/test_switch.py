"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cloud_all_sensors() -> None:
    """Stub for test_cloud_all_sensors."""

