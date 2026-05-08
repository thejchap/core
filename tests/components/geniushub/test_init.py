"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cloud_unique_id_migration() -> None:
    """Stub for test_cloud_unique_id_migration."""

