"""Test pushover config flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from pushover_complete import BadAPIRequestError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.pushover.const import CONF_USER_KEY, DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import MOCK_CONFIG
from ._fixtures import (
    mock_pushover as mock_pushover_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _mock_pushover: MagicMock = Depends(mock_pushover_fx),
    _setup: None = Depends(mock_setup_entry_fx),
) -> None:
    """Wire default mocks for every test."""


@test
async def flow_user(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test user initialized flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Pushover")
    expect(result["data"]).to_equal(MOCK_CONFIG)


@test
async def flow_user_key_api_key_exists(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with duplicate user key / api key pair."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_name_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with duplicate server."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        unique_id="MYUSERKEY",
    )
    entry.add_to_hass(hass)

    new_config = MOCK_CONFIG.copy()
    new_config[CONF_USER_KEY] = "NEUSERWKEY"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=new_config,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_invalid_user_key(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pushover: MagicMock = Depends(mock_pushover_fx),
) -> None:
    """Test user initialized flow with wrong user key."""
    mock_pushover.side_effect = BadAPIRequestError("400: user key is invalid")
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=MOCK_CONFIG,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({CONF_USER_KEY: "invalid_user_key"})


@test
async def flow_invalid_api_key(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pushover: MagicMock = Depends(mock_pushover_fx),
) -> None:
    """Test user initialized flow with wrong api key."""
    mock_pushover.side_effect = BadAPIRequestError("400: application token is invalid")
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=MOCK_CONFIG,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({CONF_API_KEY: "invalid_api_key"})


@test
async def flow_conn_err(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pushover: MagicMock = Depends(mock_pushover_fx),
) -> None:
    """Test user initialized flow with conn error."""
    mock_pushover.side_effect = BadAPIRequestError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=MOCK_CONFIG,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def reauth_success(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we can reauth."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "NEWAPIKEY"},
    )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("reauth_successful")


@test
async def reauth_failed(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pushover: MagicMock = Depends(mock_pushover_fx),
) -> None:
    """Test we can reauth."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_pushover.side_effect = BadAPIRequestError("400: application token is invalid")
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "WRONGAPIKEY"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({CONF_API_KEY: "invalid_api_key"})


@test
async def reauth_with_existing_config(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth fails if the api key entered exists in another entry."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG)
    entry.add_to_hass(hass)

    second_entry = MOCK_CONFIG.copy()
    second_entry[CONF_API_KEY] = "MYAPIKEY2"

    entry2 = MockConfigEntry(domain=DOMAIN, data=second_entry)
    entry2.add_to_hass(hass)

    result = await entry2.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: MOCK_CONFIG[CONF_API_KEY]},
    )

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
