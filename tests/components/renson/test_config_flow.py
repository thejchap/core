"""Test the Renson config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.renson.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with (
        patch(
            "homeassistant.components.renson.config_flow.renson",
            return_value={"title": "Renson"},
        ),
        patch(
            "homeassistant.components.renson.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.1.1.1"}
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Renson")
    expect(result2["data"]).to_equal({"host": "1.1.1.1"})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.renson.config_flow.renson.RensonVentilation.connect",
        return_value=False,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.1.1.1"}
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.renson.config_flow.renson.RensonVentilation.connect",
        side_effect=ValueError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "1.1.1.1"}
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})
