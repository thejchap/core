"""The water heater tests for the Airzone Cloud platform."""

from unittest.mock import patch

from aioairzone_cloud.exceptions import AirzoneCloudError
from tryke import Depends, expect, fixture, test

from homeassistant.components.water_heater import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
    ATTR_OPERATION_MODE,
    DOMAIN as WATER_HEATER_DOMAIN,
    SERVICE_SET_OPERATION_MODE,
    SERVICE_SET_TEMPERATURE,
    STATE_ECO,
    STATE_PERFORMANCE,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ._fixtures import airzone_cloud_no_websockets
from .util import async_init_integration

from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _no_ws: None = Depends(airzone_cloud_no_websockets),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def airzone_create_water_heater(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test creation of water heater."""

    await async_init_integration(hass)

    state = hass.states.get("water_heater.airzone_cloud_dhw")
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_CURRENT_TEMPERATURE]).to_equal(45.5)
    expect(state.attributes[ATTR_MAX_TEMP]).to_equal(60)
    expect(state.attributes[ATTR_MIN_TEMP]).to_equal(40)
    expect(state.attributes[ATTR_TEMPERATURE]).to_equal(48)


@test
async def airzone_water_heater_turn_on_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turning on/off."""

    await async_init_integration(hass)

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: "water_heater.airzone_cloud_dhw",
            },
            blocking=True,
        )

    state = hass.states.get("water_heater.airzone_cloud_dhw")
    expect(state.state).to_equal(STATE_ECO)

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_TURN_OFF,
            {
                ATTR_ENTITY_ID: "water_heater.airzone_cloud_dhw",
            },
            blocking=True,
        )

    state = hass.states.get("water_heater.airzone_cloud_dhw")
    expect(state.state).to_equal(STATE_OFF)


@test
async def airzone_water_heater_set_operation(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the Operation mode."""

    await async_init_integration(hass)

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {
                ATTR_ENTITY_ID: "water_heater.airzone_cloud_dhw",
                ATTR_OPERATION_MODE: STATE_ECO,
            },
            blocking=True,
        )

    state = hass.states.get("water_heater.airzone_cloud_dhw")
    expect(state.state).to_equal(STATE_ECO)

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {
                ATTR_ENTITY_ID: "water_heater.airzone_cloud_dhw",
                ATTR_OPERATION_MODE: STATE_PERFORMANCE,
            },
            blocking=True,
        )

    state = hass.states.get("water_heater.airzone_cloud_dhw")
    expect(state.state).to_equal(STATE_PERFORMANCE)

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_OPERATION_MODE,
            {
                ATTR_ENTITY_ID: "water_heater.airzone_cloud_dhw",
                ATTR_OPERATION_MODE: STATE_OFF,
            },
            blocking=True,
        )

    state = hass.states.get("water_heater.airzone_cloud_dhw")
    expect(state.state).to_equal(STATE_OFF)


@test
async def airzone_water_heater_set_temp(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the target temperature."""

    await async_init_integration(hass)

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        return_value=None,
    ):
        await hass.services.async_call(
            WATER_HEATER_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "water_heater.airzone_cloud_dhw",
                ATTR_TEMPERATURE: 50,
            },
            blocking=True,
        )

    state = hass.states.get("water_heater.airzone_cloud_dhw")
    expect(state.attributes[ATTR_TEMPERATURE]).to_equal(50)


@test
async def airzone_water_heater_set_temp_error(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test error when setting the target temperature."""

    await async_init_integration(hass)

    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.api_patch_device",
        side_effect=AirzoneCloudError,
    ):
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                WATER_HEATER_DOMAIN,
                SERVICE_SET_TEMPERATURE,
                {
                    ATTR_ENTITY_ID: "water_heater.airzone_cloud_dhw",
                    ATTR_TEMPERATURE: 80,
                },
                blocking=True,
            )

    state = hass.states.get("water_heater.airzone_cloud_dhw")
    expect(state.attributes[ATTR_TEMPERATURE]).to_equal(48)
