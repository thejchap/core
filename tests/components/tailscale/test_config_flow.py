"""Tests for the Tailscale config flow."""

from unittest.mock import AsyncMock, MagicMock

from tailscale import TailscaleAuthenticationError, TailscaleConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.tailscale.const import CONF_TAILNET, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_setup_entry, mock_tailscale_config_flow

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tailscale_flow: MagicMock = Depends(mock_tailscale_config_flow),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TAILNET: "homeassistant.github",
            CONF_API_KEY: "tskey-FAKE",
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("homeassistant.github")
    expect(result2.get("data")).to_equal(
        {
            CONF_TAILNET: "homeassistant.github",
            CONF_API_KEY: "tskey-FAKE",
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(tailscale_flow.devices.mock_calls)).to_equal(1)


@test
async def full_flow_with_authentication_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tailscale_flow: MagicMock = Depends(mock_tailscale_config_flow),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow with incorrect API key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    tailscale_flow.devices.side_effect = TailscaleAuthenticationError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TAILNET: "homeassistant.github",
            CONF_API_KEY: "tskey-INVALID",
        },
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("user")
    expect(result2.get("errors")).to_equal({"base": "invalid_auth"})

    expect(len(setup_entry.mock_calls)).to_equal(0)
    expect(len(tailscale_flow.devices.mock_calls)).to_equal(1)

    tailscale_flow.devices.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={
            CONF_TAILNET: "homeassistant.github",
            CONF_API_KEY: "tskey-VALID",
        },
    )

    expect(result3.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3.get("title")).to_equal("homeassistant.github")
    expect(result3.get("data")).to_equal(
        {
            CONF_TAILNET: "homeassistant.github",
            CONF_API_KEY: "tskey-VALID",
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(tailscale_flow.devices.mock_calls)).to_equal(2)


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tailscale_flow: MagicMock = Depends(mock_tailscale_config_flow),
) -> None:
    """Test API connection error."""
    tailscale_flow.devices.side_effect = TailscaleConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_TAILNET: "homeassistant.github",
            CONF_API_KEY: "tskey-FAKE",
        },
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": "cannot_connect"})

    expect(len(tailscale_flow.devices.mock_calls)).to_equal(1)


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    tailscale_flow: MagicMock = Depends(mock_tailscale_config_flow),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the reauthentication configuration flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "tskey-REAUTH"},
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(
        {
            CONF_TAILNET: "homeassistant.github",
            CONF_API_KEY: "tskey-REAUTH",
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(tailscale_flow.devices.mock_calls)).to_equal(1)


@test
async def reauth_with_authentication_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    tailscale_flow: MagicMock = Depends(mock_tailscale_config_flow),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the reauthentication configuration flow with an authentication error."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    tailscale_flow.devices.side_effect = TailscaleAuthenticationError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "tskey-INVALID"},
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("reauth_confirm")
    expect(result2.get("errors")).to_equal({"base": "invalid_auth"})

    expect(len(setup_entry.mock_calls)).to_equal(0)
    expect(len(tailscale_flow.devices.mock_calls)).to_equal(1)

    tailscale_flow.devices.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_API_KEY: "tskey-VALID"},
    )
    await hass.async_block_till_done()

    expect(result3.get("type")).to_be(FlowResultType.ABORT)
    expect(result3.get("reason")).to_equal("reauth_successful")
    expect(config_entry.data).to_equal(
        {
            CONF_TAILNET: "homeassistant.github",
            CONF_API_KEY: "tskey-VALID",
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(tailscale_flow.devices.mock_calls)).to_equal(2)


@test
async def reauth_api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tailscale_flow: MagicMock = Depends(mock_tailscale_config_flow),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test API error during reauthentication."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    tailscale_flow.devices.side_effect = TailscaleConnectionError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "tskey-VALID"},
    )
    await hass.async_block_till_done()

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("reauth_confirm")
    expect(result2.get("errors")).to_equal({"base": "cannot_connect"})
