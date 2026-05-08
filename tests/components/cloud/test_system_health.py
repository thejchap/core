"""Tryke skip stub for test_system_health.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def cloud_system_health() -> None:
    """Stub for test_cloud_system_health."""

