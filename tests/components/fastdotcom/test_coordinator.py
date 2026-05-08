"""Tryke skip stub for test_coordinator.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fastdotcom_data_update_coordinator() -> None:
    """Stub for test_fastdotcom_data_update_coordinator."""

