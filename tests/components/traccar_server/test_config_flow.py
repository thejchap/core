"""Test the Traccar Server config flow."""

from unittest.mock import AsyncMock

from pytraccar import TraccarAuthenticationException, TraccarException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.traccar_server.const import (
    CONF_CUSTOM_ATTRIBUTES,
    CONF_EVENTS,
    CONF_MAX_ACCURACY,
    CONF_SKIP_ACCURACY_FILTER_FOR,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    CONF_API_TOKEN,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_traccar_api_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_traccar_api_client),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_API_TOKEN: "test-token",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("1.1.1.1:8082")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PORT: "8082",
            CONF_API_TOKEN: "test-token",
            CONF_SSL: False,
            CONF_VERIFY_SSL: True,
        }
    )
    expect(result["result"].state).to_be(ConfigEntryState.LOADED)


@test.cases(
    test.case("cannot_connect", side_effect=TraccarException, error="cannot_connect"),
    test.case("unknown", side_effect=Exception, error="unknown"),
)
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_traccar_api_client),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    client.get_server.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_API_TOKEN: "test-token",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    client.get_server.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_API_TOKEN: "test-token",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("1.1.1.1:8082")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PORT: "8082",
            CONF_API_TOKEN: "test-token",
            CONF_SSL: False,
            CONF_VERIFY_SSL: True,
        }
    )
    expect(result["result"].state).to_be(ConfigEntryState.LOADED)


@test
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_traccar_api_client),
) -> None:
    """Test options flow."""
    config_entry.add_to_hass(hass)

    expect(bool(await hass.config_entries.async_setup(config_entry.entry_id))).to_be(True)

    expect(config_entry.options.get(CONF_MAX_ACCURACY)).to_equal(5.0)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_MAX_ACCURACY: 2.0},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal(
        {
            CONF_MAX_ACCURACY: 2.0,
            CONF_EVENTS: [],
            CONF_CUSTOM_ATTRIBUTES: [],
            CONF_SKIP_ACCURACY_FILTER_FOR: [],
        }
    )


@test
async def abort_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_traccar_api_client),
) -> None:
    """Test abort for existing server."""
    config_entry.add_to_hass(hass)
    expect(bool(await hass.config_entries.async_setup(config_entry.entry_id))).to_be(True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_PORT: "8082",
            CONF_API_TOKEN: "test-token",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_traccar_api_client),
) -> None:
    """Test reauth flow."""
    config_entry.add_to_hass(hass)
    expect(bool(await hass.config_entries.async_setup(config_entry.entry_id))).to_be(True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": config_entry.entry_id,
        },
        data=config_entry.data,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_TOKEN: "new-token",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(config_entry.data[CONF_API_TOKEN]).to_equal("new-token")


@test.cases(
    test.case(
        "invalid_auth",
        side_effect=TraccarAuthenticationException,
        error="invalid_auth",
    ),
    test.case("cannot_connect", side_effect=TraccarException, error="cannot_connect"),
    test.case("unknown", side_effect=Exception, error="unknown"),
)
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_traccar_api_client),
    *,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test reauth flow with errors."""
    config_entry.add_to_hass(hass)
    expect(bool(await hass.config_entries.async_setup(config_entry.entry_id))).to_be(True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": config_entry.entry_id,
        },
        data=config_entry.data,
    )

    client.get_server.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_TOKEN: "new-token",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    client.get_server.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_TOKEN: "new-token",
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
