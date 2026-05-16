"""Test auth of websocket API."""

from typing import Any
from unittest.mock import patch

import aiohttp
from aiohttp import WSMsgType, web
from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant.auth.providers.homeassistant import HassAuthProvider
from homeassistant.components.websocket_api.auth import (
    TYPE_AUTH,
    TYPE_AUTH_INVALID,
    TYPE_AUTH_OK,
    TYPE_AUTH_REQUIRED,
)
from homeassistant.components.websocket_api.const import (
    SIGNAL_WEBSOCKET_CONNECTED,
    SIGNAL_WEBSOCKET_DISCONNECTED,
    URL,
)
from homeassistant.const import HASSIO_USER_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.setup import async_setup_component

from ._fixtures import (
    no_auth_websocket_client as no_auth_websocket_client_fx,
    websocket_client as websocket_client_fx,
)

from tests.hass_fixtures import (
    ClientSessionGenerator,
    LogCapture,
    caplog as caplog_fx,
    hass as hass_fixture,
    hass_access_token as hass_access_token_fx,
    hass_client_no_auth as hass_client_no_auth_fx,
    local_auth as local_auth_fx,
)
from tests.test_util import mock_real_ip


@fixture
def _trigger_executor() -> int:
    return 0


@fixture
def track_connected(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, list[int]]:
    """Track connected and disconnected events."""
    connected_evt: list[int] = []

    @callback
    def track_connected():
        connected_evt.append(1)

    async_dispatcher_connect(hass, SIGNAL_WEBSOCKET_CONNECTED, track_connected)
    disconnected_evt: list[int] = []

    @callback
    def track_disconnected():
        disconnected_evt.append(1)

    async_dispatcher_connect(hass, SIGNAL_WEBSOCKET_DISCONNECTED, track_disconnected)

    return {"connected": connected_evt, "disconnected": disconnected_evt}


async def _do_auth_active_with_token(
    hass: HomeAssistant,
    no_auth_websocket_client: TestClient,
    hass_access_token: str,
) -> None:
    """Authenticate with a token (shared helper)."""
    await no_auth_websocket_client.send_json(
        {"type": TYPE_AUTH, "access_token": hass_access_token}
    )
    auth_msg = await no_auth_websocket_client.receive_json()

    expect(auth_msg["type"]).to_equal(TYPE_AUTH_OK)


async def _do_auth_via_msg_incorrect_pass(
    no_auth_websocket_client: TestClient,
) -> None:
    """Test authenticating with an incorrect password (shared helper)."""
    with patch(
        "homeassistant.components.websocket_api.auth.process_wrong_login",
    ) as mock_process_wrong_login:
        await no_auth_websocket_client.send_json(
            {"type": TYPE_AUTH, "api_password": "wrong"}
        )

        msg = await no_auth_websocket_client.receive_json()

    expect(mock_process_wrong_login.called).to_be(True)
    expect(msg["type"]).to_equal(TYPE_AUTH_INVALID)
    expect(msg["message"]).to_equal("Invalid access token or password")


@test
async def auth_events(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    no_auth_websocket_client: TestClient = Depends(no_auth_websocket_client_fx),
    local_auth: HassAuthProvider = Depends(local_auth_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
    track_connected: dict[str, list[int]] = Depends(track_connected),
) -> None:
    """Test authenticating."""
    await _do_auth_active_with_token(hass, no_auth_websocket_client, hass_access_token)

    expect(len(track_connected["connected"])).to_equal(1)
    expect(track_connected["disconnected"]).to_be_falsy()

    await no_auth_websocket_client.close()
    await hass.async_block_till_done()

    expect(len(track_connected["disconnected"])).to_equal(1)


@test
async def auth_via_msg_incorrect_pass(
    _exec: int = Depends(_trigger_executor),
    no_auth_websocket_client: TestClient = Depends(no_auth_websocket_client_fx),
) -> None:
    """Test authenticating."""
    await _do_auth_via_msg_incorrect_pass(no_auth_websocket_client)


@test
async def auth_events_incorrect_pass(
    _exec: int = Depends(_trigger_executor),
    no_auth_websocket_client: TestClient = Depends(no_auth_websocket_client_fx),
    track_connected: dict[str, list[int]] = Depends(track_connected),
) -> None:
    """Test authenticating."""
    await _do_auth_via_msg_incorrect_pass(no_auth_websocket_client)

    expect(track_connected["connected"]).to_be_falsy()
    expect(track_connected["disconnected"]).to_be_falsy()

    await no_auth_websocket_client.close()

    expect(track_connected["connected"]).to_be_falsy()
    expect(track_connected["disconnected"]).to_be_falsy()


@test
async def pre_auth_only_auth_allowed(
    _exec: int = Depends(_trigger_executor),
    no_auth_websocket_client: TestClient = Depends(no_auth_websocket_client_fx),
) -> None:
    """Verify that before authentication, only auth messages are allowed."""
    await no_auth_websocket_client.send_json(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
        }
    )

    msg = await no_auth_websocket_client.receive_json()

    expect(msg["type"]).to_equal(TYPE_AUTH_INVALID)
    expect(msg["message"].startswith("Auth message incorrectly formatted")).to_be(True)


