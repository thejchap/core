"""Test the Z-Wave JS diagnostics."""

from tryke import expect, test

from homeassistant.components.zwave_js.helpers import ZwaveValueMatcher


@test
def empty_zwave_value_matcher() -> None:
    """Test that an empty ZwaveValueMatcher fails construction."""
    expect(lambda: ZwaveValueMatcher()).to_raise(ValueError)


@test.skip("zwave_js: requires client + integration conftest fixtures")
async def config_entry_diagnostics() -> None:
    """Stub for test_config_entry_diagnostics."""


@test.skip("zwave_js: requires client + integration conftest fixtures")
async def device_diagnostics() -> None:
    """Stub for test_device_diagnostics."""


@test.skip("zwave_js: requires client + integration conftest fixtures")
async def device_diagnostics_error() -> None:
    """Stub for test_device_diagnostics_error."""


@test.skip("zwave_js: requires client + integration conftest fixtures")
async def device_diagnostics_missing_primary_value() -> None:
    """Stub for test_device_diagnostics_missing_primary_value."""


@test.skip("zwave_js: requires client + integration conftest fixtures")
async def device_diagnostics_secret_value() -> None:
    """Stub for test_device_diagnostics_secret_value."""
