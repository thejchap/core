"""Unit tests for iottycloud API."""

from aiohttp import ClientSession
from tryke import Depends, fixture, test

from homeassistant.components.iotty import api
from homeassistant.components.iotty.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import aiohttp_client_session, local_oauth_impl, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fx,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def api_create_fail(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test API creation with no session."""
    async with expect_raises_async(ValueError, match="websession"):
        api.IottyProxy(hass, None, None)

    async with expect_raises_async(ValueError, match="oauth_session"):
        api.IottyProxy(hass, aioclient_mock, None)


@test
async def api_create_ok(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    session_cls: type[ClientSession] = Depends(aiohttp_client_session),
    impl: config_entry_oauth2_flow.LocalOAuth2Implementation = Depends(
        local_oauth_impl
    ),
) -> None:
    """Test API creation succeeds with a registered local OAuth2 impl."""
    entry.add_to_hass(hass)
    assert entry.data["auth_implementation"] is not None

    config_entry_oauth2_flow.async_register_implementation(hass, DOMAIN, impl)

    api.IottyProxy(hass, session_cls, impl)


@test.skip(
    "requires patching OAuth2Session.valid_token + aioclient_mock token reload chain"
)
async def api_getaccesstoken_tokennotvalid_reloadtoken() -> None:
    """Stub for test_api_getaccesstoken_tokennotvalid_reloadtoken."""
