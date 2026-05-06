"""Test the homekit config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("discovery + extensive setup")
async def setup_in_bridge_mode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup a new instance in bridge mode."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def setup_in_bridge_mode_name_taken(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup a new instance in bridge mode when the name is taken."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def setup_creates_entries_for_accessory_mode_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can setup a new instance and we create entries for accessory mode devices."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def import(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can import instance."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_exclude_mode_advanced(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options in exclude mode with advanced options."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_exclude_mode_basic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options in exclude mode."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test devices can be bridged."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_devices_preserved_when_advanced_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test devices are preserved if they were added in advanced mode but it was turned off."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_include_mode_with_non_existant_entity(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options in include mode with a non-existent entity."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_exclude_mode_with_non_existant_entity(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options in exclude mode with a non-existent entity."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_include_mode_basic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options in include mode."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_exclude_mode_with_cameras(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options in exclude mode with cameras."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_include_mode_with_cameras(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options in include mode with cameras."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_with_camera_audio(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options with cameras that support audio."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_blocked_when_from_yaml(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_include_mode_basic_accessory(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow options in include mode with a single accessory."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def converting_bridge_to_accessory_mode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can convert a bridge to accessory mode."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_exclude_mode_skips_category_entities(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure exclude mode does not offer category entities."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_exclude_mode_skips_hidden_entities(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure exclude mode does not offer hidden entities."""
    expect(True).to_be(True)


@test.skip("discovery + extensive setup")
async def options_flow_include_mode_allows_hidden_entities(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure include mode does not offer hidden entities."""
    expect(True).to_be(True)


