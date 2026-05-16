"""Test Websocket API http module."""

import asyncio
from datetime import timedelta
import logging
from typing import Any, cast
from unittest.mock import patch

from aiohttp import ServerDisconnectedError, WSMsgType, web
from tryke import Depends, expect, fixture, test

from homeassistant.components.websocket_api import (
    async_register_command,
    const,
    http,
    websocket_command,
)
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.core import HomeAssistant, callback
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow

from ._fixtures import websocket_client as websocket_client_fx

from tests.common import async_call_logger_set_level, async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
    hass as hass_fixture,
    hass_client as hass_client_fx,
    hass_ws_client as hass_ws_client_fx,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import (
    ClientSessionGenerator,
    MockHAClientWebSocket,
    WebSocketGenerator,
)


@fixture
def _trigger_executor() -> int:
    return 0


@test
async def pending_msg_overflow(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test pending messages overflows."""
    with patch("homeassistant.components.websocket_api.http.MAX_PENDING_MSG", 1):
        for idx in range(10):
            await websocket_client.send_json({"id": idx + 1, "type": "ping"})
        msg = await websocket_client.receive()
        expect(msg.type is WSMsgType.CLOSE).to_be(True)


@test
async def cleanup_on_cancellation(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test cleanup on cancellation."""

    subscriptions = None

    @callback
    @websocket_command(
        {
            "type": "fake_subscription",
        }
    )
    def fake_subscription(
        hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
    ) -> None:
        nonlocal subscriptions
        msg_id: int = msg["id"]
        connection.subscriptions[msg_id] = callback(lambda: None)
        connection.send_result(msg_id)
        subscriptions = connection.subscriptions

    async_register_command(hass, fake_subscription)

    @callback
    @websocket_command(
        {
            "type": "subscription_that_raises_on_cancel",
        }
    )
    def subscription_that_raises_on_cancel(
        hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
    ) -> None:
        nonlocal subscriptions
        msg_id: int = msg["id"]

        @callback
        def _raise():
            raise ValueError

        connection.subscriptions[msg_id] = _raise
        connection.send_result(msg_id)
        subscriptions = connection.subscriptions

    async_register_command(hass, subscription_that_raises_on_cancel)

    @callback
    @websocket_command(
        {
            "type": "cancel_in_handler",
        }
    )
    def cancel_in_handler(
        hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
    ) -> None:
        raise asyncio.CancelledError

    async_register_command(hass, cancel_in_handler)

    await websocket_client.send_json({"id": 1, "type": "ping"})
    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal("pong")
    expect(subscriptions).to_be_falsy()
    await websocket_client.send_json({"id": 2, "type": "fake_subscription"})
    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(2)
    expect(msg["type"]).to_equal(const.TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    expect(len(subscriptions)).to_equal(2)
    await websocket_client.send_json(
        {"id": 3, "type": "subscription_that_raises_on_cancel"}
    )
    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(3)
    expect(msg["type"]).to_equal(const.TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    expect(len(subscriptions)).to_equal(3)
    await websocket_client.send_json({"id": 4, "type": "cancel_in_handler"})
    await hass.async_block_till_done()
    msg = await websocket_client.receive()
    expect(msg.type).to_equal(WSMsgType.close)
    expect(len(subscriptions)).to_equal(0)


@test
async def delayed_response_handler(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test a handler that responds after a connection has already been closed."""

    subscriptions = None

    @callback
    @websocket_command(
        {
            "type": "late_responder",
        }
    )
    def async_late_responder(
        hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
    ) -> None:
        msg_id: int = msg["id"]
        nonlocal subscriptions
        subscriptions = connection.subscriptions
        connection.subscriptions[msg_id] = lambda: None
        connection.send_result(msg_id)

        async def _async_late_send_message():
            await asyncio.sleep(0.05)
            connection.send_event(msg_id, {"event": "any"})

        hass.async_create_task(_async_late_send_message())

    async_register_command(hass, async_late_responder)

    await websocket_client.send_json({"id": 1, "type": "ping"})
    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal("pong")
    expect(subscriptions).to_be_falsy()
    await websocket_client.send_json({"id": 2, "type": "late_responder"})
    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(2)
    expect(msg["type"]).to_equal("result")
    expect(len(subscriptions)).to_equal(2)
    expect(await websocket_client.close()).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(subscriptions)).to_equal(0)

    expect("Tried to send message" in caplog.text).to_be(True)
    expect("on closed connection" in caplog.text).to_be(True)


@test
async def ensure_disconnect_invalid_json(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test we get disconnected when sending invalid JSON."""
    await websocket_client.send_json({"id": 1, "type": "ping"})
    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal("pong")
    await websocket_client.send_str("[--INVALID-JSON--]")
    msg = await websocket_client.receive()
    expect(msg.type).to_equal(WSMsgType.CLOSE)


@test
async def ensure_disconnect_invalid_binary(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test we get disconnected when sending invalid bytes."""
    await websocket_client.send_json({"id": 1, "type": "ping"})
    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal("pong")
    await websocket_client.send_bytes(b"")
    msg = await websocket_client.receive()
    expect(msg.type).to_equal(WSMsgType.CLOSE)


@test
async def pending_msg_peak(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test pending msg overflow command."""
    with patch("homeassistant.components.websocket_api.http.PENDING_MSG_PEAK", 5):
        orig_handler = http.WebSocketHandler
        setup_instance: http.WebSocketHandler | None = None

        def instantiate_handler(*args):
            nonlocal setup_instance
            setup_instance = orig_handler(*args)
            return setup_instance

        with patch(
            "homeassistant.components.websocket_api.http.WebSocketHandler",
            instantiate_handler,
        ):
            websocket_client = await hass_ws_client()

        instance: http.WebSocketHandler = cast(http.WebSocketHandler, setup_instance)

        for _ in range(20):
            instance._send_message({"overload": "message"})

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=const.PENDING_MSG_PEAK_TIME + 1)
        )

        msg = await websocket_client.receive()
        expect(msg.type is WSMsgType.CLOSE).to_be(True)
        expect("Client unable to keep up with pending messages" in caplog.text).to_be(
            True
        )
        expect("Stayed over 5 for 10 seconds" in caplog.text).to_be(True)
        expect("overload" in caplog.text).to_be(True)


@test
async def pending_msg_peak_recovery(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test pending msg nears the peak but recovers."""
    with patch("homeassistant.components.websocket_api.http.PENDING_MSG_PEAK", 5):
        orig_handler = http.WebSocketHandler
        setup_instance: http.WebSocketHandler | None = None

        def instantiate_handler(*args):
            nonlocal setup_instance
            setup_instance = orig_handler(*args)
            return setup_instance

        with patch(
            "homeassistant.components.websocket_api.http.WebSocketHandler",
            instantiate_handler,
        ):
            websocket_client = await hass_ws_client()

        instance: http.WebSocketHandler = cast(http.WebSocketHandler, setup_instance)

        for _ in range(10):
            instance._send_message({})

        for _ in range(10):
            msg = await websocket_client.receive()
            expect(msg.type).to_equal(WSMsgType.TEXT)

        instance._send_message({})
        msg = await websocket_client.receive()
        expect(msg.type).to_equal(WSMsgType.TEXT)

        instance._send_message({})
        instance._handle_task.cancel()

        msg = await websocket_client.receive()
        expect(msg.type is WSMsgType.CLOSE).to_be(True)
        expect("Client unable to keep up with pending messages" in caplog.text).to_be(
            False
        )


@test
async def pending_msg_peak_but_does_not_overflow(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test pending msg hits the low peak but recovers and does not overflow."""
    with patch("homeassistant.components.websocket_api.http.PENDING_MSG_PEAK", 5):
        orig_handler = http.WebSocketHandler
        setup_instance: http.WebSocketHandler | None = None

        def instantiate_handler(*args):
            nonlocal setup_instance
            setup_instance = orig_handler(*args)
            return setup_instance

        with patch(
            "homeassistant.components.websocket_api.http.WebSocketHandler",
            instantiate_handler,
        ):
            websocket_client = await hass_ws_client()

        instance: http.WebSocketHandler = cast(http.WebSocketHandler, setup_instance)

        for _ in range(5):
            instance._message_queue.append(None)

        instance._send_message({})

        instance._message_queue.clear()

        instance._send_message({})

        async_fire_time_changed(
            hass, utcnow() + timedelta(seconds=const.PENDING_MSG_PEAK_TIME + 1)
        )

        msg = await websocket_client.receive()
        expect(msg.type).to_equal(WSMsgType.TEXT)

        expect("Client unable to keep up with pending messages" in caplog.text).to_be(
            False
        )


@test
async def non_json_message(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test trying to serialize non JSON objects."""
    bad_data = object()
    hass.states.async_set("test_domain.entity", "testing", {"bad": bad_data})
    await websocket_client.send_json({"id": 5, "type": "get_states"})

    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(5)
    expect(msg["type"]).to_equal(const.TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"]).to_equal([])
    expect("Unable to serialize to JSON. Bad data found" in caplog.text).to_be(True)
    expect("State: test_domain.entity" in caplog.text).to_be(True)
    expect("bad=<object" in caplog.text).to_be(True)


@test
async def prepare_fail_timeout(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test failing to prepare due to timeout."""
    with patch(
        "homeassistant.components.websocket_api.http.web.WebSocketResponse.prepare",
        side_effect=(TimeoutError, web.WebSocketResponse.prepare),
    ):
        async with expect_raises_async(ServerDisconnectedError):
            await hass_ws_client(hass)

    expect("Timeout preparing request" in caplog.text).to_be(True)


@test
async def prepare_fail_connection_reset(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test failing to prepare due to connection reset."""
    with patch(
        "homeassistant.components.websocket_api.http.web.WebSocketResponse.prepare",
        side_effect=(ConnectionResetError, web.WebSocketResponse.prepare),
    ):
        async with expect_raises_async(ServerDisconnectedError):
            await hass_ws_client(hass)

    expect("Connection reset by peer while preparing WebSocket" in caplog.text).to_be(
        True
    )


@test
async def auth_timeout_logs_at_debug(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test auth timeout is logged at debug level not warning."""
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)

    client = await hass_client()

    with (
        caplog.at_level(logging.DEBUG, "homeassistant.components.websocket_api"),
        patch(
            "homeassistant.components.websocket_api.http.AUTH_MESSAGE_TIMEOUT", 0.001
        ),
    ):
        ws = await client.ws_connect("/api/websocket")
        await asyncio.sleep(0.1)
        await ws.close()
        await asyncio.sleep(0.1)

        debug_messages = [
            r.getMessage() for r in caplog.records if r.levelno == logging.DEBUG
        ]
        expect(
            any(
                "Disconnected during auth phase: Did not receive auth message" in msg
                for msg in debug_messages
            )
        ).to_be(True)

        warning_messages = [
            r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING
        ]
        for msg in warning_messages:
            expect("Did not receive auth message" not in msg).to_be(True)


@test
async def enable_coalesce(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test enabling coalesce."""
    websocket_client = await hass_ws_client(hass)

    await websocket_client.send_json(
        {
            "id": 1,
            "type": "supported_features",
            "features": {const.FEATURE_COALESCE_MESSAGES: 1},
        }
    )
    msg = await websocket_client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["success"]).to_be(True)
    send_tasks: list[asyncio.Future] = []
    ids: set[int] = set()
    start_id = 2

    for idx in range(10):
        id_ = idx + start_id
        ids.add(id_)
        send_tasks.append(websocket_client.send_json({"id": id_, "type": "ping"}))

    await asyncio.gather(*send_tasks)
    returned_ids: set[int] = set()
    while len(returned_ids) < 10:
        msg = await websocket_client.receive_json()
        msgs = msg if isinstance(msg, list) else [msg]
        for entry in msgs:
            expect(entry["type"]).to_equal("pong")
            returned_ids.add(entry["id"])

    expect(ids).to_equal(returned_ids)

    send_tasks_with_close: list[asyncio.Future] = []
    start_id = 12
    for idx in range(10):
        id_ = idx + start_id
        send_tasks_with_close.append(
            websocket_client.send_json({"id": id_, "type": "ping"})
        )

    send_tasks_with_close.append(websocket_client.close())
    send_tasks_with_close.append(websocket_client.send_json({"id": 50, "type": "ping"}))

    async with expect_raises_async(ConnectionResetError):
        await asyncio.gather(*send_tasks_with_close)


@test
async def binary_message(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test binary messages."""
    binary_payloads = {
        104: ([], asyncio.Future()),
        105: ([], asyncio.Future()),
    }

    @callback
    @websocket_command(
        {
            "type": "get_binary_message_handler",
        }
    )
    def get_binary_message_handler(
        hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
    ):
        unsub = None

        @callback
        def binary_message_handler(
            hass: HomeAssistant, connection: ActiveConnection, payload: bytes
        ):
            nonlocal unsub
            if msg["id"] == 103:
                raise ValueError("Boom")

            if payload:
                binary_payloads[msg["id"]][0].append(payload)
            else:
                binary_payloads[msg["id"]][1].set_result(
                    b"".join(binary_payloads[msg["id"]][0])
                )
                unsub()

        prefix, unsub = connection.async_register_binary_handler(binary_message_handler)

        connection.send_result(msg["id"], {"prefix": prefix})

    async_register_command(hass, get_binary_message_handler)

    for i in range(101, 106):
        await websocket_client.send_json(
            {"id": i, "type": "get_binary_message_handler"}
        )
        result = await websocket_client.receive_json()
        expect(result["id"]).to_equal(i)
        expect(result["type"]).to_equal(const.TYPE_RESULT)
        expect(result["success"]).to_be_truthy()
        expect(result["result"]["prefix"]).to_equal(i - 100)

    await websocket_client.send_bytes((0).to_bytes(1, "big") + b"test0")
    await websocket_client.send_bytes((3).to_bytes(1, "big") + b"test3")
    await websocket_client.send_bytes((3).to_bytes(1, "big") + b"test3")
    await websocket_client.send_bytes((10).to_bytes(1, "big") + b"test10")
    await websocket_client.send_bytes((4).to_bytes(1, "big") + b"test4")
    await websocket_client.send_bytes((4).to_bytes(1, "big") + b"")
    await websocket_client.send_bytes((5).to_bytes(1, "big") + b"test5")
    await websocket_client.send_bytes((5).to_bytes(1, "big") + b"test5-2")
    await websocket_client.send_bytes((5).to_bytes(1, "big") + b"")

    expect(await binary_payloads[104][1]).to_equal(b"test4")
    expect(await binary_payloads[105][1]).to_equal(b"test5test5-2")
    expect("Error handling binary message" in caplog.text).to_be(True)
    expect("Received binary message for non-existing handler 0" in caplog.text).to_be(
        True
    )
    expect("Received binary message for non-existing handler 3" in caplog.text).to_be(
        True
    )
    expect("Received binary message for non-existing handler 10" in caplog.text).to_be(
        True
    )


@test
async def enable_disable_debug_logging(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test enabling and disabling debug logging."""
    expect(await async_setup_component(hass, "logger", {"logger": {}})).to_be_truthy()
    async with async_call_logger_set_level(
        "homeassistant.components.websocket_api", "DEBUG", hass=hass, caplog=caplog
    ):
        await websocket_client.send_json({"id": 1, "type": "ping"})
        msg = await websocket_client.receive_json()
        expect(msg["id"]).to_equal(1)
        expect(msg["type"]).to_equal("pong")
        expect('Sending b\'{"id":1,"type":"pong"}\'' in caplog.text).to_be(True)
    async with async_call_logger_set_level(
        "homeassistant.components.websocket_api", "WARNING", hass=hass, caplog=caplog
    ):
        await websocket_client.send_json({"id": 2, "type": "ping"})
        msg = await websocket_client.receive_json()
        expect(msg["id"]).to_equal(2)
        expect(msg["type"]).to_equal("pong")
        expect('Sending b\'{"id":2,"type":"pong"}\'' not in caplog.text).to_be(True)
