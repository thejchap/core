"""Test the Google Maps Travel Time config flow."""

from unittest.mock import AsyncMock, patch

from google.api_core.exceptions import (
    GatewayTimeout,
    GoogleAPIError,
    PermissionDenied,
    Unauthorized,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.google_travel_time.const import (
    ARRIVAL_TIME,
    CONF_ARRIVAL_TIME,
    CONF_AVOID,
    CONF_DEPARTURE_TIME,
    CONF_DESTINATION,
    CONF_ORIGIN,
    CONF_TIME,
    CONF_TIME_TYPE,
    CONF_TRAFFIC_MODEL,
    CONF_TRANSIT_MODE,
    CONF_TRANSIT_ROUTING_PREFERENCE,
    CONF_UNITS,
    DEFAULT_NAME,
    DEPARTURE_TIME,
    DOMAIN,
    UNITS_IMPERIAL,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_LANGUAGE, CONF_MODE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import make_mock_config, mock_setup_entry, routes_mock
from .const import DEFAULT_OPTIONS, MOCK_CONFIG, RECONFIGURE_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


async def _assert_common_create_steps(hass: HomeAssistant, result: dict) -> None:
    """Step through and assert the happy case create flow."""
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_CONFIG,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_API_KEY: "api_key",
            CONF_ORIGIN: "location1",
            CONF_DESTINATION: "49.983862755708444,8.223882827079068",
        }
    )


async def _assert_common_reconfigure_steps(hass: HomeAssistant, result: dict) -> None:
    """Step through and assert the happy case reconfigure flow."""
    client_mock = AsyncMock()
    with (
        patch(
            "homeassistant.components.google_travel_time.helpers.RoutesAsyncClient",
            return_value=client_mock,
        ),
        patch(
            "homeassistant.components.google_travel_time.sensor.RoutesAsyncClient",
            return_value=client_mock,
        ),
    ):
        client_mock.compute_routes.return_value = None
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            RECONFIGURE_CONFIG,
        )
        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("reconfigure_successful")
        await hass.async_block_till_done()
        entry = hass.config_entries.async_entries(DOMAIN)[0]
        expect(entry.data).to_equal(RECONFIGURE_CONFIG)


@test
async def minimum_fields(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _routes: AsyncMock = Depends(routes_mock),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"] is None).to_be(True)
    await _assert_common_create_steps(hass, result)


@test.cases(
    test.case(
        "google_api_error",
        exception=GoogleAPIError("test"),
        error="cannot_connect",
    ),
    test.case(
        "gateway_timeout",
        exception=GatewayTimeout("Timeout error."),
        error="timeout_connect",
    ),
    test.case(
        "unauthorized",
        exception=Unauthorized("Invalid API key."),
        error="invalid_auth",
    ),
    test.case(
        "permission_denied",
        exception=PermissionDenied(
            "Requests to this API routes.googleapis.com method google.maps.routing.v2.Routes.ComputeRoutes are blocked."
        ),
        error="permission_denied",
    ),
)
async def errors(
    *,
    exception: Exception,
    error: str,
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    routes: AsyncMock = Depends(routes_mock),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Test errors in the flow."""
    routes.compute_routes.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"] is None).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_CONFIG,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    routes.compute_routes.side_effect = None
    await _assert_common_create_steps(hass, result)


@test
async def reconfigure(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _routes: AsyncMock = Depends(routes_mock),
    _setup: None = Depends(mock_setup_entry),
    make_config=Depends(make_mock_config),
) -> None:
    """Test reconfigure flow."""
    mock_config = await make_config(MOCK_CONFIG, DEFAULT_OPTIONS)
    result = await mock_config.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    await _assert_common_reconfigure_steps(hass, result)


@test
async def options_flow(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _routes: AsyncMock = Depends(routes_mock),
    make_config=Depends(make_mock_config),
) -> None:
    """Test options flow."""
    mock_config = await make_config(MOCK_CONFIG, DEFAULT_OPTIONS)
    result = await hass.config_entries.options.async_init(mock_config.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_MODE: "driving",
            CONF_LANGUAGE: "en",
            CONF_AVOID: "tolls",
            CONF_UNITS: UNITS_IMPERIAL,
            CONF_TIME_TYPE: ARRIVAL_TIME,
            CONF_TIME: "08:00",
            CONF_TRAFFIC_MODEL: "best_guess",
            CONF_TRANSIT_MODE: "train",
            CONF_TRANSIT_ROUTING_PREFERENCE: "less_walking",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("")
    expected = {
        CONF_MODE: "driving",
        CONF_LANGUAGE: "en",
        CONF_AVOID: "tolls",
        CONF_UNITS: UNITS_IMPERIAL,
        CONF_ARRIVAL_TIME: "08:00",
        CONF_TRAFFIC_MODEL: "best_guess",
        CONF_TRANSIT_MODE: "train",
        CONF_TRANSIT_ROUTING_PREFERENCE: "less_walking",
    }
    expect(result["data"]).to_equal(expected)
    expect(mock_config.options).to_equal(expected)


@test
async def options_flow_departure_time(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _routes: AsyncMock = Depends(routes_mock),
    make_config=Depends(make_mock_config),
) -> None:
    """Test options flow with departure time."""
    mock_config = await make_config(MOCK_CONFIG, DEFAULT_OPTIONS)
    result = await hass.config_entries.options.async_init(mock_config.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_MODE: "driving",
            CONF_LANGUAGE: "en",
            CONF_AVOID: "tolls",
            CONF_UNITS: UNITS_IMPERIAL,
            CONF_TIME_TYPE: DEPARTURE_TIME,
            CONF_TIME: "08:00",
            CONF_TRAFFIC_MODEL: "best_guess",
            CONF_TRANSIT_MODE: "train",
            CONF_TRANSIT_ROUTING_PREFERENCE: "less_walking",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expected = {
        CONF_MODE: "driving",
        CONF_LANGUAGE: "en",
        CONF_AVOID: "tolls",
        CONF_UNITS: UNITS_IMPERIAL,
        CONF_DEPARTURE_TIME: "08:00",
        CONF_TRAFFIC_MODEL: "best_guess",
        CONF_TRANSIT_MODE: "train",
        CONF_TRANSIT_ROUTING_PREFERENCE: "less_walking",
    }
    expect(result["data"]).to_equal(expected)
    expect(mock_config.options).to_equal(expected)


@test
async def dupe(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _routes: AsyncMock = Depends(routes_mock),
    _setup: None = Depends(mock_setup_entry),
    make_config=Depends(make_mock_config),
) -> None:
    """Test setting up the same entry data twice is OK."""
    await make_config(MOCK_CONFIG, DEFAULT_OPTIONS)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"] is None).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_KEY: "test",
            CONF_ORIGIN: "location1",
            CONF_DESTINATION: "49.983862755708444,8.223882827079068",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.skip("complex multi-parametrize options flow not yet ported")
async def reconfigure_invalid_config_entry(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""


@test.skip("complex multi-parametrize options flow not yet ported")
async def reset_departure_time(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test resetting departure time."""


@test.skip("complex multi-parametrize options flow not yet ported")
async def reset_arrival_time(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test resetting arrival time."""


@test.skip("complex multi-parametrize options flow not yet ported")
async def reset_options_flow_fields(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test resetting options flow fields that are not time related to None."""
