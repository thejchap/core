"""Test the Wake on Lan config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.wake_on_lan.const import DOMAIN
from homeassistant.const import CONF_BROADCAST_ADDRESS, CONF_BROADCAST_PORT, CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    DEFAULT_MAC,
    mock_setup_entry,
    mock_subprocess_call,
    setup_loaded_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _subprocess: MagicMock = Depends(mock_subprocess_call),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_MAC: DEFAULT_MAC,
            CONF_BROADCAST_ADDRESS: "255.255.255.255",
            CONF_BROADCAST_PORT: 9,
        },
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["version"]).to_equal(1)
    expect(result["options"]).to_equal(
        {
            CONF_MAC: DEFAULT_MAC,
            CONF_BROADCAST_ADDRESS: "255.255.255.255",
            CONF_BROADCAST_PORT: 9,
        }
    )

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow."""
    loaded_entry = await setup_loaded_entry(hass)

    result = await hass.config_entries.options.async_init(loaded_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_BROADCAST_ADDRESS: "192.168.255.255",
            CONF_BROADCAST_PORT: 10,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_MAC: DEFAULT_MAC,
            CONF_BROADCAST_ADDRESS: "192.168.255.255",
            CONF_BROADCAST_PORT: 10,
        }
    )

    await hass.async_block_till_done()

    expect(loaded_entry.options).to_equal(
        {
            CONF_MAC: DEFAULT_MAC,
            CONF_BROADCAST_ADDRESS: "192.168.255.255",
            CONF_BROADCAST_PORT: 10,
        }
    )

    expect(len(hass.states.async_all())).to_equal(1)

    state = hass.states.get("button.wake_on_lan_00_01_02_03_04_05")
    expect(state is not None).to_be(True)


@test
async def entry_already_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test abort when entry already exist."""
    await setup_loaded_entry(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_MAC: DEFAULT_MAC,
            CONF_BROADCAST_ADDRESS: "255.255.255.255",
            CONF_BROADCAST_PORT: 9,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
