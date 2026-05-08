"""Tryke skip-stubs for test_select.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def default_tone_select() -> None:
    """Stub for test_default_tone_select."""


@test.skip("zwave_js: sibling test pending tryke port")
async def protection_select() -> None:
    """Stub for test_protection_select."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multilevel_switch_select() -> None:
    """Stub for test_multilevel_switch_select."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multilevel_switch_select_no_value() -> None:
    """Stub for test_multilevel_switch_select_no_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def config_parameter_select() -> None:
    """Stub for test_config_parameter_select."""


@test.skip("zwave_js: sibling test pending tryke port")
async def lock_popp_electric_strike_lock_control_select() -> None:
    """Stub for test_lock_popp_electric_strike_lock_control_select."""
