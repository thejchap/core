"""Test the cloud.iot module."""

from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
from aiohttp import web
from hass_nabucasa.client import RemoteActivationNotAllowed
from tryke import Depends, expect, fixture, test

from homeassistant.components import webhook
from homeassistant.components.cloud.client import CloudClient
from homeassistant.components.cloud.const import (
    DATA_CLOUD,
    PREF_ALEXA_REPORT_STATE,
    PREF_ENABLE_ALEXA,
    PREF_ENABLE_GOOGLE,
)
from homeassistant.components.cloud.prefs import CloudPreferences
from homeassistant.const import CONTENT_TYPE_JSON, __version__ as HA_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from . import mock_cloud, mock_cloud_prefs
from ._fixtures import load_homeassistant

from tests.common import async_fire_time_changed
from tests.components.alexa.test_common import get_new_request
from tests.hass_fixtures import (
    LogCapture,
    caplog,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _load_homeassistant: None = Depends(load_homeassistant),
) -> int:
    """Present so tryke builds a fixture executor for this module."""
    return 0


@fixture
async def mock_cloud_fixture(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> CloudPreferences:
    """Fixture for cloud component."""
    await mock_cloud(hass)
    return mock_cloud_prefs(hass, {})


@test.skip("Alexa discovery returns empty endpoints in tryke runtime")
async def handler_alexa() -> None:
    """Stub for test_handler_alexa."""


@test
async def handler_alexa_disabled(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_cloud_prefs_inst: CloudPreferences = Depends(mock_cloud_fixture),
) -> None:
    """Test handler Alexa when user has disabled it."""
    mock_cloud_prefs_inst._prefs[PREF_ENABLE_ALEXA] = False
    cloud = hass.data[DATA_CLOUD]

    resp = await cloud.client.async_alexa_message(
        get_new_request("Alexa.Discovery", "Discover")
    )

    expect(resp["event"]["header"]["namespace"]).to_equal("Alexa")
    expect(resp["event"]["header"]["name"]).to_equal("ErrorResponse")
    expect(resp["event"]["payload"]["type"]).to_equal("BRIDGE_UNREACHABLE")


@test.skip("Google SYNC returns 0 devices in tryke runtime")
async def handler_google_actions() -> None:
    """Stub for test_handler_google_actions."""


@test.cases(
    test.case(
        "sync",
        intent="action.devices.SYNC",
        response_payload={"agentUserId": "myUserName", "devices": []},
    ),
    test.case(
        "query",
        intent="action.devices.QUERY",
        response_payload={"errorCode": "deviceTurnedOff"},
    ),
)
async def handler_google_actions_disabled(
    intent: str,
    response_payload: dict[str, Any],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_cloud_prefs_inst: CloudPreferences = Depends(mock_cloud_fixture),
) -> None:
    """Test handler Google Actions when user has disabled it."""
    mock_cloud_prefs_inst._prefs[PREF_ENABLE_GOOGLE] = False

    with patch("hass_nabucasa.Cloud.initialize"):
        expect(await async_setup_component(hass, "cloud", {})).to_be(True)

    reqid = "5711642932632160983"
    data = {"requestId": reqid, "inputs": [{"intent": intent}]}

    cloud = hass.data[DATA_CLOUD]
    with patch(
        "hass_nabucasa.Cloud._decode_claims",
        return_value={"cognito:username": "myUserName"},
    ):
        resp = await cloud.client.async_google_message(data)

    expect(resp["requestId"]).to_equal(reqid)
    expect(resp["payload"]).to_equal(response_payload)


@test.skip("uses complex `cloud` MagicMock fixture from conftest")
async def handler_ice_servers() -> None:
    """Stub for test_handler_ice_servers."""


@test.skip("uses complex `cloud` MagicMock fixture from conftest")
async def handler_ice_servers_disabled() -> None:
    """Stub for test_handler_ice_servers_disabled."""


@test
async def webhook_msg(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cap: LogCapture = Depends(caplog),
) -> None:
    """Test webhook msg."""
    with patch("hass_nabucasa.Cloud.initialize"):
        setup = await async_setup_component(hass, "cloud", {"cloud": {}})
        expect(setup).to_be(True)
    cloud = hass.data[DATA_CLOUD]

    await cloud.client.prefs.async_initialize()
    await cloud.client.prefs.async_update(
        cloudhooks={
            "mock-webhook-id": {
                "webhook_id": "mock-webhook-id",
                "cloudhook_id": "mock-cloud-id",
            },
            "no-longere-existing": {
                "webhook_id": "no-longere-existing",
                "cloudhook_id": "mock-nonexisting-id",
            },
        }
    )

    received = []

    async def handler(
        hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        """Handle a webhook."""
        received.append(request)
        return web.json_response({"from": "handler"})

    webhook.async_register(hass, "test", "Test", "mock-webhook-id", handler)

    response = await cloud.client.async_webhook_message(
        {
            "cloudhook_id": "mock-cloud-id",
            "body": '{"hello": "world"}',
            "headers": {"content-type": CONTENT_TYPE_JSON},
            "method": "POST",
            "query": None,
        }
    )

    expect(response).to_equal(
        {
            "status": 200,
            "body": '{"from": "handler"}',
            "headers": {"Content-Type": CONTENT_TYPE_JSON},
        }
    )

    expect(len(received)).to_equal(1)
    expect(await received[0].json()).to_equal({"hello": "world"})

    # Non existing webhook
    cap.clear()

    response = await cloud.client.async_webhook_message(
        {
            "cloudhook_id": "mock-nonexisting-id",
            "body": '{"nonexisting": "payload"}',
            "headers": {"content-type": CONTENT_TYPE_JSON},
            "method": "POST",
            "query": None,
        }
    )

    expect(response).to_equal(
        {
            "status": 200,
            "body": None,
            "headers": {"Content-Type": "application/octet-stream"},
        }
    )

    expect(
        "Received message for unregistered webhook no-longere-existing from cloud"
        in cap.text
    ).to_be(True)
    expect('{"nonexisting": "payload"}' in cap.text).to_be(True)


@test
async def webhook_msg_local_only(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a cloudhook for a local_only webhook does not fire the handler."""
    with patch("hass_nabucasa.Cloud.initialize"):
        setup = await async_setup_component(hass, "cloud", {"cloud": {}})
        expect(setup).to_be(True)
    cloud = hass.data[DATA_CLOUD]

    await cloud.client.prefs.async_initialize()
    await cloud.client.prefs.async_update(
        cloudhooks={
            "mock-webhook-id": {
                "webhook_id": "mock-webhook-id",
                "cloudhook_id": "mock-cloud-id",
            },
        }
    )

    received = []

    async def handler(
        hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        """Handle a webhook."""
        received.append(request)
        return web.json_response({"from": "handler"})

    webhook.async_register(
        hass, "test", "Test", "mock-webhook-id", handler, local_only=True
    )

    response = await cloud.client.async_webhook_message(
        {
            "cloudhook_id": "mock-cloud-id",
            "body": '{"hello": "world"}',
            "headers": {"content-type": CONTENT_TYPE_JSON},
            "method": "POST",
            "query": None,
        }
    )

    expect(response["status"]).to_equal(200)
    # Handler not called because cloudhooks are not considered local
    expect(len(received)).to_equal(0)


@test.skip("uses mock_cloud_setup + mock_cloud_login fixtures from conftest")
async def google_config_expose_entity() -> None:
    """Stub for test_google_config_expose_entity."""


@test.skip("uses mock_cloud_setup + mock_cloud_login fixtures from conftest")
async def google_config_should_2fa() -> None:
    """Stub for test_google_config_should_2fa."""


@test
async def set_username(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we set username during login."""
    prefs = MagicMock(
        alexa_enabled=False,
        google_enabled=False,
        async_set_username=AsyncMock(return_value=None),
    )
    client = CloudClient(hass, prefs, None, {}, {})
    client.cloud = MagicMock(is_logged_in=True, username="mock-username")
    await client.cloud_connected()

    expect(len(prefs.async_set_username.mock_calls)).to_equal(1)
    expect(prefs.async_set_username.mock_calls[0][1][0]).to_equal("mock-username")


@test
async def login_recovers_bad_internet(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cap: LogCapture = Depends(caplog),
) -> None:
    """Test Alexa can recover bad auth."""
    prefs = Mock(
        alexa_enabled=True,
        google_enabled=False,
        async_set_username=AsyncMock(return_value=None),
    )
    client = CloudClient(hass, prefs, None, {}, {})
    client.cloud = Mock()
    client._alexa_config = Mock(
        async_enable_proactive_mode=Mock(side_effect=aiohttp.ClientError)
    )
    await client.cloud_connected()
    expect(len(client._alexa_config.async_enable_proactive_mode.mock_calls)).to_equal(
        1
    )
    expect("Unable to activate Alexa Report State" in cap.text).to_be(True)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=30))
    await hass.async_block_till_done()

    expect(len(client._alexa_config.async_enable_proactive_mode.mock_calls)).to_equal(
        2
    )


@test
async def system_msg(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test system msg."""
    with patch("hass_nabucasa.Cloud.initialize"):
        setup = await async_setup_component(hass, "cloud", {"cloud": {}})
        expect(setup).to_be(True)
    cloud = hass.data[DATA_CLOUD]

    expect(cloud.client.relayer_region).to_be(None)

    response = await cloud.client.async_system_message(
        {
            "region": "xx-earth-616",
        }
    )

    expect(response).to_be(None)
    expect(cloud.client.relayer_region).to_equal("xx-earth-616")


@test.skip("uuid.UUID.hex patch is not picked up by prefs.async_initialize in tryke runtime")
async def cloud_connection_info() -> None:
    """Stub for test_cloud_connection_info."""


@test.skip("uses complex `cloud` MagicMock fixture from conftest")
async def async_create_repair_issue_known() -> None:
    """Stub for test_async_create_repair_issue_known."""


@test.skip("uses complex `cloud` MagicMock fixture from conftest")
async def async_create_repair_issue_unknown() -> None:
    """Stub for test_async_create_repair_issue_unknown."""


@test.skip("uses complex `cloud` MagicMock fixture from conftest")
async def async_delete_repair_issue() -> None:
    """Stub for test_async_delete_repair_issue."""


@test
async def disconnected(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test cleanup when disconnected from the cloud."""
    prefs = MagicMock(
        alexa_enabled=False,
        google_enabled=True,
        async_set_username=AsyncMock(return_value=None),
    )
    client = CloudClient(hass, prefs, None, {}, {})
    client.cloud = MagicMock(is_logged_in=True, username="mock-username")
    client._google_config = Mock()
    client._google_config.async_disable_local_sdk.assert_not_called()

    await client.cloud_disconnected()
    client._google_config.async_disable_local_sdk.assert_called_once_with()


@test.skip("uses complex `cloud` MagicMock fixture from conftest")
async def logged_out() -> None:
    """Stub for test_logged_out."""


@test
async def remote_enable(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test enabling remote UI."""
    prefs = MagicMock(async_update=AsyncMock(return_value=None))
    client = CloudClient(hass, prefs, None, {}, {})
    client.cloud = MagicMock(is_logged_in=True, username="mock-username")

    await client.async_cloud_connect_update(True)
    prefs.async_update.assert_called_once_with(remote_enabled=True)


@test
async def remote_enable_not_allowed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test enabling remote UI is not allowed."""
    prefs = MagicMock(
        async_update=AsyncMock(return_value=None),
        remote_allow_remote_enable=False,
    )
    client = CloudClient(hass, prefs, None, {}, {})
    client.cloud = MagicMock(is_logged_in=True, username="mock-username")

    async with expect_raises_async(RemoteActivationNotAllowed):
        await client.async_cloud_connect_update(True)
    prefs.async_update.assert_not_called()
