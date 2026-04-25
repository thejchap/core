"""Test the Trend config flow."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.trend import async_setup_entry
from homeassistant.components.trend.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import config_entry as config_entry_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "CPU Temperature rising", "entity_id": "sensor.cpu_temp"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.trend.async_setup_entry", wraps=async_setup_entry
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "invert": False,
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("CPU Temperature rising")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "entity_id": "sensor.cpu_temp",
            "invert": False,
            "name": "CPU Temperature rising",
        }
    )


@test
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test options flow."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "min_samples": 30,
            "max_samples": 50,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "min_samples": 30,
            "max_samples": 50,
            "entity_id": "sensor.cpu_temp",
            "invert": False,
            "min_gradient": 0.0,
            "name": "My trend",
            "sample_duration": 0.0,
        }
    )
