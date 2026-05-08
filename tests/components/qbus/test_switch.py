"""Test Qbus switch entities. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("mqtt_mock not in shim")
async def switch_turn_on_off() -> None:
    """Stub for test_switch_turn_on_off (port deferred)."""
