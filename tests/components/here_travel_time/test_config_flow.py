"""Test the HERE Travel Time config flow."""

from unittest.mock import MagicMock, patch

from here_routing import HERERoutingError, HERERoutingUnauthorizedError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.here_travel_time.config_flow import (
    DEFAULT_OPTIONS,
    HERETravelTimeConfigFlow,
)
from homeassistant.components.here_travel_time.const import (
    CONF_ARRIVAL_TIME,
    CONF_DEPARTURE_TIME,
    CONF_DESTINATION_ENTITY_ID,
    CONF_DESTINATION_LATITUDE,
    CONF_DESTINATION_LONGITUDE,
    CONF_ORIGIN_ENTITY_ID,
    CONF_ORIGIN_LATITUDE,
    CONF_ORIGIN_LONGITUDE,
    CONF_ROUTE_MODE,
    CONF_TRAFFIC_MODE,
    DOMAIN,
    ROUTE_MODE_FASTEST,
    TRAVEL_MODE_BICYCLE,
    TRAVEL_MODE_CAR,
    TRAVEL_MODE_PUBLIC,
)
from homeassistant.const import CONF_API_KEY, CONF_MODE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    bypass_setup,
    option_init_result,
    origin_step_result,
    user_step_result,
    valid_response,
)
from .const import (
    API_KEY,
    DEFAULT_CONFIG,
    DESTINATION_LATITUDE,
    DESTINATION_LONGITUDE,
    ORIGIN_LATITUDE,
    ORIGIN_LONGITUDE,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _bypass: None = Depends(bypass_setup),
) -> None:
    """Anchor fixture so tryke materializes hass + dependents per-test.

    Tryke requires every @test signature to have at least one fixture
    Depends() besides hass for hass injection to occur reliably; this
    fixture serves that role and bundles bypass_setup which most tests
    need anyway.
    """


