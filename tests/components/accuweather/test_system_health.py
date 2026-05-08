"""Test AccuWeather system health."""

import asyncio
from unittest.mock import AsyncMock

from aiohttp import ClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.accuweather.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import init_integration
from ._fixtures import mock_accuweather_client

from tests.common import get_system_health_info
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import mock_async_zeroconf
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _zc: None = Depends(mock_async_zeroconf),
) -> None:
    """Per-module trigger to anchor fixture resolution."""


@test
async def accuweather_system_health(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test AccuWeather system health."""
    aioclient_mock.get("https://dataservice.accuweather.com/", text="")

    await init_integration(hass)
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    await hass.async_block_till_done()

    info = await get_system_health_info(hass, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    expect(info).to_equal(
        {
            "can_reach_server": "ok",
            "remaining_requests": 10,
        }
    )


@test
async def accuweather_system_health_fail(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    mock_accuweather_client: AsyncMock = Depends(mock_accuweather_client),
) -> None:
    """Test AccuWeather system health failure."""
    aioclient_mock.get("https://dataservice.accuweather.com/", exc=ClientError)

    await init_integration(hass)
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    await hass.async_block_till_done()

    info = await get_system_health_info(hass, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    expect(info).to_equal(
        {
            "can_reach_server": {"type": "failed", "error": "unreachable"},
            "remaining_requests": 10,
        }
    )
