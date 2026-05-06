"""Test the Cloudflare config flow."""

from unittest.mock import MagicMock

import pycfdns
from tryke import Depends, expect, fixture, test

from homeassistant.components.cloudflare.const import CONF_RECORDS, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_TOKEN, CONF_SOURCE, CONF_ZONE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    ENTRY_CONFIG,
    USER_INPUT,
    USER_INPUT_RECORDS,
    USER_INPUT_ZONE,
    patch_async_setup_entry,
)
from ._fixtures import cfupdate_flow

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _flow: MagicMock = Depends(cfupdate_flow),
) -> None:
    """Test we get the user initiated form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zone")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT_ZONE,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("records")
    expect(result["errors"]).to_be(None)

    with patch_async_setup_entry() as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT_RECORDS,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(USER_INPUT_ZONE[CONF_ZONE])

    expect(bool(result["data"])).to_be(True)
    expect(result["data"][CONF_API_TOKEN]).to_equal(USER_INPUT[CONF_API_TOKEN])
    expect(result["data"][CONF_ZONE]).to_equal(USER_INPUT_ZONE[CONF_ZONE])
    expect(result["data"][CONF_RECORDS]).to_equal(USER_INPUT_RECORDS[CONF_RECORDS])

    expect(bool(result["result"])).to_be(True)
    expect(result["result"].unique_id).to_equal(USER_INPUT_ZONE[CONF_ZONE])

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    flow: MagicMock = Depends(cfupdate_flow),
) -> None:
    """Test we handle cannot connect error."""
    instance = flow.return_value

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    instance.list_zones.side_effect = pycfdns.ComunicationException()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def user_form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    flow: MagicMock = Depends(cfupdate_flow),
) -> None:
    """Test we handle invalid auth error."""
    instance = flow.return_value

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    instance.list_zones.side_effect = pycfdns.AuthenticationException()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def user_form_unexpected_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    flow: MagicMock = Depends(cfupdate_flow),
) -> None:
    """Test we handle unexpected exception."""
    instance = flow.return_value

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    instance.list_zones.side_effect = Exception()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})


@test
async def user_form_single_instance_allowed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that configuring more than one instance is rejected."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _flow: MagicMock = Depends(cfupdate_flow),
) -> None:
    """Test the reauthentication configuration flow."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch_async_setup_entry() as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_TOKEN: "other_token"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(entry.data[CONF_API_TOKEN]).to_equal("other_token")
    expect(entry.data[CONF_ZONE]).to_equal(ENTRY_CONFIG[CONF_ZONE])
    expect(entry.data[CONF_RECORDS]).to_equal(ENTRY_CONFIG[CONF_RECORDS])

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
