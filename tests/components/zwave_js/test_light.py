"""Tryke skip-stubs for test_light.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def light() -> None:
    """Stub for test_light."""


@test.skip("zwave_js: sibling test pending tryke port")
async def v4_dimmer_light() -> None:
    """Stub for test_v4_dimmer_light."""


@test.skip("zwave_js: sibling test pending tryke port")
async def optional_light() -> None:
    """Stub for test_optional_light."""


@test.skip("zwave_js: sibling test pending tryke port")
async def rgbw_light() -> None:
    """Stub for test_rgbw_light."""


@test.skip("zwave_js: sibling test pending tryke port")
async def light_none_color_value() -> None:
    """Stub for test_light_none_color_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def light_on_off_color() -> None:
    """Stub for test_light_on_off_color."""


@test.skip("zwave_js: sibling test pending tryke port")
async def light_color_only() -> None:
    """Stub for test_light_color_only."""


@test.skip("zwave_js: sibling test pending tryke port")
async def basic_cc_light() -> None:
    """Stub for test_basic_cc_light."""
