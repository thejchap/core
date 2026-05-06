"""Test the PurpleAir config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

from aiopurpleair.errors import InvalidApiKeyError, PurpleAirError
from tryke import Depends, expect, fixture, test

from homeassistant.components.purpleair.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr

from ._fixtures import (
    TEST_API_KEY,
    TEST_SENSOR_INDEX1,
    TEST_SENSOR_INDEX2,
    api as api_fx,
    config_entry as config_entry_fx,
    mock_aiopurpleair as mock_aiopurpleair_fx,
    mock_async_zeroconf as mock_async_zeroconf_fx,
    setup_config_entry as setup_config_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_LATITUDE = 51.5285582
TEST_LONGITUDE = -0.2416796


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: object = Depends(mock_async_zeroconf_fx),
) -> None:
    """Wire mock_network + zeroconf for every test."""


@test.cases(
    test.case(
        "unknown_exception",
        check_api_key_side_effect=Exception,
        check_api_key_errors={"base": "unknown"},
        get_nearby_sensors_kwargs={"return_value": []},
        get_nearby_sensors_errors={"base": "no_sensors_near_coordinates"},
    ),
    test.case(
        "invalid_api_key",
        check_api_key_side_effect=InvalidApiKeyError,
        check_api_key_errors={"base": "invalid_api_key"},
        get_nearby_sensors_kwargs={"side_effect": Exception},
        get_nearby_sensors_errors={"base": "unknown"},
    ),
    test.case(
        "purple_air_error",
        check_api_key_side_effect=PurpleAirError,
        check_api_key_errors={"base": "unknown"},
        get_nearby_sensors_kwargs={"side_effect": PurpleAirError},
        get_nearby_sensors_errors={"base": "unknown"},
    ),
)
async def create_entry_by_coordinates(
    check_api_key_side_effect: type[Exception],
    check_api_key_errors: dict[str, str],
    get_nearby_sensors_kwargs: dict[str, object],
    get_nearby_sensors_errors: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    api: Mock = Depends(api_fx),
    _mock_aiopurpleair: Mock = Depends(mock_aiopurpleair_fx),
) -> None:
    """Test creating an entry by entering a latitude/longitude (including errors)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch.object(
        api, "async_check_api_key", AsyncMock(side_effect=check_api_key_side_effect)
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"api_key": TEST_API_KEY}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal(check_api_key_errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"api_key": TEST_API_KEY}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("by_coordinates")

    with patch.object(
        api.sensors,
        "async_get_nearby_sensors",
        AsyncMock(**get_nearby_sensors_kwargs),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                "latitude": TEST_LATITUDE,
                "longitude": TEST_LONGITUDE,
                "distance": 5,
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal(get_nearby_sensors_errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "latitude": TEST_LATITUDE,
            "longitude": TEST_LONGITUDE,
            "distance": 5,
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("choose_sensor")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"sensor_index": str(TEST_SENSOR_INDEX1)},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("abcde")
    expect(result["data"]).to_equal({"api_key": TEST_API_KEY})
    expect(result["options"]).to_equal({"sensor_indices": [TEST_SENSOR_INDEX1]})


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _config_entry: MockConfigEntry = Depends(config_entry_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test that the proper error is shown when adding a duplicate config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={"api_key": TEST_API_KEY}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "unknown_exception",
        check_api_key_side_effect=Exception,
        check_api_key_errors={"base": "unknown"},
    ),
    test.case(
        "invalid_api_key",
        check_api_key_side_effect=InvalidApiKeyError,
        check_api_key_errors={"base": "invalid_api_key"},
    ),
    test.case(
        "purple_air_error",
        check_api_key_side_effect=PurpleAirError,
        check_api_key_errors={"base": "unknown"},
    ),
)
async def reauth(
    check_api_key_side_effect: type[Exception],
    check_api_key_errors: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_aiopurpleair: Mock = Depends(mock_aiopurpleair_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test re-auth (including errors)."""
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch.object(
        mock_aiopurpleair,
        "async_check_api_key",
        AsyncMock(side_effect=check_api_key_side_effect),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"api_key": "new_api_key"}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal(check_api_key_errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"api_key": "new_api_key"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(hass.config_entries.async_entries())).to_equal(1)
    await hass.config_entries.async_unload(config_entry.entry_id)


@test.cases(
    test.case(
        "no_sensors",
        get_nearby_sensors_kwargs={"return_value": []},
        get_nearby_sensors_errors={"base": "no_sensors_near_coordinates"},
    ),
    test.case(
        "unknown_exception",
        get_nearby_sensors_kwargs={"side_effect": Exception},
        get_nearby_sensors_errors={"base": "unknown"},
    ),
    test.case(
        "purple_air_error",
        get_nearby_sensors_kwargs={"side_effect": PurpleAirError},
        get_nearby_sensors_errors={"base": "unknown"},
    ),
)
async def options_add_sensor(
    get_nearby_sensors_kwargs: dict[str, object],
    get_nearby_sensors_errors: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_aiopurpleair: Mock = Depends(mock_aiopurpleair_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test adding a sensor via the options flow (including errors)."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "add_sensor"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("add_sensor")

    with patch.object(
        mock_aiopurpleair.sensors,
        "async_get_nearby_sensors",
        AsyncMock(**get_nearby_sensors_kwargs),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "latitude": TEST_LATITUDE,
                "longitude": TEST_LONGITUDE,
                "distance": 5,
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("add_sensor")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "latitude": TEST_LATITUDE,
            "longitude": TEST_LONGITUDE,
            "distance": 5,
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("choose_sensor")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"sensor_index": str(TEST_SENSOR_INDEX2)},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {"sensor_indices": [TEST_SENSOR_INDEX1, TEST_SENSOR_INDEX2]}
    )
    expect(config_entry.options["sensor_indices"]).to_equal(
        [TEST_SENSOR_INDEX1, TEST_SENSOR_INDEX2]
    )
    await hass.config_entries.async_unload(config_entry.entry_id)


@test
async def options_add_sensor_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test adding a duplicate sensor via the options flow."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "add_sensor"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("add_sensor")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "latitude": TEST_LATITUDE,
            "longitude": TEST_LONGITUDE,
            "distance": 5,
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("choose_sensor")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"sensor_index": str(TEST_SENSOR_INDEX1)},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    await hass.config_entries.async_unload(config_entry.entry_id)


@test
async def options_remove_sensor(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test removing a sensor via the options flow."""
    device_registry = dr.async_get(hass)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "remove_sensor"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("remove_sensor")

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, str(TEST_SENSOR_INDEX1))}
    )
    expect(device_entry is not None).to_be(True)
    assert device_entry is not None
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"sensor_device_id": device_entry.id},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({"sensor_indices": []})
    expect(config_entry.options["sensor_indices"]).to_equal([])
    await hass.config_entries.async_unload(config_entry.entry_id)


@test
async def options_settings(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test setting settings via the options flow."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "settings"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("settings")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"show_on_map": True}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {"sensor_indices": [TEST_SENSOR_INDEX1], "show_on_map": True}
    )
    expect(config_entry.options["show_on_map"]).to_be(True)
