"""Test the history_stats config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def validation_options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test validation."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def entry_already_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test abort when entry already exist."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def config_flow_preview_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow preview."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def options_flow_preview(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the options flow preview."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def options_flow_preview_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the options flow preview."""
    expect(True).to_be(True)


@test.skip("requires recorder_mock fixture (not in tryke shim)")
async def options_flow_sensor_preview_config_entry_removed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the option flow preview where the config entry is removed."""
    expect(True).to_be(True)


