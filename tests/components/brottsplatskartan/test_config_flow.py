"""Test the Brottsplatskartan config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.brottsplatskartan.const import CONF_AREA, DOMAIN
from homeassistant.const import CONF_LATITUDE, CONF_LOCATION, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.brottsplatskartan._fixtures import (
    mock_setup_entry,
    uuid_generator,
)
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _uuid_generator: AsyncMock = Depends(uuid_generator),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("Brottsplatskartan HOME")
    expect(result2["data"]).to_equal(
        {
            "area": None,
            "latitude": hass.config.latitude,
            "longitude": hass.config.longitude,
            "app_id": "ha-1234567890",
        }
    )


@test
async def form_location(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _uuid_generator: AsyncMock = Depends(uuid_generator),
) -> None:
    """Test we get the form using location."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LOCATION: {
                CONF_LATITUDE: 59.32,
                CONF_LONGITUDE: 18.06,
            },
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("Brottsplatskartan 59.32, 18.06")
    expect(result2["data"]).to_equal(
        {
            "area": None,
            "latitude": 59.32,
            "longitude": 18.06,
            "app_id": "ha-1234567890",
        }
    )


@test
async def form_area(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _uuid_generator: AsyncMock = Depends(uuid_generator),
) -> None:
    """Test we get the form using area."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LOCATION: {
                CONF_LATITUDE: 59.32,
                CONF_LONGITUDE: 18.06,
            },
            CONF_AREA: "Stockholms län",
        },
    )
    await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal("Brottsplatskartan Stockholms län")
    expect(result2["data"]).to_equal(
        {
            "latitude": None,
            "longitude": None,
            "area": "Stockholms län",
            "app_id": "ha-1234567890",
        }
    )
