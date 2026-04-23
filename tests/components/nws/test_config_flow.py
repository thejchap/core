"""Test the National Weather Service (NWS) config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nws.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.nws._fixtures import mock_simple_nws_config
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    _nws: MagicMock = Depends(mock_simple_nws_config),
) -> None:
    """Test we get the form."""
    hass.config.latitude = 35
    hass.config.longitude = -90

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.nws.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"api_key": "test"}
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("ABC")
    expect(result2["data"]).to_equal(
        {
            "api_key": "test",
            "latitude": 35,
            "longitude": -90,
            "station": "ABC",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_nws: MagicMock = Depends(mock_simple_nws_config),
) -> None:
    """Test we handle cannot connect error."""
    mock_instance = mock_nws.return_value
    mock_instance.set_station.side_effect = aiohttp.ClientError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": "test"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_nws: MagicMock = Depends(mock_simple_nws_config),
) -> None:
    """Test we handle unknown error."""
    mock_instance = mock_nws.return_value
    mock_instance.set_station.side_effect = ValueError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": "test"},
    )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _nws: MagicMock = Depends(mock_simple_nws_config),
) -> None:
    """Test we handle duplicate entries."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nws.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"api_key": "test"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nws.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"api_key": "test"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)
