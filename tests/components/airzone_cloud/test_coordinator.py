"""Tryke skip stub for test_coordinator.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_client_connector_error() -> None:
    """Stub for test_coordinator_client_connector_error."""

