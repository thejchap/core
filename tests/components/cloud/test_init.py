"""Test the cloud component."""

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.cloud.const import DATA_CLOUD, MODE_DEV
from homeassistant.components.cloud.prefs import STORAGE_KEY
from homeassistant.const import CONF_MODE
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import load_homeassistant

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _load_homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def constructor_loads_info_from_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test non-dev mode loads info from SERVERS constant."""
    with patch("hass_nabucasa.Cloud.initialize"):
        result = await async_setup_component(
            hass,
            "cloud",
            {
                "http": {},
                "cloud": {
                    CONF_MODE: MODE_DEV,
                    "cognito_client_id": "test-cognito_client_id",
                    "user_pool_id": "test-user_pool_id",
                    "region": "test-region",
                    "api_server": "test-api-server",
                    "relayer_server": "test-relayer-server",
                    "acme_server": "test-acme-server",
                    "remotestate_server": "test-remotestate-server",
                    "discovery_service_actions": {
                        "lorem_ipsum": "https://lorem.ipsum/test-url"
                    },
                },
            },
        )
        expect(result).to_be(True)

    cl = hass.data[DATA_CLOUD]
    expect(cl.mode).to_equal(MODE_DEV)
    expect(cl.cognito_client_id).to_equal("test-cognito_client_id")
    expect(cl.user_pool_id).to_equal("test-user_pool_id")
    expect(cl.region).to_equal("test-region")
    expect(cl.relayer_server).to_equal("test-relayer-server")
    expect(cl.iot.ws_server_url).to_equal("wss://test-relayer-server/websocket")
    expect(cl.acme_server).to_equal("test-acme-server")
    expect(cl.api_server).to_equal("test-api-server")
    expect(cl.remotestate_server).to_equal("test-remotestate-server")
    expect(cl.service_discovery._action_overrides["lorem_ipsum"]).to_equal(
        "https://lorem.ipsum/test-url"
    )


@test
async def setup_existing_cloud_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test setup with API push default data."""
    user = await hass.auth.async_create_system_user("Cloud test")
    hass_storage[STORAGE_KEY] = {"version": 1, "data": {"cloud_user": user.id}}
    with patch("hass_nabucasa.Cloud.initialize"):
        result = await async_setup_component(
            hass,
            "cloud",
            {
                "http": {},
                "cloud": {
                    CONF_MODE: MODE_DEV,
                    "cognito_client_id": "test-cognito_client_id",
                    "user_pool_id": "test-user_pool_id",
                    "region": "test-region",
                    "relayer_server": "test-relayer-serer",
                    "api_server": "test-api-server",
                },
            },
        )
        expect(result).to_be(True)

    expect(hass_storage[STORAGE_KEY]["data"]["cloud_user"]).to_equal(user.id)


@test.skip("requires mock_cloud_fixture (full hass_nabucasa.Cloud mock)")
async def remote_services() -> None:
    """Stub for test_remote_services."""


@test.skip("requires mock_cloud_fixture (full hass_nabucasa.Cloud mock)")
async def shutdown_event() -> None:
    """Stub for test_shutdown_event."""


@test.skip("requires mock_cloud_fixture (full hass_nabucasa.Cloud mock)")
async def on_connect() -> None:
    """Stub for test_on_connect."""


@test.skip("requires mock_cloud_fixture (full hass_nabucasa.Cloud mock)")
async def remote_ui_url() -> None:
    """Stub for test_remote_ui_url."""


@test.skip("requires cloud + set_cloud_prefs fixtures (cloud mock chain)")
async def async_get_or_create_cloudhook() -> None:
    """Stub for test_async_get_or_create_cloudhook."""


@test.skip("requires cloud fixture (full hass_nabucasa.Cloud mock)")
async def cloud_logout() -> None:
    """Stub for test_cloud_logout."""


@test.skip("requires cloud + set_cloud_prefs fixtures (cloud mock chain)")
async def async_listen_cloudhook_change() -> None:
    """Stub for test_async_listen_cloudhook_change."""


@test.skip("requires cloud + set_cloud_prefs fixtures (cloud mock chain)")
async def async_listen_cloudhook_change_cloud_setup_later() -> None:
    """Stub for test_async_listen_cloudhook_change_cloud_setup_later."""
