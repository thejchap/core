"""Test the OpenGarage config flow."""

from __future__ import annotations

from unittest.mock import patch

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.opengarage.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
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
            "opengarage.OpenGarage.update_state",
            return_value={"name": "Name of the device", "mac": "unique"},
        ),
        patch(
            "homeassistant.components.opengarage.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "http://1.1.1.1", "device_key": "AfsasdnfkjDD"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Name of the device")
    expect(result2["data"]).to_equal(
        {
            "host": "http://1.1.1.1",
            "device_key": "AfsasdnfkjDD",
            "port": 80,
            "verify_ssl": False,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "opengarage.OpenGarage.update_state",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "http://1.1.1.1", "device_key": "AfsasdnfkjDD"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "opengarage.OpenGarage.update_state",
        side_effect=aiohttp.ClientError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "http://1.1.1.1", "device_key": "AfsasdnfkjDD"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "opengarage.OpenGarage.update_state",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "http://1.1.1.1", "device_key": "AfsasdnfkjDD"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def flow_entry_already_exists(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user input for config_entry that already exists."""
    first_entry = MockConfigEntry(
        domain="opengarage",
        data={
            "host": "http://1.1.1.1",
            "device_key": "AfsasdnfkjDD",
        },
        unique_id="unique",
    )
    first_entry.add_to_hass(hass)

    with patch(
        "opengarage.OpenGarage.update_state",
        return_value={"name": "Name of the device", "mac": "unique"},
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                "host": "http://1.1.1.1",
                "device_key": "AfsasdnfkjDD",
                "port": 80,
                "verify_ssl": False,
            },
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
