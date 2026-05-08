"""Tryke skip-stubs for test_humidifier.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def humidifier() -> None:
    """Stub for test_humidifier."""


@test.skip("zwave_js: sibling test pending tryke port")
async def dehumidifier_missing_setpoint() -> None:
    """Stub for test_dehumidifier_missing_setpoint."""


@test.skip("zwave_js: sibling test pending tryke port")
async def humidifier_missing_mode() -> None:
    """Stub for test_humidifier_missing_mode."""


@test.skip("zwave_js: sibling test pending tryke port")
async def dehumidifier() -> None:
    """Stub for test_dehumidifier."""
