"""The tests for the Ring switch platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def states() -> None:
    """Stub for test_states (port deferred)."""

@test.skip("syrupy snapshot")
async def siren_off_reports_correctly() -> None:
    """Stub for test_siren_off_reports_correctly (port deferred)."""

@test.skip("syrupy snapshot")
async def siren_on_reports_correctly() -> None:
    """Stub for test_siren_on_reports_correctly (port deferred)."""

@test.skip("syrupy snapshot")
async def switch_can_be_turned_on_and_off() -> None:
    """Stub for test_switch_can_be_turned_on_and_off (port deferred)."""

@test.skip("syrupy snapshot")
async def switch_errors_when_turned_on() -> None:
    """Stub for test_switch_errors_when_turned_on (port deferred)."""
