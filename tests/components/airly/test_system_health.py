"""Test Airly system health."""

import asyncio

from aiohttp import ClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.airly.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import init_integration

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
async def airly_system_health(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test Airly system health."""
    aioclient_mock.get("https://airapi.airly.eu/v2/", text="")

    await init_integration(hass, aioclient_mock)
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    await hass.async_block_till_done()

    info = await get_system_health_info(hass, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    expect(info["can_reach_server"]).to_equal("ok")
    expect(info["requests_remaining"]).to_equal(42)
    expect(info["requests_per_day"]).to_equal(100)


@test
async def airly_system_health_fail(
    _t: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test Airly system health failure."""
    aioclient_mock.get("https://airapi.airly.eu/v2/", exc=ClientError)

    await init_integration(hass, aioclient_mock)
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    await hass.async_block_till_done()

    info = await get_system_health_info(hass, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    expect(info["can_reach_server"]).to_equal(
        {"type": "failed", "error": "unreachable"}
    )
    expect(info["requests_remaining"]).to_equal(42)
    expect(info["requests_per_day"]).to_equal(100)
