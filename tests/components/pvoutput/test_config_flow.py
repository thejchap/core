"""Tests for the PVOutput config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pvo import PVOutputAuthenticationError, PVOutputConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.pvoutput.const import CONF_SYSTEM_ID, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_pvoutput as mock_pvoutput_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pvoutput: MagicMock = Depends(mock_pvoutput_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_SYSTEM_ID: 12345, CONF_API_KEY: "tadaaa"},
    )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("12345")
    expect(result2.get("data")).to_equal(
        {CONF_SYSTEM_ID: 12345, CONF_API_KEY: "tadaaa"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_pvoutput.system.mock_calls)).to_equal(1)


@test
async def full_flow_with_authentication_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pvoutput: MagicMock = Depends(mock_pvoutput_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test the full user configuration flow with incorrect API key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    mock_pvoutput.system.side_effect = PVOutputAuthenticationError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_SYSTEM_ID: 12345, CONF_API_KEY: "invalid"},
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("user")
    expect(result2.get("errors")).to_equal({"base": "invalid_auth"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)
    expect(len(mock_pvoutput.system.mock_calls)).to_equal(1)

    mock_pvoutput.system.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_SYSTEM_ID: 12345, CONF_API_KEY: "tadaaa"},
    )

    expect(result3.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3.get("title")).to_equal("12345")
    expect(result3.get("data")).to_equal(
        {CONF_SYSTEM_ID: 12345, CONF_API_KEY: "tadaaa"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_pvoutput.system.mock_calls)).to_equal(2)


@test
async def connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pvoutput: MagicMock = Depends(mock_pvoutput_fx),
) -> None:
    """Test API connection error."""
    mock_pvoutput.system.side_effect = PVOutputConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_SYSTEM_ID: 12345, CONF_API_KEY: "tadaaa"},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": "cannot_connect"})
    expect(len(mock_pvoutput.system.mock_calls)).to_equal(1)


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    _mock: MagicMock = Depends(mock_pvoutput_fx),
) -> None:
    """Test we abort if the PVOutput system is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_SYSTEM_ID: 12345, CONF_API_KEY: "tadaaa"},
    )

    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("already_configured")


@test
async def reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_pvoutput: MagicMock = Depends(mock_pvoutput_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test the reauthentication configuration flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "some_new_key"},
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal(
        {CONF_SYSTEM_ID: 12345, CONF_API_KEY: "some_new_key"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_pvoutput.system.mock_calls)).to_equal(1)


@test
async def reauth_with_authentication_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_pvoutput: MagicMock = Depends(mock_pvoutput_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test the reauthentication configuration flow with an authentication error."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    mock_pvoutput.system.side_effect = PVOutputAuthenticationError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "invalid_key"},
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("reauth_confirm")
    expect(result2.get("errors")).to_equal({"base": "invalid_auth"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)
    expect(len(mock_pvoutput.system.mock_calls)).to_equal(1)

    mock_pvoutput.system.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_API_KEY: "valid_key"},
    )
    await hass.async_block_till_done()

    expect(result3.get("type")).to_be(FlowResultType.ABORT)
    expect(result3.get("reason")).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal(
        {CONF_SYSTEM_ID: 12345, CONF_API_KEY: "valid_key"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_pvoutput.system.mock_calls)).to_equal(2)


@test
async def reauth_api_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_pvoutput: MagicMock = Depends(mock_pvoutput_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test API error during reauthentication."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    mock_pvoutput.system.side_effect = PVOutputConnectionError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "some_new_key"},
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("reauth_confirm")
    expect(result2.get("errors")).to_equal({"base": "cannot_connect"})
