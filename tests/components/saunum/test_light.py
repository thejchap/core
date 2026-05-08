"""Test the Saunum light platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def entities() -> None:
    """Stub for test_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def light_service_calls() -> None:
    """Stub for test_light_service_calls (port deferred)."""

@test.skip("syrupy snapshot")
async def light_service_call_failure() -> None:
    """Stub for test_light_service_call_failure (port deferred)."""
