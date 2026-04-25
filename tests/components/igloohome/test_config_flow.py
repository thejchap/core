"""Test the igloohome config flow."""

from unittest.mock import AsyncMock

from aiohttp import ClientError
from igloohome_api import AuthException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.igloohome.const import DOMAIN
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import setup_integration
from ._fixtures import mock_api, mock_auth, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

FORM_USER_INPUT = {
    CONF_CLIENT_ID: "client-id",
    CONF_CLIENT_SECRET: "client-secret",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _api: AsyncMock = Depends(mock_api),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_valid_input(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _auth: AsyncMock = Depends(mock_auth),
) -> None:
    """Test that the form correct reacts to valid input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FORM_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Client Credentials")
    expect(result["data"]).to_equal(FORM_USER_INPUT)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", exception=AuthException(), result_error="invalid_auth"),
    test.case("cannot_connect", exception=ClientError(), result_error="cannot_connect"),
)
async def form_invalid_input(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    auth: AsyncMock = Depends(mock_auth),
    *,
    exception: Exception,
    result_error: str,
) -> None:
    """Tests where we handle errors in the config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    auth.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FORM_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": result_error})

    auth.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FORM_USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Client Credentials")
    expect(result["data"]).to_equal(FORM_USER_INPUT)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def form_abort_on_matching_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _auth: AsyncMock = Depends(mock_auth),
) -> None:
    """Tests where we handle errors in the config flow."""
    # Create first config flow.
    await setup_integration(hass, config_entry)

    # Attempt another config flow with the same client credentials
    # and ensure that FlowResultType.ABORT is returned.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FORM_USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