@test
async def auth_active_with_token(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    no_auth_websocket_client: TestClient = Depends(no_auth_websocket_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test authenticating with a token."""
    await _do_auth_active_with_token(hass, no_auth_websocket_client, hass_access_token)


@test
async def auth_active_user_inactive(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test authenticating with a token."""
    refresh_token = hass.auth.async_validate_access_token(hass_access_token)
    refresh_token.user.is_active = False
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    client = await hass_client_no_auth()

    async with client.ws_connect(URL) as ws:
        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

        await ws.send_json({"type": TYPE_AUTH, "access_token": hass_access_token})

        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_INVALID)


@test
async def auth_local_only_user_rejected_remote(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test that a local-only user cannot authenticate from a remote IP."""
    refresh_token = hass.auth.async_validate_access_token(hass_access_token)
    refresh_token.user.local_only = True

    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    set_mock_ip = mock_real_ip(hass.http.app)
    set_mock_ip("198.51.100.1")

    client = await hass_client_no_auth()

    with patch(
        "homeassistant.components.websocket_api.auth.process_wrong_login",
    ) as mock_process_wrong_login:
        async with client.ws_connect(URL) as ws:
            auth_msg = await ws.receive_json()
            expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

            await ws.send_json({"type": TYPE_AUTH, "access_token": hass_access_token})

            auth_msg = await ws.receive_json()
            expect(auth_msg["type"]).to_equal(TYPE_AUTH_INVALID)
            expect(auth_msg["message"]).to_equal("User cannot authenticate remotely")

    expect(mock_process_wrong_login.called).to_be(True)


@test
async def auth_local_only_user_allowed_local(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test that a local-only user can authenticate from a local IP."""
    refresh_token = hass.auth.async_validate_access_token(hass_access_token)
    refresh_token.user.local_only = True

    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    set_mock_ip = mock_real_ip(hass.http.app)
    set_mock_ip("192.168.1.100")

    client = await hass_client_no_auth()

    async with client.ws_connect(URL) as ws:
        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

        await ws.send_json({"type": TYPE_AUTH, "access_token": hass_access_token})

        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_OK)


@test
async def auth_active_with_password_not_allow(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test authenticating with a token."""
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    client = await hass_client_no_auth()

    async with client.ws_connect(URL) as ws:
        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

        await ws.send_json({"type": TYPE_AUTH, "api_password": "some-password"})

        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_INVALID)


@test
async def auth_legacy_support_with_password(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    local_auth: HassAuthProvider = Depends(local_auth_fx),
) -> None:
    """Test authenticating with a token."""
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    client = await hass_client_no_auth()

    async with client.ws_connect(URL) as ws:
        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

        await ws.send_json({"type": TYPE_AUTH, "api_password": "some-password"})

        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_INVALID)


@test
async def auth_with_invalid_token(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test authenticating with a token."""
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    client = await hass_client_no_auth()

    async with client.ws_connect(URL) as ws:
        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

        await ws.send_json({"type": TYPE_AUTH, "access_token": "incorrect"})

        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_INVALID)


@test
async def auth_close_after_revoke(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: Any = Depends(websocket_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test that a websocket is closed after the refresh token is revoked."""
    expect(websocket_client.closed).to_be(False)

    refresh_token = hass.auth.async_validate_access_token(hass_access_token)
    hass.auth.async_remove_refresh_token(refresh_token)

    msg = await websocket_client.receive()
    expect(msg.type is aiohttp.WSMsgType.CLOSE).to_be(True)
    expect(websocket_client.closed).to_be(True)


@test
async def auth_sending_invalid_json_disconnects(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test sending invalid json during auth."""
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    client = await hass_client_no_auth()

    async with client.ws_connect(URL) as ws:
        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

        await ws.send_str("[--INVALID--JSON--]")

        auth_msg = await ws.receive()
        expect(auth_msg.type).to_equal(WSMsgType.close)


@test
async def auth_sending_binary_disconnects(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test sending bytes during auth."""
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    client = await hass_client_no_auth()

    async with client.ws_connect(URL) as ws:
        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

        await ws.send_bytes(b"[INVALID]")

        auth_msg = await ws.receive()
        expect(auth_msg.type is WSMsgType.CLOSE).to_be(True)


@test
async def auth_close_disconnects(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test closing during auth."""
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    client = await hass_client_no_auth()

    async with client.ws_connect(URL) as ws:
        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

        await ws.close()

        auth_msg = await ws.receive()
        expect(auth_msg.type is WSMsgType.CLOSED).to_be(True)


@test
async def auth_error_disconnects(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test error during auth."""
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    client = await hass_client_no_auth()
    ws_response = web.WebSocketResponse()

    with patch(
        "homeassistant.components.websocket_api.http.web.WebSocketResponse",
        return_value=ws_response,
    ):
        async with client.ws_connect(URL) as ws:
            auth_msg = await ws.receive_json()
            expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

            ws_response._reader.feed_data(
                aiohttp.WSMessage(
                    type=WSMsgType.ERROR, data=Exception("explode"), extra=None
                ),
                0,
            )

            auth_msg = await ws.receive()
            expect(auth_msg.type is WSMsgType.CLOSE).to_be(True)

    expect("Received error message during auth phase: explode" in caplog.text).to_be(
        True
    )


@test
async def auth_sending_unknown_type_disconnects(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test sending unknown type during auth."""
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    client = await hass_client_no_auth()

    async with client.ws_connect(URL) as ws:
        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

        await ws._writer.send_frame(b"1" * 130, 0x30)
        auth_msg = await ws.receive()
        expect(auth_msg.type).to_equal(WSMsgType.close)


@test
async def error_right_after_auth_disconnects(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test error right after auth."""
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    client = await hass_client_no_auth()
    ws_response = web.WebSocketResponse()

    with patch(
        "homeassistant.components.websocket_api.http.web.WebSocketResponse",
        return_value=ws_response,
    ):
        async with client.ws_connect(URL) as ws:
            auth_msg = await ws.receive_json()
            expect(auth_msg["type"]).to_equal(TYPE_AUTH_REQUIRED)

            await ws.send_json({"type": TYPE_AUTH, "access_token": hass_access_token})
            auth_msg = await ws.receive_json()
            expect(auth_msg["type"]).to_equal(TYPE_AUTH_OK)

            ws_response._reader.feed_data(
                aiohttp.WSMessage(
                    type=WSMsgType.ERROR, data=Exception("explode"), extra=None
                ),
                0,
            )

            close_error_msg = await ws.receive()
            expect(close_error_msg.type is WSMsgType.CLOSE).to_be(True)

    expect(
        "Received error message during command phase: explode" in caplog.text
    ).to_be(True)


@test
async def unix_socket_auth_bypass(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
) -> None:
    """Test that Unix socket connections skip websocket auth phase."""
    await hass.auth.async_create_system_user(
        HASSIO_USER_NAME, group_ids=["system-admin"]
    )

    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    await hass.async_block_till_done()

    client = await hass_client_no_auth()

    with (
        patch(
            "homeassistant.components.http.ban.is_supervisor_unix_socket_request",
            return_value=True,
        ),
        patch(
            "homeassistant.components.http.auth.is_supervisor_unix_socket_request",
            return_value=True,
        ),
        patch(
            "homeassistant.components.websocket_api.http.is_supervisor_unix_socket_request",
            return_value=True,
        ),
    ):
        async with client.ws_connect(URL) as ws:
            auth_msg = await ws.receive_json()
            expect(auth_msg["type"]).to_equal(TYPE_AUTH_OK)

            await ws.send_json({"id": 1, "type": "ping"})
            pong_msg = await ws.receive_json()
            expect(pong_msg["type"]).to_equal("pong")
            expect(pong_msg["id"]).to_equal(1)
