"""Test Netgear LTE config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.netgear_lte.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.netgear_lte._fixtures import (
    CONF_DATA,
    cannot_connect,
    connection,
    setup_integration,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


def _patch_setup():
    return patch(
        "homeassistant.components.netgear_lte.async_setup_entry", return_value=True
    )


@test
async def flow_user_form(
    hass: HomeAssistant = Depends(hass_fixture),
    _connection: None = Depends(connection),
) -> None:
    """Test that the user set up form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with _patch_setup():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DATA,
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Netgear LM1200")
    expect(result["data"]).to_equal(CONF_DATA)
    expect(result["context"]["unique_id"]).to_equal("FFFFFFFFFFFFF")


@test
async def flow_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_integration),
) -> None:
    """Test config flow aborts when already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=CONF_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_user_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    _cannot: None = Depends(cannot_connect),
) -> None:
    """Test connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=CONF_DATA,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("cannot_connect")
