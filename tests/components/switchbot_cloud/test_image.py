"""Test for the switchbot_cloud image. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def coordinator_data_is_none() -> None:
    """Stub for test_coordinator_data_is_none (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_image() -> None:
    """Stub for test_async_image (port deferred)."""
