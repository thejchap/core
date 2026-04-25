"""Test the Time & Date config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.time_date.const import CONF_DISPLAY_OPTIONS, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the forms."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"display_options": "time"},
    )
    await hass.async_block_till_done()

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_does_not_allow_beat(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the forms."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    raised = False
    try:
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"display_options": ["beat"]},
        )
    except vol.Invalid:
        raised = True
    expect(raised).to_be(True)


@test
async def single_instance(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the forms."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={}, options={CONF_DISPLAY_OPTIONS: "time"}
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"display_options": "time"},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def timezone_not_set(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test time zone not set."""
    hass.config.time_zone = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"display_options": "time"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "timezone_not_exist"})


@test.skip("uses hass_ws_client (WebSocketGenerator)")
async def config_flow_preview(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow preview."""
