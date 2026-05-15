"""The tests for the Foobot sensor platform."""

from http import HTTPStatus
import re
from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components import sensor
from homeassistant.components.foobot import sensor as foobot
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.setup import async_setup_component

from tests.common import async_load_fixture
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async
from tests.test_util.aiohttp import AiohttpClientMocker

VALID_CONFIG = {
    "platform": "foobot",
    "token": "adfdsfasd",
    "username": "example@example.com",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def default_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test the default setup."""
    aioclient.get(
        re.compile(r"api\.foobot\.io/v2/owner/.*"),
        text=await async_load_fixture(hass, "devices.json", "foobot"),
    )
    aioclient.get(
        re.compile(r"api\.foobot\.io/v2/device/.*"),
        text=await async_load_fixture(hass, "data.json", "foobot"),
    )
    expect(
        await async_setup_component(hass, sensor.DOMAIN, {"sensor": VALID_CONFIG})
    ).to_be(True)
    await hass.async_block_till_done()

    metrics = {
        "co2": ["1232.0", CONCENTRATION_PARTS_PER_MILLION],
        "temperature": ["21.1", UnitOfTemperature.CELSIUS],
        "humidity": ["49.5", PERCENTAGE],
        "pm2_5": ["144.8", CONCENTRATION_MICROGRAMS_PER_CUBIC_METER],
        "voc": ["340.7", CONCENTRATION_PARTS_PER_BILLION],
        "index": ["138.9", PERCENTAGE],
    }

    for name, value in metrics.items():
        state = hass.states.get(f"sensor.foobot_happybot_{name}")
        expect(state.state).to_equal(value[0])
        expect(state.attributes.get("unit_of_measurement")).to_equal(value[1])


@test
async def setup_timeout_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Expected failures caused by a timeout in API response."""
    fake_async_add_entities = MagicMock()

    aioclient.get(re.compile(r"api\.foobot\.io/v2/owner/.*"), exc=TimeoutError())
    async with expect_raises_async(PlatformNotReady):
        await foobot.async_setup_platform(hass, VALID_CONFIG, fake_async_add_entities)


@test
async def setup_permanent_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Expected failures caused by permanent errors in API response."""
    fake_async_add_entities = MagicMock()

    errors = [HTTPStatus.BAD_REQUEST, HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN]
    for error in errors:
        aioclient.get(re.compile(r"api\.foobot\.io/v2/owner/.*"), status=error)
        result = await foobot.async_setup_platform(
            hass, VALID_CONFIG, fake_async_add_entities
        )
        expect(result).to_be(None)


@test
async def setup_temporary_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Expected failures caused by temporary errors in API response."""
    fake_async_add_entities = MagicMock()

    errors = [HTTPStatus.TOO_MANY_REQUESTS, HTTPStatus.INTERNAL_SERVER_ERROR]
    for error in errors:
        aioclient.get(re.compile(r"api\.foobot\.io/v2/owner/.*"), status=error)
        async with expect_raises_async(PlatformNotReady):
            await foobot.async_setup_platform(
                hass, VALID_CONFIG, fake_async_add_entities
            )
