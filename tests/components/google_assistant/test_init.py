"""The tests for google-assistant init."""

from http import HTTPStatus

from tryke import Depends, expect, fixture, test

from homeassistant.components import google_assistant as ga
from homeassistant.core import Context, HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import hass_fixture
from .test_http import DUMMY_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import aioclient_mock as aioclient_mock_fx
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def import_(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test import."""

    await async_setup_component(
        hass,
        ga.DOMAIN,
        {"google_assistant": DUMMY_CONFIG},
    )

    entries = hass.config_entries.async_entries("google_assistant")
    expect(len(entries)).to_equal(1)
    expect(entries[0].data[ga.const.CONF_PROJECT_ID]).to_equal("1234")


@test
async def import_changed(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test import with changed project id."""

    old_entry = MockConfigEntry(
        domain=ga.DOMAIN, data={ga.const.CONF_PROJECT_ID: "4321"}, source="import"
    )
    old_entry.add_to_hass(hass)

    await async_setup_component(
        hass,
        ga.DOMAIN,
        {"google_assistant": DUMMY_CONFIG},
    )
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries("google_assistant")
    expect(len(entries)).to_equal(1)
    expect(entries[0].data[ga.const.CONF_PROJECT_ID]).to_equal("1234")


@test
async def request_sync_service(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test that it posts to the request_sync url."""
    aioclient_mock.post(
        ga.const.HOMEGRAPH_TOKEN_URL,
        status=HTTPStatus.OK,
        json={"access_token": "1234", "expires_in": 3600},
    )

    aioclient_mock.post(ga.const.REQUEST_SYNC_BASE_URL, status=HTTPStatus.OK)

    await async_setup_component(
        hass,
        "google_assistant",
        {"google_assistant": DUMMY_CONFIG},
    )

    expect(aioclient_mock.call_count).to_equal(0)
    await hass.services.async_call(
        ga.const.DOMAIN,
        ga.const.SERVICE_REQUEST_SYNC,
        blocking=True,
        context=Context(user_id="123"),
    )

    expect(aioclient_mock.call_count).to_equal(2)  # token + request
