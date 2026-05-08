"""Unit tests for iottycloud API."""

from tryke import Depends, fixture, test

from homeassistant.components.iotty import api
from homeassistant.core import HomeAssistant

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


@test.skip("requires OAuth2 application credentials + local_oauth_impl chain")
async def api_create_ok() -> None:
    """Stub for test_api_create_ok."""


@test.skip("requires OAuth2 application credentials + local_oauth_impl chain")
async def api_getaccesstoken_tokennotvalid_reloadtoken() -> None:
    """Stub for test_api_getaccesstoken_tokennotvalid_reloadtoken."""
