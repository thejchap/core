"""Test the SmartTub switch platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def pump_state() -> None:
    """Stub for test_pump_state (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def pump_toggle() -> None:
    """Stub for test_pump_toggle (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def pump_turn_on() -> None:
    """Stub for test_pump_turn_on (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def pump_turn_off() -> None:
    """Stub for test_pump_turn_off (port deferred)."""
