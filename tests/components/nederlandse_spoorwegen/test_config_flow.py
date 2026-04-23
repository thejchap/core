"""Test config flow for Nederlandse Spoorwegen integration."""

from __future__ import annotations

from unittest.mock import AsyncMock

from requests import ConnectionError as RequestsConnectionError, HTTPError, Timeout
from tryke import Depends, expect, fixture, test

from homeassistant.components.nederlandse_spoorwegen.const import (
    CONF_FROM,
    CONF_TIME,
    CONF_TO,
    CONF_VIA,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.nederlandse_spoorwegen._fixtures import (
    mock_config_entry,
    mock_nsapi,
    mock_setup_entry,
)
from tests.components.nederlandse_spoorwegen.const import API_KEY
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire fixtures for every test in the module."""


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _nsapi: AsyncMock = Depends(mock_nsapi),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: API_KEY}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Nederlandse Spoorwegen")
    expect(result["data"]).to_equal({CONF_API_KEY: API_KEY})
    expect(len(mock_setup_entry_.mock_calls)).to_equal(1)


@test
async def creating_route(
    hass: HomeAssistant = Depends(hass_fixture),
    _nsapi: AsyncMock = Depends(mock_nsapi),
    _mse: AsyncMock = Depends(mock_setup_entry),
    mock_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test creating a route after setting up the main config entry."""
    mock_entry.add_to_hass(hass)
    expect(len(mock_entry.subentries)).to_equal(2)
    result = await hass.config_entries.subentries.async_init(
        (mock_entry.entry_id, "route"), context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            CONF_FROM: "ASD",
            CONF_TO: "RTD",
            CONF_VIA: "HT",
            CONF_NAME: "Home to Work",
            CONF_TIME: "08:30",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Home to Work")
    expect(result["data"]).to_equal(
        {
            CONF_FROM: "ASD",
            CONF_TO: "RTD",
            CONF_VIA: "HT",
            CONF_NAME: "Home to Work",
            CONF_TIME: "08:30",
        }
    )
    expect(len(mock_entry.subentries)).to_equal(3)


@test.cases(
    test.case("invalid_auth_http", HTTPError("Invalid API key"), "invalid_auth"),
    test.case("cannot_connect_timeout", Timeout("Cannot connect"), "cannot_connect"),
    test.case(
        "cannot_connect_conn",
        RequestsConnectionError("Cannot connect"),
        "cannot_connect",
    ),
    test.case("unknown", Exception("Unexpected error"), "unknown"),
)
async def flow_exceptions(
    exception: Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_nsapi_: AsyncMock = Depends(mock_nsapi),
    mock_setup_entry_: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow handling different exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    mock_nsapi_.get_stations.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: API_KEY}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_nsapi_.get_stations.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: API_KEY}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Nederlandse Spoorwegen")
    expect(result["data"]).to_equal({CONF_API_KEY: API_KEY})
    expect(len(mock_setup_entry_.mock_calls)).to_equal(1)


@test
async def fetching_stations_failed(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_nsapi_: AsyncMock = Depends(mock_nsapi),
    _mse: AsyncMock = Depends(mock_setup_entry),
    mock_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test creating a route aborts when stations fetch fails."""
    mock_entry.add_to_hass(hass)
    expect(len(mock_entry.subentries)).to_equal(2)
    mock_nsapi_.get_stations.side_effect = RequestsConnectionError("Unexpected error")
    result = await hass.config_entries.subentries.async_init(
        (mock_entry.entry_id, "route"), context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config flow aborts if already configured."""
    mock_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: API_KEY}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _nsapi: AsyncMock = Depends(mock_nsapi),
    mock_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successfully reconfiguring (updating) the API key."""
    new_key = "new_api_key_123456"
    mock_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_entry.entry_id},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: new_key}
    )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reconfigure_successful")
    expect(mock_entry.data[CONF_API_KEY]).to_equal(new_key)


@test.cases(
    test.case("invalid_auth_http", HTTPError("Invalid API key"), "invalid_auth"),
    test.case("cannot_connect_timeout", Timeout("Cannot connect"), "cannot_connect"),
    test.case(
        "cannot_connect_conn",
        RequestsConnectionError("Cannot connect"),
        "cannot_connect",
    ),
    test.case("unknown", Exception("Unexpected error"), "unknown"),
)
async def reconfigure_errors(
    exception: Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_nsapi_: AsyncMock = Depends(mock_nsapi),
    mock_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow error handling."""
    mock_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_entry.entry_id},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    mock_nsapi_.get_stations.side_effect = exception

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "bad_key"}
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": expected_error})

    mock_nsapi_.get_stations.side_effect = None

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "new_valid_key"}
    )

    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reconfigure_successful")
    expect(mock_entry.data[CONF_API_KEY]).to_equal("new_valid_key")


@test
async def reconfigure_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _nsapi: AsyncMock = Depends(mock_nsapi),
    mock_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguring with an API key already in use by another entry."""
    mock_entry.add_to_hass(hass)

    second_entry = MockConfigEntry(
        domain=DOMAIN,
        title="NS Integration 2",
        data={CONF_API_KEY: "another_api_key_456"},
        unique_id="second_entry",
    )
    second_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": mock_entry.entry_id},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "another_api_key_456"}
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "already_configured"})
    expect(mock_entry.data[CONF_API_KEY]).to_equal(API_KEY)

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "new_unique_key_789"}
    )

    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reconfigure_successful")
    expect(mock_entry.data[CONF_API_KEY]).to_equal("new_unique_key_789")