@test.cases(
    test.case(
        "default_menu",
        menu_options=["origin_coordinates", "origin_entity"],
    ),
)
async def step_user(
    menu_options: list[str],
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _valid: MagicMock = Depends(valid_response),
) -> None:
    """Test the user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: API_KEY,
            CONF_MODE: TRAVEL_MODE_CAR,
            CONF_NAME: "test",
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.MENU)
    expect(result2["menu_options"]).to_equal(menu_options)


@test
async def step_origin_coordinates(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _valid: MagicMock = Depends(valid_response),
    user_step_result: config_entries.ConfigFlowResult = Depends(user_step_result),
) -> None:
    """Test the origin coordinates step."""
    menu_result = await hass.config_entries.flow.async_configure(
        user_step_result["flow_id"], {"next_step_id": "origin_coordinates"}
    )
    expect(menu_result["type"]).to_be(FlowResultType.FORM)

    location_selector_result = await hass.config_entries.flow.async_configure(
        menu_result["flow_id"],
        {
            "origin": {
                "latitude": float(ORIGIN_LATITUDE),
                "longitude": float(ORIGIN_LONGITUDE),
                "radius": 3.0,
            }
        },
    )
    expect(location_selector_result["type"]).to_be(FlowResultType.MENU)


@test
async def step_origin_entity(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _valid: MagicMock = Depends(valid_response),
    user_step_result: config_entries.ConfigFlowResult = Depends(user_step_result),
) -> None:
    """Test the origin coordinates step."""
    menu_result = await hass.config_entries.flow.async_configure(
        user_step_result["flow_id"], {"next_step_id": "origin_entity"}
    )
    expect(menu_result["type"]).to_be(FlowResultType.FORM)

    entity_selector_result = await hass.config_entries.flow.async_configure(
        menu_result["flow_id"],
        {"origin_entity_id": "zone.home"},
    )
    expect(entity_selector_result["type"]).to_be(FlowResultType.MENU)


@test
async def step_destination_coordinates(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _valid: MagicMock = Depends(valid_response),
    origin_step_result: config_entries.ConfigFlowResult = Depends(origin_step_result),
) -> None:
    """Test the origin coordinates step."""
    menu_result = await hass.config_entries.flow.async_configure(
        origin_step_result["flow_id"], {"next_step_id": "destination_coordinates"}
    )
    expect(menu_result["type"]).to_be(FlowResultType.FORM)

    location_selector_result = await hass.config_entries.flow.async_configure(
        menu_result["flow_id"],
        {
            "destination": {
                "latitude": float(DESTINATION_LATITUDE),
                "longitude": float(DESTINATION_LONGITUDE),
                "radius": 3.0,
            }
        },
    )
    expect(location_selector_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.data).to_equal(
        {
            CONF_NAME: "test",
            CONF_API_KEY: API_KEY,
            CONF_ORIGIN_LATITUDE: float(ORIGIN_LATITUDE),
            CONF_ORIGIN_LONGITUDE: float(ORIGIN_LONGITUDE),
            CONF_DESTINATION_LATITUDE: float(DESTINATION_LATITUDE),
            CONF_DESTINATION_LONGITUDE: float(DESTINATION_LONGITUDE),
            CONF_MODE: TRAVEL_MODE_CAR,
        }
    )


@test
async def step_destination_entity(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _valid: MagicMock = Depends(valid_response),
    origin_step_result: config_entries.ConfigFlowResult = Depends(origin_step_result),
) -> None:
    """Test the origin coordinates step."""
    menu_result = await hass.config_entries.flow.async_configure(
        origin_step_result["flow_id"], {"next_step_id": "destination_entity"}
    )
    expect(menu_result["type"]).to_be(FlowResultType.FORM)

    entity_selector_result = await hass.config_entries.flow.async_configure(
        menu_result["flow_id"],
        {"destination_entity_id": "zone.home"},
    )
    expect(entity_selector_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.data).to_equal(
        {
            CONF_NAME: "test",
            CONF_API_KEY: API_KEY,
            CONF_ORIGIN_LATITUDE: float(ORIGIN_LATITUDE),
            CONF_ORIGIN_LONGITUDE: float(ORIGIN_LONGITUDE),
            CONF_DESTINATION_ENTITY_ID: "zone.home",
            CONF_MODE: TRAVEL_MODE_CAR,
        }
    )
    expect(entry.options).to_equal(
        {
            CONF_ROUTE_MODE: ROUTE_MODE_FASTEST,
            CONF_ARRIVAL_TIME: None,
            CONF_DEPARTURE_TIME: None,
            CONF_TRAFFIC_MODE: True,
        }
    )


async def do_common_reconfiguration_steps(
    hass: HomeAssistant,
) -> config_entries.ConfigFlowResult:
    """Walk through common flow steps for reconfiguring."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="0123456789",
        data=DEFAULT_CONFIG,
        options=DEFAULT_OPTIONS,
        version=HERETravelTimeConfigFlow.VERSION,
        minor_version=HERETravelTimeConfigFlow.MINOR_VERSION,
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
            CONF_API_KEY: API_KEY,
            CONF_MODE: TRAVEL_MODE_BICYCLE,
            CONF_NAME: "test",
        },
    )
    await hass.async_block_till_done()
    menu_result = await hass.config_entries.flow.async_configure(
        user_step_result["flow_id"], {"next_step_id": "origin_entity"}
    )
    return await hass.config_entries.flow.async_configure(
        menu_result["flow_id"],
        {"origin_entity_id": "zone.home"},
    )


@test
async def reconfigure_destination_entity(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _valid: MagicMock = Depends(valid_response),
) -> None:
    """Test reconfigure flow when choosing a destination entity."""
    origin_entity_selector_result = await do_common_reconfiguration_steps(hass)
    menu_result = await hass.config_entries.flow.async_configure(
        origin_entity_selector_result["flow_id"], {"next_step_id": "destination_entity"}
    )
    expect(menu_result["type"]).to_be(FlowResultType.FORM)

    destination_entity_selector_result = await hass.config_entries.flow.async_configure(
        menu_result["flow_id"],
        {"destination_entity_id": "zone.home"},
    )
    expect(destination_entity_selector_result["type"]).to_be(FlowResultType.ABORT)
    expect(destination_entity_selector_result["reason"]).to_equal(
        "reconfigure_successful"
    )
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.data).to_equal(
        {
            CONF_NAME: "test",
            CONF_API_KEY: API_KEY,
            CONF_ORIGIN_ENTITY_ID: "zone.home",
            CONF_DESTINATION_ENTITY_ID: "zone.home",
            CONF_MODE: TRAVEL_MODE_BICYCLE,
        }
    )


