"""Tryke skip-stubs for test_diagnostics.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def config_entry_diagnostics() -> None:
    """Stub for test_config_entry_diagnostics."""


@test.skip("zwave_js: sibling test pending tryke port")
async def device_diagnostics() -> None:
    """Stub for test_device_diagnostics."""


@test.skip("zwave_js: sibling test pending tryke port")
async def device_diagnostics_error() -> None:
    """Stub for test_device_diagnostics_error."""


@test.skip("zwave_js: sibling test pending tryke port")
async def empty_zwave_value_matcher() -> None:
    """Stub for test_empty_zwave_value_matcher."""


@test.skip("zwave_js: sibling test pending tryke port")
async def device_diagnostics_missing_primary_value() -> None:
    """Stub for test_device_diagnostics_missing_primary_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def device_diagnostics_secret_value() -> None:
    """Stub for test_device_diagnostics_secret_value."""
