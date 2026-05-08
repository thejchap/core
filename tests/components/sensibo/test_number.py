"""The test for the sensibo number platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def number() -> None:
    """Stub for test_number (port deferred)."""

@test.skip("syrupy snapshot")
async def number_set_value() -> None:
    """Stub for test_number_set_value (port deferred)."""
