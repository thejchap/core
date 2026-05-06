"""Tryke fixtures for the HERE Travel Time integration."""

from collections.abc import AsyncGenerator, Generator
import json
from unittest.mock import MagicMock, patch

from tryke import Depends, fixture

from homeassistant import config_entries
from homeassistant.components.here_travel_time.config_flow import (
    HERETravelTimeConfigFlow,
)
from homeassistant.components.here_travel_time.const import (
    CONF_DESTINATION_LATITUDE,
    CONF_DESTINATION_LONGITUDE,
    CONF_ORIGIN_LATITUDE,
    CONF_ORIGIN_LONGITUDE,
    DOMAIN,
    TRAVEL_MODE_CAR,
    TRAVEL_MODE_PUBLIC,
)
from homeassistant.const import CONF_API_KEY, CONF_MODE, CONF_NAME
from homeassistant.core import HomeAssistant

from .const import (
    API_KEY,
    DESTINATION_LATITUDE,
    DESTINATION_LONGITUDE,
    ORIGIN_LATITUDE,
    ORIGIN_LONGITUDE,
)

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture

RESPONSE = json.loads(load_fixture("here_travel_time/car_response.json"))
TRANSIT_RESPONSE = json.loads(
    load_fixture("here_travel_time/transit_route_response.json")
)
NO_ATTRIBUTION_TRANSIT_RESPONSE = json.loads(
    load_fixture("here_travel_time/no_attribution_transit_route_response.json")
)
BIKE_RESPONSE = json.loads(load_fixture("here_travel_time/bike_response.json"))


@fixture
def valid_response() -> Generator[MagicMock]:
    """Return valid api response."""
    with (
        patch("here_transit.HERETransitApi.route", return_value=TRANSIT_RESPONSE),
        patch(
            "here_routing.HERERoutingApi.route",
            return_value=RESPONSE,
        ) as mock,
    ):
        yield mock


@fixture
def bike_response() -> Generator[MagicMock]:
    """Return valid api response."""
    with (
        patch("here_transit.HERETransitApi.route", return_value=TRANSIT_RESPONSE),
        patch(
            "here_routing.HERERoutingApi.route",
            return_value=BIKE_RESPONSE,
        ) as mock,
    ):
        yield mock


@fixture
def no_attribution_response() -> Generator[MagicMock]:
    """Return valid api response without attribution."""
    with (
        patch(
            "here_transit.HERETransitApi.route",
            return_value=NO_ATTRIBUTION_TRANSIT_RESPONSE,
        ),
        patch(
            "here_routing.HERERoutingApi.route",
            return_value=RESPONSE,
        ) as mock,
    ):
        yield mock


@fixture
def bypass_setup() -> Generator[None]:
    """Prevent setup."""
    with patch(
        "homeassistant.components.here_travel_time.async_setup_entry",
        return_value=True,
    ):
        yield


@fixture
async def user_step_result(
    hass: HomeAssistant = Depends(hass_fixture),
    _bypass: None = Depends(bypass_setup),
) -> config_entries.ConfigFlowResult:
    """Provide the result of a completed user step."""
    init_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    user_step_result = await hass.config_entries.flow.async_configure(
        init_result["flow_id"],
        {
            CONF_API_KEY: API_KEY,
            CONF_MODE: TRAVEL_MODE_CAR,
            CONF_NAME: "test",
        },
    )
    await hass.async_block_till_done()
    return user_step_result


@fixture
async def option_init_result(
    hass: HomeAssistant = Depends(hass_fixture),
    _bypass: None = Depends(bypass_setup),
    _valid: MagicMock = Depends(valid_response),
) -> config_entries.ConfigFlowResult:
    """Provide the result of a completed options init step."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="0123456789",
        data={
            CONF_ORIGIN_LATITUDE: float(ORIGIN_LATITUDE),
            CONF_ORIGIN_LONGITUDE: float(ORIGIN_LONGITUDE),
            CONF_DESTINATION_LATITUDE: float(DESTINATION_LATITUDE),
            CONF_DESTINATION_LONGITUDE: float(DESTINATION_LONGITUDE),
            CONF_API_KEY: API_KEY,
            CONF_MODE: TRAVEL_MODE_PUBLIC,
            CONF_NAME: "test",
        },
        version=HERETravelTimeConfigFlow.VERSION,
        minor_version=HERETravelTimeConfigFlow.MINOR_VERSION,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    from homeassistant.components.here_travel_time.const import (  # noqa: PLC0415
        CONF_ROUTE_MODE,
        ROUTE_MODE_FASTEST,
    )

    return await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={
            CONF_ROUTE_MODE: ROUTE_MODE_FASTEST,
        },
    )


@fixture
async def origin_step_result(
    hass: HomeAssistant = Depends(hass_fixture),
    user_step_result: config_entries.ConfigFlowResult = Depends(user_step_result),
) -> config_entries.ConfigFlowResult:
    """Provide the result of a completed origin by coordinates step."""
    origin_menu_result = await hass.config_entries.flow.async_configure(
        user_step_result["flow_id"], {"next_step_id": "origin_coordinates"}
    )

    return await hass.config_entries.flow.async_configure(
        origin_menu_result["flow_id"],
        {
            "origin": {
                "latitude": float(ORIGIN_LATITUDE),
                "longitude": float(ORIGIN_LONGITUDE),
                "radius": 3.0,
            }
        },
    )
