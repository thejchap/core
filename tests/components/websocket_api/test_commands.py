"""Tests for WebSocket API commands."""

import asyncio
import logging
import math

import voluptuous as vol
from tryke import Depends, fixture, test

from homeassistant.components.websocket_api import const
from homeassistant.components.websocket_api.auth import (
    TYPE_AUTH,
    TYPE_AUTH_OK,
    TYPE_AUTH_REQUIRED,
)
from homeassistant.components.websocket_api.const import URL
from homeassistant.const import CONF_EXTERNAL_URL
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.setup import async_setup_component

from ._fixtures import websocket_client as websocket_client_fx

from tests.common import MockUser, async_mock_service
from tests.hass_fixtures import (
    ClientSessionGenerator,
    LogCapture,
    caplog as caplog_fx,
    hass as hass_fixture,
    hass_access_token as hass_access_token_fx,
    hass_admin_user as hass_admin_user_fx,
    hass_client_no_auth as hass_client_no_auth_fx,
)
from tests.typing import MockHAClientWebSocket


@fixture
def _trigger_executor() -> int:
    return 0


@test
async def fire_event(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test fire event command."""
    runs = []

    async def event_handler(event):
        runs.append(event)

    hass.bus.async_listen_once("event_type_test", event_handler)

    await websocket_client.send_json_auto_id(
        {
            "type": "fire_event",
            "event_type": "event_type_test",
            "event_data": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    assert len(runs) == 1
    assert runs[0].event_type == "event_type_test"
    assert runs[0].data == {"hello": "world"}


@test
async def fire_event_without_data(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test fire event command."""
    runs = []

    async def event_handler(event):
        runs.append(event)

    hass.bus.async_listen_once("event_type_test", event_handler)

    await websocket_client.send_json_auto_id(
        {
            "type": "fire_event",
            "event_type": "event_type_test",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    assert len(runs) == 1
    assert runs[0].event_type == "event_type_test"
    assert runs[0].data == {}


@test
async def call_service(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test call service command."""
    calls = async_mock_service(hass, "domain_test", "test_service")

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    assert len(calls) == 1
    call = calls[0]

    assert call.domain == "domain_test"
    assert call.service == "test_service"
    assert call.data == {"hello": "world"}
    assert call.context.as_dict() == msg["result"]["context"]


@test
async def return_response_error(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test return_response=True errors when service has no response."""
    hass.services.async_register(
        "domain_test", "test_service_with_no_response", lambda x: None
    )
    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service_with_no_response",
            "service_data": {"hello": "world"},
            "return_response": True,
        },
    )
    msg = await websocket_client.receive_json()

    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == "service_validation_error"


@test
async def call_service_target(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test call service command with target."""
    calls = async_mock_service(hass, "domain_test", "test_service")

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
            "target": {
                "entity_id": ["entity.one", "entity.two"],
                "device_id": "deviceid",
            },
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    assert len(calls) == 1
    call = calls[0]

    assert call.domain == "domain_test"
    assert call.service == "test_service"
    assert call.data == {
        "hello": "world",
        "entity_id": ["entity.one", "entity.two"],
        "device_id": ["deviceid"],
    }
    assert call.context.as_dict() == msg["result"]["context"]


@test
async def call_service_target_template(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test call service command with target does not allow template."""
    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
            "target": {
                "entity_id": "{{ 1 }}",
            },
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_INVALID_FORMAT


@test
async def call_service_not_found(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test call service command."""
    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_NOT_FOUND
    assert msg["error"]["message"] == "Service domain_test.test_service not found."
    assert msg["error"]["translation_placeholders"] == {
        "domain": "domain_test",
        "service": "test_service",
    }
    assert msg["error"]["translation_key"] == "service_not_found"
    assert msg["error"]["translation_domain"] == "homeassistant"


@test
async def call_service_child_not_found(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test not reporting not found errors if it's not the called service."""

    async def serv_handler(call):
        await hass.services.async_call("non", "existing")

    hass.services.async_register("domain_test", "test_service", serv_handler)

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_HOME_ASSISTANT_ERROR
    assert (
        msg["error"]["message"] == "Service non.existing called service "
        "domain_test.test_service which was not found."
    )
    assert msg["error"]["translation_placeholders"] == {
        "domain": "domain_test",
        "service": "test_service",
        "child_domain": "non",
        "child_service": "existing",
    }
    assert msg["error"]["translation_key"] == "child_service_not_found"
    assert msg["error"]["translation_domain"] == "websocket_api"


@test
async def call_service_schema_validation_error(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test call service command with invalid service data."""
    calls = []
    service_schema = vol.Schema(
        {
            vol.Required("message"): str,
        }
    )

    @callback
    def service_call(call):
        calls.append(call)

    hass.services.async_register(
        "domain_test",
        "test_service",
        service_call,
        schema=service_schema,
    )

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {},
        }
    )
    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_INVALID_FORMAT

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"extra_key": "not allowed"},
        }
    )
    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_INVALID_FORMAT

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"message": []},
        }
    )
    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_INVALID_FORMAT

    assert len(calls) == 0


@test
async def call_service_error(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fx),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test call service command with error."""
    caplog.set_level(logging.ERROR)

    @callback
    def ha_error_call(_):
        raise HomeAssistantError(
            "error_message",
            translation_domain="test",
            translation_key="custom_error",
            translation_placeholders={"option": "bla"},
        )

    hass.services.async_register("domain_test", "ha_error", ha_error_call)

    @callback
    def service_error_call(_):
        raise ServiceValidationError(
            "error_message",
            translation_domain="test",
            translation_key="custom_error",
            translation_placeholders={"option": "bla"},
        )

    hass.services.async_register("domain_test", "service_error", service_error_call)

    async def unknown_error_call(_):
        raise ValueError("value_error")

    hass.services.async_register("domain_test", "unknown_error", unknown_error_call)

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "ha_error",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"] is False
    assert msg["error"]["code"] == "home_assistant_error"
    assert msg["error"]["message"] == "error_message"
    assert msg["error"]["translation_placeholders"] == {"option": "bla"}
    assert msg["error"]["translation_key"] == "custom_error"
    assert msg["error"]["translation_domain"] == "test"
    assert "Traceback" not in caplog.text

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "service_error",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"] is False
    assert msg["error"]["code"] == "service_validation_error"
    assert msg["error"]["message"] == "Validation error: error_message"
    assert msg["error"]["translation_placeholders"] == {"option": "bla"}
    assert msg["error"]["translation_key"] == "custom_error"
    assert msg["error"]["translation_domain"] == "test"
    assert "Traceback" not in caplog.text

    await websocket_client.send_json_auto_id(
        {
            "type": "call_service",
            "domain": "domain_test",
            "service": "unknown_error",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"] is False
    assert msg["error"]["code"] == "unknown_error"
    assert msg["error"]["message"] == "value_error"
    assert "Traceback" in caplog.text


@test
async def subscribe_unsubscribe_events(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test subscribe/unsubscribe events command."""
    init_count = sum(hass.bus.async_listeners().values())

    await websocket_client.send_json_auto_id(
        {"type": "subscribe_events", "event_type": "test_event"}
    )

    msg = await websocket_client.receive_json()
    subscription = msg["id"]
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    assert sum(hass.bus.async_listeners().values()) == init_count + 1

    hass.bus.async_fire("ignore_event")
    hass.bus.async_fire("test_event", {"hello": "world"})
    hass.bus.async_fire("ignore_event")

    async with asyncio.timeout(3):
        msg = await websocket_client.receive_json()

    assert msg["id"] == subscription
    assert msg["type"] == "event"
    event = msg["event"]

    assert event["event_type"] == "test_event"
    assert event["data"] == {"hello": "world"}
    assert event["origin"] == "LOCAL"

    await websocket_client.send_json_auto_id(
        {"type": "unsubscribe_events", "subscription": subscription}
    )

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    assert sum(hass.bus.async_listeners().values()) == init_count


@test
async def get_states(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test get_states command."""
    hass.states.async_set("greeting.hello", "world")
    hass.states.async_set("greeting.bye", "universe")

    await websocket_client.send_json_auto_id({"type": "get_states"})

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    states = [state.as_dict() for state in hass.states.async_all()]

    assert msg["result"] == states


@test
async def get_config(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test get_config command."""
    await websocket_client.send_json_auto_id({"type": "get_config"})

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    result = msg["result"]
    ignore_order_keys = (
        "components",
        "allowlist_external_dirs",
        "whitelist_external_dirs",
        "allowlist_external_urls",
    )
    config = hass.config.as_dict()

    for key in ignore_order_keys:
        if key in result:
            result[key] = set(result[key])
            config[key] = set(config[key])

    assert result == config


@test
async def get_config_local_only(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test get_config command for a local only user."""
    hass_admin_user.local_only = True
    await websocket_client.send_json_auto_id({"type": "get_config"})

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    result = msg["result"]
    ignore_order_keys = (
        "components",
        "allowlist_external_dirs",
        "whitelist_external_dirs",
        "allowlist_external_urls",
    )
    config = hass.config.as_dict()

    for key in ignore_order_keys:
        if key in result:
            result[key] = set(result[key])
            config[key] = set(config[key])

    assert CONF_EXTERNAL_URL in config
    config.pop(CONF_EXTERNAL_URL)

    assert result == config


@test
async def ping(
    _exec: int = Depends(_trigger_executor),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test ping command."""
    await websocket_client.send_json_auto_id({"type": "ping"})

    msg = await websocket_client.receive_json()
    assert msg["type"] == "pong"


@test
async def call_service_context_with_user(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test that the user is set in the service call context."""
    assert await async_setup_component(hass, "websocket_api", {})

    calls = async_mock_service(hass, "domain_test", "test_service")
    client = await hass_client_no_auth()

    async with client.ws_connect(URL) as ws:
        auth_msg = await ws.receive_json()
        assert auth_msg["type"] == TYPE_AUTH_REQUIRED

        await ws.send_json({"type": TYPE_AUTH, "access_token": hass_access_token})

        auth_msg = await ws.receive_json()
        assert auth_msg["type"] == TYPE_AUTH_OK

        await ws.send_json(
            {
                "id": 5,
                "type": "call_service",
                "domain": "domain_test",
                "service": "test_service",
                "service_data": {"hello": "world"},
            }
        )

        msg = await ws.receive_json()
        assert msg["success"]

        refresh_token = hass.auth.async_validate_access_token(hass_access_token)

        assert len(calls) == 1
        call = calls[0]
        assert call.domain == "domain_test"
        assert call.service == "test_service"
        assert call.data == {"hello": "world"}
        assert call.context.user_id == refresh_token.user.id


@test
async def subscribe_requires_admin(
    _exec: int = Depends(_trigger_executor),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test subscribing events without being admin."""
    hass_admin_user.groups = []
    await websocket_client.send_json_auto_id(
        {"type": "subscribe_events", "event_type": "test_event"}
    )

    msg = await websocket_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_UNAUTHORIZED


@test
async def states_filters_visible(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test we only get entities that we're allowed to see."""
    hass_admin_user.groups = []
    hass_admin_user.mock_policy({"entities": {"entity_ids": {"test.entity": True}}})
    hass.states.async_set("test.entity", "hello")
    hass.states.async_set("test.not_visible_entity", "invisible")
    await websocket_client.send_json_auto_id({"type": "get_states"})

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    assert len(msg["result"]) == 1
    assert msg["result"][0]["entity_id"] == "test.entity"


@test
async def get_states_not_allows_nan(
    _exec: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    websocket_client: MockHAClientWebSocket = Depends(websocket_client_fx),
) -> None:
    """Test get_states command converts NaN to None."""
    hass.states.async_set("greeting.hello", "world")
    hass.states.async_set("greeting.bad", "data", {"hello": math.nan})
    hass.states.async_set("greeting.bye", "universe")

    await websocket_client.send_json_auto_id({"type": "get_states"})
    bad = dict(hass.states.get("greeting.bad").as_dict())
    bad["attributes"] = dict(bad["attributes"])
    bad["attributes"]["hello"] = None

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == [
        hass.states.get("greeting.hello").as_dict(),
        bad,
        hass.states.get("greeting.bye").as_dict(),
    ]
