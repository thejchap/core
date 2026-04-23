"""The tests for the emoncms_history init."""

from collections.abc import AsyncGenerator
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import aiohttp
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.const import CONF_API_KEY, CONF_URL, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import LogCapture, caplog, freezer, hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
async def emoncms_client() -> AsyncGenerator[AsyncMock]:
    """Mock pyemoncms client with successful responses."""
    with patch(
        "homeassistant.components.emoncms_history.EmoncmsClient", autospec=True
    ) as mock_client:
        client = mock_client.return_value
        client.async_input_post.return_value = '{"success": true}'
        yield client


@test
async def setup_valid_config(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
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
    hass.states.async_set("sensor.temp", "23.4", {"unit_of_measurement": "°C"})
    await hass.async_block_till_done()

    expect(await async_setup_component(hass, "emoncms_history", config)).to_be(True)
    await hass.async_block_till_done()


@test
async def setup_missing_config(hass: HomeAssistant = Depends(hass)) -> None:
    """Test setting up the emoncms_history component with missing configuration."""
    config = {"emoncms_history": {"api_key": "dummy"}}
    success = await async_setup_component(hass, "emoncms_history", config)
    expect(success).to_be(False)


@test
async def emoncms_send_data(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    emoncms_client: AsyncMock = Depends(emoncms_client),
    caplog: LogCapture = Depends(caplog),
    freezer: FrozenDateTimeFactory = Depends(freezer),
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
