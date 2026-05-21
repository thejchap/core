"""Test cloud system health."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import MagicMock

from aiohttp import ClientError
from hass_nabucasa.remote import CertificateStatus
from tryke import Depends, expect, fixture, test

from homeassistant.components.cloud.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import cloud, load_homeassistant, set_cloud_prefs

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
    _load_homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def cloud_system_health(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    cloud: MagicMock = Depends(cloud),
    set_cloud_prefs: Callable[[dict[str, Any]], Awaitable[None]] = Depends(
        set_cloud_prefs
    ),
) -> None:
    """Test cloud system health."""
    aioclient_mock.get("https://cloud.bla.com/status", text="")
    aioclient_mock.get("https://cert-server/directory", text="")
    aioclient_mock.get(
        "https://cognito-idp.us-east-1.amazonaws.com/AAAA/.well-known/jwks.json",
        exc=ClientError,
    )
    expect(await async_setup_component(hass, "system_health", {})).to_be(True)
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "user_pool_id": "AAAA",
                    "region": "us-east-1",
                    "acme_server": "cert-server",
                    "relayer_server": "cloud.bla.com",
                },
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()
    await cloud.login("test-user", "test-pass")

    cloud.remote.snitun_server = "us-west-1"
    cloud.remote.certificate_status = CertificateStatus.READY

    await cloud.client.async_system_message({"region": "xx-earth-616"})
    await set_cloud_prefs(
        {
            "alexa_enabled": True,
            "google_enabled": False,
            "remote_enabled": True,
            "cloud_ice_servers_enabled": True,
        }
    )

    info = await get_system_health_info(hass, "cloud")

    for key, val in info.items():
        if asyncio.iscoroutine(val):
            info[key] = await val

    expect(info).to_equal(
        {
            "logged_in": True,
            "subscription_expiration": cloud.expiration_date,
            "certificate_status": CertificateStatus.READY,
            "relayer_connected": True,
            "relayer_region": "xx-earth-616",
            "remote_enabled": True,
            "remote_connected": False,
            "remote_server": "us-west-1",
            "alexa_enabled": True,
            "google_enabled": False,
            "cloud_ice_servers_enabled": True,
            "can_reach_cert_server": "ok",
            "can_reach_cloud_auth": {"type": "failed", "error": "unreachable"},
            "can_reach_cloud": "ok",
            "instance_id": cloud.client.prefs.instance_id,
        }
    )
