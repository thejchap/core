"""Tryke skip-stubs for test_switch.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def switch() -> None:
    """Stub for test_switch."""


@test.skip("zwave_js: sibling test pending tryke port")
async def barrier_signaling_switch() -> None:
    """Stub for test_barrier_signaling_switch."""


@test.skip("zwave_js: sibling test pending tryke port")
async def switch_no_value() -> None:
    """Stub for test_switch_no_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def config_parameter_switch() -> None:
    """Stub for test_config_parameter_switch."""
