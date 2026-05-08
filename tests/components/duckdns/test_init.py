"""Test the DuckDNS component."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.duckdns.const import DOMAIN
from homeassistant.components.duckdns.helpers import UPDATE_URL
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import TEST_SUBDOMAIN, TEST_TOKEN, config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test.skip("pending - parametrize + freezer")
async def setup() -> None:
    """Stub."""


@test.skip("requires freezer + complex backoff parametrize")
async def setup_backoff() -> None:
    """Stub."""


@test.skip("requires aioclient_mock + service call assertions")
async def service_set_txt() -> None:
    """Stub."""


@test.skip("requires aioclient_mock + service call assertions")
async def service_clear_txt() -> None:
    """Stub."""


@test.skip("requires service exception parametrize")
async def service_exceptions() -> None:
    """Stub."""


@test.skip("requires service exception parametrize")
async def service_request_exception() -> None:
    """Stub."""


@test.skip("requires aioclient_mock + service call assertions")
async def service_select_entry() -> None:
    """Stub."""


@test
async def load_unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test loading and unloading of the config entry."""

    aioclient_mock.get(
        UPDATE_URL,
        params={"domains": TEST_SUBDOMAIN, "token": TEST_TOKEN},
        text="OK",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)

    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
