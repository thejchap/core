"""Test ESPHome water heaters."""

from unittest.mock import call

from aioesphomeapi import (
    APIClient,
    WaterHeaterFeature,
    WaterHeaterInfo,
    WaterHeaterMode,
    WaterHeaterState,
    WaterHeaterStateFlag,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.water_heater import (
    ATTR_AWAY_MODE,
    ATTR_OPERATION_LIST,
    DOMAIN as WATER_HEATER_DOMAIN,
    SERVICE_SET_AWAY_MODE,
    SERVICE_SET_OPERATION_MODE,
    SERVICE_SET_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    WaterHeaterEntityFeature,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    ATTR_TEMPERATURE,
)
from homeassistant.core import HomeAssistant

from ._fixtures import MockESPHomeDeviceType, mock_client, mock_esphome_device

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


@test
async def water_heater_entity(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic water heater entity."""
    entity_info = [
        WaterHeaterInfo(
            object_id="my_boiler",
            key=1,
            name="My Boiler",
            min_temperature=10.0,
            max_temperature=85.0,
            supported_modes=[
                WaterHeaterMode.ECO,
                WaterHeaterMode.GAS,
            ],
        )
    ]
    states = [
        WaterHeaterState(
            key=1,
            mode=WaterHeaterMode.ECO,
            current_temperature=45.0,
            target_temperature=50.0,
        )
    ]

    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    state = hass.states.get("water_heater.test_my_boiler")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("eco")
    expect(state.attributes["current_temperature"]).to_equal(45.0)
    expect(state.attributes["temperature"]).to_equal(50.0)
    expect(state.attributes["min_temp"]).to_equal(10.0)
    expect(state.attributes["max_temp"]).to_equal(85.0)
    expect(state.attributes["operation_list"]).to_equal(["eco", "gas"])


@test
async def water_heater_entity_no_modes(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a water heater entity without operation modes."""
    entity_info = [
        WaterHeaterInfo(
            object_id="my_boiler",
            key=1,
            name="My Boiler",
            min_temperature=10.0,
            max_temperature=85.0,
        )
    ]
    states = [
        WaterHeaterState(
            key=1,
            current_temperature=45.0,
            target_temperature=50.0,
        )
    ]

    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    state = hass.states.get("water_heater.test_my_boiler")
    expect(state is not None).to_be(True)
    expect(state.attributes["min_temp"]).to_equal(10.0)
    expect(state.attributes["max_temp"]).to_equal(85.0)
    expect(state.attributes.get(ATTR_OPERATION_LIST) is None).to_be(True)


@test
async def water_heater_set_temperature(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test setting the target temperature."""
    entity_info = [
        WaterHeaterInfo(
            object_id="my_boiler",
            key=1,
            name="My Boiler",
            min_temperature=10.0,
            max_temperature=85.0,
        )
    ]
    states = [
        WaterHeaterState(
            key=1,
            mode=WaterHeaterMode.ECO,
            target_temperature=45.0,
        )
    ]

    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    await hass.services.async_call(
        WATER_HEATER_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: "water_heater.test_my_boiler",
            ATTR_TEMPERATURE: 55,
        },
        blocking=True,
    )

    mock_client.water_heater_command.assert_has_calls(
        [call(key=1, target_temperature=55.0, device_id=0)]
    )


@test
async def water_heater_set_operation_mode(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test setting the operation mode."""
    entity_info = [
        WaterHeaterInfo(
            object_id="my_boiler",
            key=1,
            name="My Boiler",
            supported_modes=[
                WaterHeaterMode.ECO,
                WaterHeaterMode.GAS,
            ],
        )
    ]
    states = [
        WaterHeaterState(
            key=1,
            mode=WaterHeaterMode.ECO,
        )
    ]

    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    await hass.services.async_call(
        WATER_HEATER_DOMAIN,
        SERVICE_SET_OPERATION_MODE,
        {
            ATTR_ENTITY_ID: "water_heater.test_my_boiler",
            "operation_mode": "gas",
        },
        blocking=True,
    )

    mock_client.water_heater_command.assert_has_calls(
        [call(key=1, mode=WaterHeaterMode.GAS, device_id=0)]
    )


@test
async def water_heater_on_off(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test turning the water heater on and off."""
    entity_info = [
        WaterHeaterInfo(
            object_id="my_boiler",
            key=1,
            name="My Boiler",
            min_temperature=10.0,
            max_temperature=85.0,
            supported_features=WaterHeaterFeature.SUPPORTS_ON_OFF,
        )
    ]
    states = [
        WaterHeaterState(
            key=1,
            target_temperature=50.0,
        )
    ]

    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    state = hass.states.get("water_heater.test_my_boiler")
    expect(state is not None).to_be(True)
    expect(
        bool(state.attributes["supported_features"] & WaterHeaterEntityFeature.ON_OFF)
    ).to_be(True)

    await hass.services.async_call(
        WATER_HEATER_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "water_heater.test_my_boiler"},
        blocking=True,
    )

    mock_client.water_heater_command.assert_has_calls(
        [call(key=1, on=True, device_id=0)]
    )

    mock_client.water_heater_command.reset_mock()

    await hass.services.async_call(
        WATER_HEATER_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "water_heater.test_my_boiler"},
        blocking=True,
    )

    mock_client.water_heater_command.assert_has_calls(
        [call(key=1, on=False, device_id=0)]
    )


@test
async def water_heater_target_temperature_step(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test target temperature step is respected."""
    entity_info = [
        WaterHeaterInfo(
            object_id="my_boiler",
            key=1,
            name="My Boiler",
            min_temperature=10.0,
            max_temperature=85.0,
            target_temperature_step=5.0,
        )
    ]
    states = [
        WaterHeaterState(
            key=1,
            target_temperature=50.0,
        )
    ]

    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    state = hass.states.get("water_heater.test_my_boiler")
    expect(state is not None).to_be(True)
    expect(state.attributes["target_temp_step"]).to_equal(5.0)


@test
async def water_heater_no_on_off_without_feature(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test ON_OFF feature is not set when not supported."""
    entity_info = [
        WaterHeaterInfo(
            object_id="my_boiler",
            key=1,
            name="My Boiler",
            min_temperature=10.0,
            max_temperature=85.0,
        )
    ]
    states = [
        WaterHeaterState(
            key=1,
            target_temperature=50.0,
        )
    ]

    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    state = hass.states.get("water_heater.test_my_boiler")
    expect(state is not None).to_be(True)
    expect(
        bool(state.attributes["supported_features"] & WaterHeaterEntityFeature.ON_OFF)
    ).to_be(False)


@test.cases(
    test.case(
        "supports_away",
        supported_features=WaterHeaterFeature.SUPPORTS_AWAY_MODE,
        has_away_mode=True,
    ),
    test.case(
        "no_features",
        supported_features=WaterHeaterFeature(0),
        has_away_mode=False,
    ),
)
async def water_heater_away_mode_feature_flag(
    supported_features: WaterHeaterFeature,
    has_away_mode: bool,
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test AWAY_MODE feature flag tracks the ESPHome SUPPORTS_AWAY_MODE flag."""
    entity_info = [
        WaterHeaterInfo(
            object_id="my_boiler",
            key=1,
            name="My Boiler",
            min_temperature=10.0,
            max_temperature=85.0,
            supported_features=supported_features,
        )
    ]
    states = [WaterHeaterState(key=1, target_temperature=50.0)]

    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    state = hass.states.get("water_heater.test_my_boiler")
    expect(state is not None).to_be(True)
    expect(
        bool(
            state.attributes[ATTR_SUPPORTED_FEATURES]
            & WaterHeaterEntityFeature.AWAY_MODE
        )
    ).to_be(has_away_mode)


@test.cases(
    test.case(
        "away_off",
        state_flag=WaterHeaterStateFlag(0),
        expected_away_mode="off",
    ),
    test.case(
        "away_on",
        state_flag=WaterHeaterStateFlag.AWAY,
        expected_away_mode="on",
    ),
)
async def water_heater_away_mode_state(
    state_flag: WaterHeaterStateFlag,
    expected_away_mode: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test is_away_mode_on reflects the AWAY state flag."""
    entity_info = [
        WaterHeaterInfo(
            object_id="my_boiler",
            key=1,
            name="My Boiler",
            min_temperature=10.0,
            max_temperature=85.0,
            supported_features=WaterHeaterFeature.SUPPORTS_AWAY_MODE,
        )
    ]
    states = [
        WaterHeaterState(
            key=1,
            target_temperature=50.0,
            state=state_flag,
        )
    ]

    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    state = hass.states.get("water_heater.test_my_boiler")
    expect(state is not None).to_be(True)
    expect(state.attributes[ATTR_AWAY_MODE]).to_equal(expected_away_mode)


@test.cases(
    test.case("away_true", away_mode=True),
    test.case("away_false", away_mode=False),
)
async def water_heater_set_away_mode(
    away_mode: bool,
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test the set_away_mode service forwards the value to ESPHome."""
    entity_info = [
        WaterHeaterInfo(
            object_id="my_boiler",
            key=1,
            name="My Boiler",
            min_temperature=10.0,
            max_temperature=85.0,
            supported_features=WaterHeaterFeature.SUPPORTS_AWAY_MODE,
        )
    ]
    states = [
        WaterHeaterState(
            key=1,
            target_temperature=50.0,
            state=WaterHeaterStateFlag(0),
        )
    ]

    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )

    await hass.services.async_call(
        WATER_HEATER_DOMAIN,
        SERVICE_SET_AWAY_MODE,
        {
            ATTR_ENTITY_ID: "water_heater.test_my_boiler",
            ATTR_AWAY_MODE: away_mode,
        },
        blocking=True,
    )

    mock_client.water_heater_command.assert_has_calls(
        [call(key=1, away=away_mode, device_id=0)]
    )
