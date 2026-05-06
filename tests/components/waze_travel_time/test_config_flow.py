"""Test the Waze Travel Time config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.waze_travel_time.config_flow import WazeConfigFlow
from homeassistant.components.waze_travel_time.const import (
    CONF_AVOID_FERRIES,
    CONF_AVOID_SUBSCRIPTION_ROADS,
    CONF_AVOID_TOLL_ROADS,
    CONF_BASE_COORDINATES,
    CONF_DESTINATION,
    CONF_EXCL_FILTER,
    CONF_INCL_FILTER,
    CONF_ORIGIN,
    CONF_REALTIME,
    CONF_TIME_DELTA,
    CONF_UNITS,
    CONF_VEHICLE_TYPE,
    DEFAULT_NAME,
    DEFAULT_OPTIONS,
    DOMAIN,
    IMPERIAL_UNITS,
)
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, CONF_REGION
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import get_default_options
from ._fixtures import invalidate_config_entry, mock_update, validate_config_entry
from .const import CONFIG_FLOW_USER_INPUT, MOCK_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures."""


@test
async def minimum_fields(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _validate: object = Depends(validate_config_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG_FLOW_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(DEFAULT_NAME)
    expect(result2["data"]).to_equal(
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ORIGIN: "location1",
            CONF_DESTINATION: "location2",
            CONF_REGION: "US",
        }
    )


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _update: object = Depends(mock_update),
) -> None:
    """Test reconfigure flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        options=DEFAULT_OPTIONS,
        version=WazeConfigFlow.VERSION,
        minor_version=WazeConfigFlow.MINOR_VERSION,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    reconfigure_result = await entry.start_reconfigure_flow(hass)
    expect(reconfigure_result["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_result["step_id"]).to_equal("user")

    user_step_result = await hass.config_entries.flow.async_configure(
        reconfigure_result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ORIGIN: "location3",
            CONF_DESTINATION: "location4",
            CONF_REGION: "us",
        },
    )
    expect(user_step_result["type"]).to_be(FlowResultType.ABORT)
    expect(user_step_result["reason"]).to_equal("reconfigure_successful")
    await hass.async_block_till_done()

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.data).to_equal(
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ORIGIN: "location3",
            CONF_DESTINATION: "location4",
            CONF_REGION: "US",
        }
    )


@test
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _update: object = Depends(mock_update),
) -> None:
    """Test options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        options=get_default_options(hass),
        version=WazeConfigFlow.VERSION,
        minor_version=WazeConfigFlow.MINOR_VERSION,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id, data=None)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_AVOID_FERRIES: True,
            CONF_AVOID_SUBSCRIPTION_ROADS: True,
            CONF_AVOID_TOLL_ROADS: True,
            CONF_BASE_COORDINATES: {
                CONF_LATITUDE: 1.123,
                CONF_LONGITUDE: -1.123,
            },
            CONF_EXCL_FILTER: ["ExcludeThis"],
            CONF_INCL_FILTER: ["IncludeThis"],
            CONF_REALTIME: False,
            CONF_TIME_DELTA: {"hours": 1, "minutes": 30},
            CONF_UNITS: IMPERIAL_UNITS,
            CONF_VEHICLE_TYPE: "taxi",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("")
    expected = {
        CONF_AVOID_FERRIES: True,
        CONF_AVOID_SUBSCRIPTION_ROADS: True,
        CONF_AVOID_TOLL_ROADS: True,
        CONF_BASE_COORDINATES: {
            CONF_LATITUDE: 1.123,
            CONF_LONGITUDE: -1.123,
        },
        CONF_EXCL_FILTER: ["ExcludeThis"],
        CONF_INCL_FILTER: ["IncludeThis"],
        CONF_REALTIME: False,
        CONF_TIME_DELTA: {"hours": 1, "minutes": 30},
        CONF_UNITS: IMPERIAL_UNITS,
        CONF_VEHICLE_TYPE: "taxi",
    }
    expect(result["data"]).to_equal(expected)
    expect(entry.options).to_equal(expected)


@test
async def dupe(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _validate: object = Depends(validate_config_entry),
) -> None:
    """Test setting up the same entry data twice is OK."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG_FLOW_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        CONFIG_FLOW_USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.skip("uses caplog text inspection")
async def invalid_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _invalidate: object = Depends(invalidate_config_entry),
) -> None:
    """Test we get the form."""


@test
async def reset_filters(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _update: object = Depends(mock_update),
) -> None:
    """Test resetting inclusive and exclusive filters to empty string."""
    options = {**DEFAULT_OPTIONS}
    options[CONF_INCL_FILTER] = ["test"]
    options[CONF_EXCL_FILTER] = ["test"]
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        options=options,
        entry_id="test",
        version=WazeConfigFlow.VERSION,
        minor_version=WazeConfigFlow.MINOR_VERSION,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, data=None
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_AVOID_FERRIES: True,
            CONF_AVOID_SUBSCRIPTION_ROADS: True,
            CONF_AVOID_TOLL_ROADS: True,
            CONF_REALTIME: False,
            CONF_UNITS: IMPERIAL_UNITS,
            CONF_VEHICLE_TYPE: "taxi",
        },
    )

    expect(config_entry.options).to_equal(
        {
            CONF_AVOID_FERRIES: True,
            CONF_AVOID_SUBSCRIPTION_ROADS: True,
            CONF_AVOID_TOLL_ROADS: True,
            CONF_EXCL_FILTER: [""],
            CONF_INCL_FILTER: [""],
            CONF_REALTIME: False,
            CONF_TIME_DELTA: {"minutes": 0},
            CONF_UNITS: IMPERIAL_UNITS,
            CONF_VEHICLE_TYPE: "taxi",
        }
    )


@test
async def reset_base_coordinates(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _update: object = Depends(mock_update),
) -> None:
    """Test clearing base coordinates in the options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        options=get_default_options(hass),
        version=WazeConfigFlow.VERSION,
        minor_version=WazeConfigFlow.MINOR_VERSION,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id, data=None)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_AVOID_FERRIES: False,
            CONF_AVOID_SUBSCRIPTION_ROADS: False,
            CONF_AVOID_TOLL_ROADS: False,
            CONF_REALTIME: True,
            CONF_UNITS: IMPERIAL_UNITS,
            CONF_VEHICLE_TYPE: "taxi",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(CONF_BASE_COORDINATES not in entry.options).to_be(True)
