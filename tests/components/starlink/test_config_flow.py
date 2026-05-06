"""Test the Starlink config flow."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.starlink.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .patchers import DEVICE_FOUND_PATCHER, NO_DEVICE_PATCHER, SETUP_ENTRY_PATCHER

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def flow_user_fails_can_succeed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow can still succeed after failure when Starlink is available."""
    user_input = {CONF_IP_ADDRESS: "192.168.100.1:9200"}

    with NO_DEVICE_PATCHER, SETUP_ENTRY_PATCHER:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(True)

    with DEVICE_FOUND_PATCHER, SETUP_ENTRY_PATCHER:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(user_input)


@test
async def flow_user_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow succeeds when Starlink is available."""
    user_input = {CONF_IP_ADDRESS: "192.168.100.1:9200"}

    with DEVICE_FOUND_PATCHER, SETUP_ENTRY_PATCHER:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(user_input)


@test
async def flow_user_duplicate_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow aborts when Starlink is already configured."""
    user_input = {CONF_IP_ADDRESS: "192.168.100.1:9200"}

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=user_input,
        unique_id="some-valid-id",
        state=config_entries.ConfigEntryState.LOADED,
    )
    entry.add_to_hass(hass)

    with DEVICE_FOUND_PATCHER, SETUP_ENTRY_PATCHER:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
