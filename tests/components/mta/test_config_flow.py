"""Test the MTA config flow."""

from unittest.mock import AsyncMock, MagicMock

from pymta import MTAFeedError
from tryke import Depends, expect, fixture, test

from homeassistant.components.mta.const import (
    CONF_LINE,
    CONF_ROUTE,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    DOMAIN,
    SUBENTRY_TYPE_BUS,
    SUBENTRY_TYPE_SUBWAY,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_bus_feed,
    mock_bus_feed_with_direction,
    mock_bus_subentry,
    mock_config_entry,
    mock_config_entry_with_api_key,
    mock_config_entry_with_bus_subentry,
    mock_config_entry_with_subway_subentry,
    mock_setup_entry,
    mock_subway_feed,
    mock_subway_subentry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def main_entry_flow_without_token(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the main config flow without API key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("MTA")
    expect(result["data"]).to_equal({CONF_API_KEY: None})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def main_entry_flow_with_token(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_bus_feed: MagicMock = Depends(mock_bus_feed),
) -> None:
    """Test the main config flow with API key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "test_api_key"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("MTA")
    expect(result["data"]).to_equal({CONF_API_KEY: "test_api_key"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def main_entry_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if MTA is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_bus_feed: MagicMock = Depends(mock_bus_feed),
) -> None:
    """Test the reauth flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "new_api_key"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_API_KEY]).to_equal("new_api_key")


@test.cases(
    test.case("connection_error", side_effect=MTAFeedError("Connection error"), expected_error="cannot_connect"),
    test.case("unknown_error", side_effect=RuntimeError("Unexpected error"), expected_error="unknown"),
)
async def reauth_flow_errors(
    side_effect: Exception,
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_bus_feed: MagicMock = Depends(mock_bus_feed),
) -> None:
    """Test the reauth flow with connection error."""
    mock_config_entry.add_to_hass(hass)
    mock_bus_feed.return_value.get_stops.side_effect = side_effect

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "bad_api_key"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_bus_feed.return_value.get_stops.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "api_key"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


# Subway subentry tests


@test
async def subway_subentry_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_subway_feed: MagicMock = Depends(mock_subway_feed),
) -> None:
    """Test the subway subentry flow."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, SUBENTRY_TYPE_SUBWAY),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_LINE: "1"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("stop")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "127N"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("1 - Times Sq - 42 St (N direction)")
    expect(result["data"]).to_equal({
        CONF_LINE: "1",
        CONF_STOP_ID: "127N",
        CONF_STOP_NAME: "Times Sq - 42 St (N direction)",
    })


@test
async def subway_subentry_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry_with_subway_subentry: MockConfigEntry = Depends(mock_config_entry_with_subway_subentry),
    mock_subway_feed: MagicMock = Depends(mock_subway_feed),
) -> None:
    """Test subway subentry already configured."""
    mock_config_entry_with_subway_subentry.add_to_hass(hass)
    await hass.config_entries.async_setup(
        mock_config_entry_with_subway_subentry.entry_id
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry_with_subway_subentry.entry_id, SUBENTRY_TYPE_SUBWAY),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_LINE: "1"}
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "127N"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def subway_subentry_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_subway_feed: MagicMock = Depends(mock_subway_feed),
) -> None:
    """Test subway subentry flow with connection error."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_subway_feed.return_value.get_arrivals.side_effect = MTAFeedError(
        "Connection error"
    )

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, SUBENTRY_TYPE_SUBWAY),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_LINE: "1"}
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "127N"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def subway_subentry_cannot_get_stops(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_subway_feed: MagicMock = Depends(mock_subway_feed),
) -> None:
    """Test subway subentry flow when cannot get stops."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_subway_feed.return_value.get_stops.side_effect = MTAFeedError("Feed error")

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, SUBENTRY_TYPE_SUBWAY),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_LINE: "1"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def subway_subentry_no_stops_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_subway_feed: MagicMock = Depends(mock_subway_feed),
) -> None:
    """Test subway subentry flow when no stops are found."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_subway_feed.return_value.get_stops.return_value = []

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, SUBENTRY_TYPE_SUBWAY),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_LINE: "1"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_stops")


# Bus subentry tests


