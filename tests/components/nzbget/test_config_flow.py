"""Test the NZBGet config flow."""

from __future__ import annotations

from unittest.mock import patch

from pynzbgetapi import NZBGetAPIException
from tryke import Depends, expect, fixture, test

from homeassistant.components.nzbget.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from . import (
    ENTRY_CONFIG,
    USER_INPUT,
    _patch_async_setup_entry,
    _patch_history,
    _patch_status,
    _patch_version,
)


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def user_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the user initiated form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        _patch_version(),
        _patch_status(),
        _patch_history(),
        _patch_async_setup_entry() as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.10.10.30")
    expect(result["data"]).to_equal({**USER_INPUT, CONF_VERIFY_SSL: False})

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_form_show_advanced_options(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the user initiated form with advanced options shown."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER, "show_advanced_options": True}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    user_input_advanced = {
        **USER_INPUT,
        CONF_VERIFY_SSL: True,
    }

    with (
        _patch_version(),
        _patch_status(),
        _patch_history(),
        _patch_async_setup_entry() as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input_advanced,
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("10.10.10.30")
    expect(result["data"]).to_equal({**USER_INPUT, CONF_VERIFY_SSL: True})

    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_form_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nzbget.coordinator.NZBGetAPI.version",
        side_effect=NZBGetAPIException(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def user_form_unexpected_exception(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unexpected exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nzbget.coordinator.NZBGetAPI.version",
        side_effect=Exception(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def user_form_single_instance_allowed(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that configuring more than one instance is rejected."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=USER_INPUT,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
