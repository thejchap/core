"""Tryke fixtures for the Netgear LTE integration."""

from collections.abc import AsyncGenerator

from aiohttp.client_exceptions import ClientError
from tryke import Depends, fixture

from homeassistant.components.netgear_lte.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONTENT_TYPE_JSON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import aioclient_mock
from tests.test_util.aiohttp import AiohttpClientMocker

HOST = "192.168.5.1"
PASSWORD = "password"

CONF_DATA = {CONF_HOST: HOST, CONF_PASSWORD: PASSWORD}


@fixture
def cannot_connect(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Mock cannot connect error."""
    aioclient_mock.get(f"http://{HOST}/model.json", exc=ClientError)
    aioclient_mock.post(f"http://{HOST}/Forms/config", exc=ClientError)


@fixture
def connection(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Mock Netgear LTE connection."""
    aioclient_mock.get(
        f"http://{HOST}/model.json",
        text=load_fixture("netgear_lte/model.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.post(
        f"http://{HOST}/Forms/config",
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.post(
        f"http://{HOST}/Forms/smsSendMsg",
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )


@fixture
def config_entry() -> MockConfigEntry:
    """Create Netgear LTE entry in Home Assistant."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=CONF_DATA,
        unique_id="FFFFFFFFFFFFF",
        title="Netgear LM1200",
    )


@fixture
async def setup_integration(
    hass: HomeAssistant,
    entry: MockConfigEntry = Depends(config_entry),
    _connection: None = Depends(connection),
) -> AsyncGenerator[None]:
    """Set up the Netgear LTE integration in Home Assistant."""
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
    yield None
