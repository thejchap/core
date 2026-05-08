"""Tryke skip stub for test_water_heater.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cloud_all_water_heaters() -> None:
    """Stub for test_cloud_all_water_heaters."""

