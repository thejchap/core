"""The test for the sensibo entity. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def device() -> None:
    """Stub for test_device (port deferred)."""

@test.skip("syrupy snapshot")
async def entity_failed_service_calls() -> None:
    """Stub for test_entity_failed_service_calls (port deferred)."""
