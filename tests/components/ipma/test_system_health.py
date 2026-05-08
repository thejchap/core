"""Test ipma system health."""

import asyncio

from tryke import Depends, expect, fixture, test

from homeassistant.components.ipma.system_health import IPMA_API_URL
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import get_system_health_info
from tests.hass_fixtures import aioclient_mock as aioclient_mock_fixture, hass as hass_fixture
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def ipma_system_health(
    hass: HomeAssistant = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test ipma system health."""
    aioclient_mock.get(IPMA_API_URL, json={"result": "ok", "data": {}})

    hass.config.components.add("ipma")
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    await hass.async_block_till_done()

    info = await get_system_health_info(hass, "ipma")

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    expect(info).to_equal({"api_endpoint_reachable": "ok"})
