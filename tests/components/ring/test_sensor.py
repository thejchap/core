"""The tests for the Ring sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def states() -> None:
    """Stub for test_states (port deferred)."""

@test.skip("syrupy snapshot")
async def health_sensor() -> None:
    """Stub for test_health_sensor (port deferred)."""

@test.skip("syrupy snapshot")
async def history_sensor() -> None:
    """Stub for test_history_sensor (port deferred)."""

@test.skip("syrupy snapshot")
async def only_chime_devices() -> None:
    """Stub for test_only_chime_devices (port deferred)."""
