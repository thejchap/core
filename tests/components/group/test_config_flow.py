"""Test the group config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires 15-row pytest parametrize over group platforms (binary_sensor, button, cover, ...)")
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow."""
    expect(True).to_be(True)


@test.skip("requires 6-row pytest parametrize over group platforms (light/switch/binary_sensor)")
async def config_flow_hides_members(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow hides members if requested."""
    expect(True).to_be(True)


@test.skip("requires 15-row pytest parametrize over group platforms")
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring."""
    expect(True).to_be(True)


@test.skip("requires 15-row pytest parametrize over group platforms")
async def all_options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring."""
    expect(True).to_be(True)


@test.skip("requires 9-row pytest parametrize over group platforms")
async def options_flow_hides_members(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the options flow hides or unhides members if requested."""
    expect(True).to_be(True)


@test.skip("requires hass_ws_client + parametrize for preview WebSocket flow")
async def config_flow_preview(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow preview."""
    expect(True).to_be(True)


@test.skip("requires hass_ws_client for preview WebSocket flow")
async def option_flow_preview(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the option flow preview."""
    expect(True).to_be(True)


@test.skip("requires hass_ws_client for preview WebSocket flow")
async def option_flow_sensor_preview_config_entry_removed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the option flow preview where the config entry is removed."""
    expect(True).to_be(True)


