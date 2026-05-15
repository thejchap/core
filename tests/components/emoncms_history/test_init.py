"""The tests for the emoncms_history init."""

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant.const import CONF_API_KEY, CONF_URL, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import emoncms_client as emoncms_client_fixture

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network as mock_network_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network_fixture),
) -> HomeAssistant:
    return hass


@test
async def setup_valid_config(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting up the emoncms_history component with valid configuration."""
    config = {
        "emoncms_history": {
            CONF_API_KEY: "dummy",
            CONF_URL: "https://emoncms.example",
            "inputnode": 42,
            "whitelist": ["sensor.temp"],
        }
    }
    # Simulate a sensor
    hass.states.async_set("sensor.temp", "23.4", {"unit_of_measurement": "°C"})
    await hass.async_block_till_done()

    expect(await async_setup_component(hass, "emoncms_history", config)).to_be(True)
    await hass.async_block_till_done()


@test
async def setup_missing_config(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting up the emoncms_history component with missing configuration."""
    config = {"emoncms_history": {"api_key": "dummy"}}
    success = await async_setup_component(hass, "emoncms_history", config)
    expect(success).to_be(False)


@test
async def emoncms_send_data(
    hass: HomeAssistant = Depends(_trigger_executor),
    emoncms_client: AsyncMock = Depends(emoncms_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    freezer: Any = Depends(freezer_fixture),
) -> None:
    """Test sending data to Emoncms with and without success."""

    config = {
        "emoncms_history": {
            "api_key": "dummy",
            "url": "http://fake-url",
            "inputnode": 42,
            "whitelist": ["sensor.temp"],
        }
    }

    expect(await async_setup_component(hass, "emoncms_history", config)).to_be(True)
    await hass.async_block_till_done()

    for state in None, "", STATE_UNAVAILABLE, STATE_UNKNOWN:
        hass.states.async_set("sensor.temp", state, {"unit_of_measurement": "°C"})
        await hass.async_block_till_done()

        freezer.tick(timedelta(seconds=60))
        await hass.async_block_till_done()

        expect(emoncms_client.async_input_post.call_args is None).to_be(True)

    hass.states.async_set("sensor.temp", "not_a_number", {"unit_of_measurement": "°C"})
    await hass.async_block_till_done()

    freezer.tick(timedelta(seconds=60))
    await hass.async_block_till_done()

    emoncms_client.async_input_post.assert_not_called()

    hass.states.async_set("sensor.temp", "23.4", {"unit_of_measurement": "°C"})
    await hass.async_block_till_done()

    freezer.tick(timedelta(seconds=60))
    await hass.async_block_till_done()

    emoncms_client.async_input_post.assert_called_once()
    expect(emoncms_client.async_input_post.return_value).to_equal('{"success": true}')

    _, kwargs = emoncms_client.async_input_post.call_args
    expect(kwargs["data"]).to_equal({"sensor.temp": 23.4})
    expect(kwargs["node"]).to_equal("42")

    emoncms_client.async_input_post.side_effect = aiohttp.ClientError(
        "Connection refused"
    )
    await hass.async_block_till_done()

    freezer.tick(timedelta(seconds=60))
    await hass.async_block_till_done()

    expect(
        any(
            "Network error when sending data to Emoncms" in message
            for message in caplog.text.splitlines()
        )
    ).to_be(True)

    emoncms_client.async_input_post.side_effect = ValueError("Invalid value format")

    await hass.async_block_till_done()

    freezer.tick(timedelta(seconds=60))
    await hass.async_block_till_done()

    expect(
        any(
            "Value error when preparing data for Emoncms" in message
            for message in caplog.text.splitlines()
        )
    ).to_be(True)
