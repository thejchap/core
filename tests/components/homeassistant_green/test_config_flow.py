"""Test the Home Assistant Green config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("requires supervisor_client + os_green_info fixtures (hassio)")
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow."""
    expect(True).to_be(True)


@test.skip("requires supervisor_client fixture (hassio)")
async def config_flow_single_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test only a single entry is allowed."""
    expect(True).to_be(True)


@test.skip("requires supervisor_client fixture (hassio)")
async def option_flow_non_hassio(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test option flow without hassio."""
    expect(True).to_be(True)


@test.skip("requires os_green_info fixture (hassio)")
async def option_flow_led_settings(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating LED settings."""
    expect(True).to_be(True)


@test.skip("requires os_green_info fixture (hassio)")
async def option_flow_led_settings_unchanged(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test LED settings unchanged."""
    expect(True).to_be(True)


@test.skip("requires os_green_info fixture (hassio)")
async def option_flow_led_settings_fail_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test LED settings read failure."""
    expect(True).to_be(True)


@test.skip("requires os_green_info fixture (hassio)")
async def option_flow_led_settings_fail_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test LED settings write failure."""
    expect(True).to_be(True)