@test
async def bus_subentry_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry_with_api_key: MockConfigEntry = Depends(mock_config_entry_with_api_key),
    mock_bus_feed: MagicMock = Depends(mock_bus_feed),
) -> None:
    """Test the bus subentry flow."""
    mock_config_entry_with_api_key.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry_with_api_key.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry_with_api_key.entry_id, SUBENTRY_TYPE_BUS),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_ROUTE: "M15"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("stop")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "400561"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("M15 - 1 Av/E 79 St")
    expect(result["data"]).to_equal({
        CONF_ROUTE: "M15",
        CONF_STOP_ID: "400561",
        CONF_STOP_NAME: "1 Av/E 79 St",
    })


@test
async def bus_subentry_flow_without_token(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_bus_feed: MagicMock = Depends(mock_bus_feed),
) -> None:
    """Test the bus subentry flow without API token (space workaround)."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, SUBENTRY_TYPE_BUS),
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_ROUTE: "M15"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("stop")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "400561"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def bus_subentry_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry_with_bus_subentry: MockConfigEntry = Depends(mock_config_entry_with_bus_subentry),
    mock_bus_feed: MagicMock = Depends(mock_bus_feed),
) -> None:
    """Test bus subentry already configured."""
    mock_config_entry_with_bus_subentry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry_with_bus_subentry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry_with_bus_subentry.entry_id, SUBENTRY_TYPE_BUS),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_ROUTE: "M15"}
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "400561"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def bus_subentry_invalid_route(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry_with_api_key: MockConfigEntry = Depends(mock_config_entry_with_api_key),
    mock_bus_feed: MagicMock = Depends(mock_bus_feed),
) -> None:
    """Test bus subentry flow with invalid route."""
    mock_config_entry_with_api_key.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry_with_api_key.entry_id)
    await hass.async_block_till_done()

    mock_bus_feed.return_value.get_stops.return_value = []

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry_with_api_key.entry_id, SUBENTRY_TYPE_BUS),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_ROUTE: "INVALID"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_route"})


@test
async def bus_subentry_route_fetch_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry_with_api_key: MockConfigEntry = Depends(mock_config_entry_with_api_key),
    mock_bus_feed: MagicMock = Depends(mock_bus_feed),
) -> None:
    """Test bus subentry flow when route fetch fails (treated as invalid route)."""
    mock_config_entry_with_api_key.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry_with_api_key.entry_id)
    await hass.async_block_till_done()

    mock_bus_feed.return_value.get_stops.side_effect = MTAFeedError("Connection error")

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry_with_api_key.entry_id, SUBENTRY_TYPE_BUS),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_ROUTE: "M15"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_route"})

    mock_bus_feed.return_value.get_stops.side_effect = None

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_ROUTE: "M15"}
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "400561"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def bus_subentry_connection_test_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry_with_api_key: MockConfigEntry = Depends(mock_config_entry_with_api_key),
    mock_bus_feed: MagicMock = Depends(mock_bus_feed),
) -> None:
    """Test bus subentry flow when connection test fails after route validation."""
    mock_config_entry_with_api_key.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry_with_api_key.entry_id)
    await hass.async_block_till_done()

    mock_bus_feed.return_value.get_arrivals.side_effect = MTAFeedError(
        "Connection error"
    )

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry_with_api_key.entry_id, SUBENTRY_TYPE_BUS),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_ROUTE: "M15"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("stop")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "400561"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    mock_bus_feed.return_value.get_arrivals.side_effect = None

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "400561"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def bus_subentry_with_direction(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry_with_api_key: MockConfigEntry = Depends(mock_config_entry_with_api_key),
    mock_bus_feed_with_direction: MagicMock = Depends(mock_bus_feed_with_direction),
) -> None:
    """Test bus subentry flow shows direction for stops."""
    mock_config_entry_with_api_key.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry_with_api_key.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry_with_api_key.entry_id, SUBENTRY_TYPE_BUS),
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_ROUTE: "M15"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("stop")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_STOP_ID: "400561"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("M15 - 1 Av/E 79 St (to South Ferry)")
    expect(result["data"][CONF_STOP_NAME]).to_equal("1 Av/E 79 St (to South Ferry)")
