"""Test Dynalite light."""

from unittest.mock import Mock, PropertyMock

from dynalite_devices_lib.light import DynaliteChannelLightDevice
from tryke import Depends, expect, fixture, test

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_SUPPORTED_COLOR_MODES,
    ColorMode,
)
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant, State

from .common import (
    ATTR_METHOD,
    ATTR_SERVICE,
    create_entity_from_device,
    create_mock_device,
    get_entry_id_from_hass,
    run_service_tests,
)

from tests.common import mock_restore_cache
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@fixture
def mock_device():
    """Mock a Dynalite device."""
    mock_dev = create_mock_device("light", DynaliteChannelLightDevice)
    mock_dev.brightness = 0

    def mock_is_on():
        return mock_dev.brightness != 0

    type(mock_dev).is_on = PropertyMock(side_effect=mock_is_on)

    def mock_init_level(target):
        mock_dev.brightness = target

    type(mock_dev).init_level = Mock(side_effect=mock_init_level)
    return mock_dev


@test
async def light_setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device=Depends(mock_device),
) -> None:
    """Test a successful setup."""
    await create_entity_from_device(hass, mock_device)
    entity_state = hass.states.get("light.name")
    expect(entity_state.attributes[ATTR_FRIENDLY_NAME]).to_equal(mock_device.name)
    expect(entity_state.attributes[ATTR_SUPPORTED_COLOR_MODES]).to_equal(
        [ColorMode.BRIGHTNESS]
    )
    expect(entity_state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(0)
    expect(entity_state.state).to_equal(STATE_OFF)
    await run_service_tests(
        hass,
        mock_device,
        "light",
        [
            {ATTR_SERVICE: "turn_on", ATTR_METHOD: "async_turn_on"},
            {ATTR_SERVICE: "turn_off", ATTR_METHOD: "async_turn_off"},
        ],
    )


@test
async def unload_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device=Depends(mock_device),
) -> None:
    """Test when a config entry is unloaded from HA."""
    await create_entity_from_device(hass, mock_device)
    expect(hass.states.get("light.name") is not None).to_be(True)
    entry_id = await get_entry_id_from_hass(hass)
    expect(bool(await hass.config_entries.async_unload(entry_id))).to_be(True)
    await hass.async_block_till_done()
    expect(hass.states.get("light.name").state).to_equal(STATE_UNAVAILABLE)


@test
async def remove_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device=Depends(mock_device),
) -> None:
    """Test when a config entry is removed from HA."""
    await create_entity_from_device(hass, mock_device)
    expect(hass.states.get("light.name") is not None).to_be(True)
    entry_id = await get_entry_id_from_hass(hass)
    expect(bool(await hass.config_entries.async_remove(entry_id))).to_be(True)
    await hass.async_block_till_done()
    expect(hass.states.get("light.name")).to_be(None)


@test
async def light_restore_state(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device=Depends(mock_device),
) -> None:
    """Test restore from cache."""
    mock_restore_cache(
        hass,
        [State("light.name", STATE_ON, attributes={ATTR_BRIGHTNESS: 77})],
    )
    await create_entity_from_device(hass, mock_device)
    mock_device.init_level.assert_called_once_with(77)
    entity_state = hass.states.get("light.name")
    expect(entity_state.state).to_equal(STATE_ON)
    expect(entity_state.attributes[ATTR_BRIGHTNESS]).to_equal(77)
    expect(entity_state.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.BRIGHTNESS)


@test
async def light_restore_state_bad_cache(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_device=Depends(mock_device),
) -> None:
    """Test restore from a cache without the attribute."""
    mock_restore_cache(
        hass,
        [State("light.name", "abc", attributes={"blabla": 77})],
    )
    await create_entity_from_device(hass, mock_device)
    mock_device.init_level.assert_not_called()
    entity_state = hass.states.get("light.name")
    expect(entity_state.state).to_equal(STATE_OFF)
