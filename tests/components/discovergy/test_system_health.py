"""Test Discovergy system health."""

import asyncio

from aiohttp import ClientError
from pydiscovergy.const import API_BASE
from tryke import Depends, expect, fixture, test

from homeassistant.components.discovergy.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration
from homeassistant.setup import async_setup_component

from tests.common import get_system_health_info
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def discovergy_system_health(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test Discovergy system health."""
    aioclient_mock.get(API_BASE, text="")
    integration = await async_get_integration(hass, DOMAIN)
    await integration.async_get_component()
    hass.config.components.add(DOMAIN)
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    await hass.async_block_till_done()

    info = await get_system_health_info(hass, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    expect(info).to_equal({"api_endpoint_reachable": "ok"})


@test
async def discovergy_system_health_fail(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test Discovergy system health."""
    aioclient_mock.get(API_BASE, exc=ClientError)
    integration = await async_get_integration(hass, DOMAIN)
    await integration.async_get_component()
    hass.config.components.add(DOMAIN)
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    await hass.async_block_till_done()

    info = await get_system_health_info(hass, DOMAIN)

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    expect(info).to_equal(
        {"api_endpoint_reachable": {"type": "failed", "error": "unreachable"}}
    )
