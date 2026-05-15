"""Test the FreeDNS component."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import freedns
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow

from tests.common import async_fire_time_changed
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture, mock_network
from tests.test_util.aiohttp import AiohttpClientMocker

ACCESS_TOKEN = "test_token"
UPDATE_INTERVAL = freedns.DEFAULT_INTERVAL
UPDATE_URL = freedns.UPDATE_URL


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test setup works if update passes."""
    params = {}
    params[ACCESS_TOKEN] = ""
    aioclient.get(
        UPDATE_URL, params=params, text="ERROR: Address has not changed."
    )

    result = await async_setup_component(
        hass,
        freedns.DOMAIN,
        {
            freedns.DOMAIN: {
                "access_token": ACCESS_TOKEN,
                "scan_interval": UPDATE_INTERVAL,
            }
        },
    )
    expect(result).to_be(True)
    expect(aioclient.call_count).to_equal(1)

    async_fire_time_changed(hass, utcnow() + UPDATE_INTERVAL)
    await hass.async_block_till_done()
    expect(aioclient.call_count).to_equal(2)


@test
async def setup_fails_if_wrong_token(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test setup fails if first update fails through wrong token."""
    params = {}
    params[ACCESS_TOKEN] = ""
    aioclient.get(UPDATE_URL, params=params, text="ERROR: Invalid update URL (2)")

    result = await async_setup_component(
        hass,
        freedns.DOMAIN,
        {
            freedns.DOMAIN: {
                "access_token": ACCESS_TOKEN,
                "scan_interval": UPDATE_INTERVAL,
            }
        },
    )
    expect(result).to_be(False)
    expect(aioclient.call_count).to_equal(1)