@test
async def reconfigure_destination_coordinates(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _valid: MagicMock = Depends(valid_response),
) -> None:
    """Test reconfigure flow when choosing destination coordinates."""
    origin_entity_selector_result = await do_common_reconfiguration_steps(hass)
    menu_result = await hass.config_entries.flow.async_configure(
        origin_entity_selector_result["flow_id"],
        {"next_step_id": "destination_coordinates"},
    )
    expect(menu_result["type"]).to_be(FlowResultType.FORM)

    destination_entity_selector_result = await hass.config_entries.flow.async_configure(
        menu_result["flow_id"],
        {
            "destination": {
                "latitude": 43.0,
                "longitude": -80.3,
                "radius": 5.0,
            }
        },
    )
    expect(destination_entity_selector_result["type"]).to_be(FlowResultType.ABORT)
    expect(destination_entity_selector_result["reason"]).to_equal(
        "reconfigure_successful"
    )
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.data).to_equal(
        {
            CONF_NAME: "test",
            CONF_API_KEY: API_KEY,
            CONF_ORIGIN_ENTITY_ID: "zone.home",
            CONF_DESTINATION_LATITUDE: 43.0,
            CONF_DESTINATION_LONGITUDE: -80.3,
            CONF_MODE: TRAVEL_MODE_BICYCLE,
        }
    )


@test
async def form_invalid_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "here_routing.HERERoutingApi.route",
        side_effect=HERERoutingUnauthorizedError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: API_KEY,
                CONF_MODE: TRAVEL_MODE_CAR,
                CONF_NAME: "test",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_unknown_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "here_routing.HERERoutingApi.route",
        side_effect=HERERoutingError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: API_KEY,
                CONF_MODE: TRAVEL_MODE_CAR,
                CONF_NAME: "test",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _valid: MagicMock = Depends(valid_response),
) -> None:
    """Test the options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="0123456789",
        data=DEFAULT_CONFIG,
        version=HERETravelTimeConfigFlow.VERSION,
        minor_version=HERETravelTimeConfigFlow.MINOR_VERSION,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)

    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ROUTE_MODE: ROUTE_MODE_FASTEST,
            CONF_TRAFFIC_MODE: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.options).to_equal(
        {
            CONF_ROUTE_MODE: ROUTE_MODE_FASTEST,
            CONF_TRAFFIC_MODE: False,
        }
    )


@test
async def options_flow_arrival_time_step(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _valid: MagicMock = Depends(valid_response),
    option_init_result: config_entries.ConfigFlowResult = Depends(option_init_result),
) -> None:
    """Test the options flow arrival time type."""
    menu_result = await hass.config_entries.options.async_configure(
        option_init_result["flow_id"], {"next_step_id": "arrival_time"}
    )
    expect(menu_result["type"]).to_be(FlowResultType.FORM)
    time_selector_result = await hass.config_entries.options.async_configure(
        option_init_result["flow_id"],
        user_input={
            "arrival_time": "08:00:00",
        },
    )

    expect(time_selector_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.options).to_equal(
        {
            CONF_ROUTE_MODE: ROUTE_MODE_FASTEST,
            CONF_ARRIVAL_TIME: "08:00:00",
            CONF_TRAFFIC_MODE: True,
        }
    )


@test
async def options_flow_departure_time_step(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _valid: MagicMock = Depends(valid_response),
    option_init_result: config_entries.ConfigFlowResult = Depends(option_init_result),
) -> None:
    """Test the options flow departure time type."""
    menu_result = await hass.config_entries.options.async_configure(
        option_init_result["flow_id"], {"next_step_id": "departure_time"}
    )
    expect(menu_result["type"]).to_be(FlowResultType.FORM)
    time_selector_result = await hass.config_entries.options.async_configure(
        option_init_result["flow_id"],
        user_input={
            "departure_time": "08:00:00",
        },
    )

    expect(time_selector_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.options).to_equal(
        {
            CONF_ROUTE_MODE: ROUTE_MODE_FASTEST,
            CONF_DEPARTURE_TIME: "08:00:00",
            CONF_TRAFFIC_MODE: True,
        }
    )


@test
async def options_flow_no_time_step(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    _valid: MagicMock = Depends(valid_response),
    option_init_result: config_entries.ConfigFlowResult = Depends(option_init_result),
) -> None:
    """Test the options flow arrival time type."""
    menu_result = await hass.config_entries.options.async_configure(
        option_init_result["flow_id"], {"next_step_id": "no_time"}
    )

    expect(menu_result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.options).to_equal(
        {
            CONF_ROUTE_MODE: ROUTE_MODE_FASTEST,
            CONF_TRAFFIC_MODE: True,
        }
    )
