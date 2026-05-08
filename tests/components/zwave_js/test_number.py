"""Tryke skip-stubs for test_number.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def number() -> None:
    """Stub for test_number."""


@test.skip("zwave_js: sibling test pending tryke port")
async def number_no_target_value() -> None:
    """Stub for test_number_no_target_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def number_writeable() -> None:
    """Stub for test_number_writeable."""


@test.skip("zwave_js: sibling test pending tryke port")
async def volume_number() -> None:
    """Stub for test_volume_number."""


@test.skip("zwave_js: sibling test pending tryke port")
async def config_parameter_number() -> None:
    """Stub for test_config_parameter_number."""
