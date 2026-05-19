"""The tests for the Home Assistant API component."""

import asyncio
from http import HTTPStatus
import json
from typing import Any
from unittest.mock import patch

from aiohttp import ServerDisconnectedError
from aiohttp.test_utils import TestClient
from tryke import Depends, fixture, test
import voluptuous as vol

from homeassistant import const, core as ha
from homeassistant.auth.models import Credentials
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import CLIENT_ID, MockUser, async_mock_service
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fx,
    hass_access_token as hass_access_token_fx,
    hass_admin_user as hass_admin_user_fx,
    hass_client as hass_client_fx,
    hass_read_only_user as hass_read_only_user_fx,
)


@fixture
def _trigger_executor() -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@fixture
async def mock_api_client(
    hass: HomeAssistant = Depends(hass_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> TestClient:
    """Start the Home Assistant HTTP component and return admin API client."""
    await async_setup_component(hass, "api", {})
    return await hass_client()


@test
async def api_list_state_entities(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if the debug interface allows us to list state entities."""
    hass.states.async_set("test.entity", "hello")
    resp = await mock_api_client.get(const.URL_API_STATES)
    assert resp.status == HTTPStatus.OK
    json_data = await resp.json()

    remote_data = [ha.State.from_dict(item).as_dict() for item in json_data]
    local_data = [state.as_dict() for state in hass.states.async_all()]
    assert remote_data == local_data


@test
async def api_get_state(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if the debug interface allows us to get a state."""
    hass.states.async_set("hello.world", "nice", {"attr": 1})
    resp = await mock_api_client.get("/api/states/hello.world")
    assert resp.status == HTTPStatus.OK
    json_data = await resp.json()

    data = ha.State.from_dict(json_data)

    state = hass.states.get("hello.world")

    assert data.state == state.state
    assert data.last_changed == state.last_changed
    assert data.attributes == state.attributes


@test
async def api_get_non_existing_state(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if the debug interface allows us to get a state."""
    resp = await mock_api_client.get("/api/states/does_not_exist")
    assert resp.status == HTTPStatus.NOT_FOUND


@test
async def api_state_change(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if we can change the state of an entity that exists."""
    hass.states.async_set("test.test", "not_to_be_set")

    await mock_api_client.post(
        "/api/states/test.test", json={"state": "debug_state_change2"}
    )

    assert hass.states.get("test.test").state == "debug_state_change2"


@test
async def api_state_change_of_non_existing_entity(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if changing a state of a non existing entity is possible."""
    new_state = "debug_state_change"

    resp = await mock_api_client.post(
        "/api/states/test_entity.that_does_not_exist", json={"state": new_state}
    )

    assert resp.status == HTTPStatus.CREATED

    assert hass.states.get("test_entity.that_does_not_exist").state == new_state


@test
async def api_state_change_with_bad_entity_id(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if API sends appropriate error if we omit state."""
    resp = await mock_api_client.post(
        "/api/states/bad.entity.id", json={"state": "new_state"}
    )

    assert resp.status == HTTPStatus.BAD_REQUEST


@test
async def api_state_change_with_bad_state(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if API sends appropriate error if we omit state."""
    resp = await mock_api_client.post(
        "/api/states/test.test", json={"state": "x" * 256}
    )

    assert resp.status == HTTPStatus.BAD_REQUEST


@test
async def api_state_change_with_bad_data(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if API sends appropriate error if we omit state."""
    resp = await mock_api_client.post(
        "/api/states/test_entity.that_does_not_exist", json={}
    )

    assert resp.status == HTTPStatus.BAD_REQUEST


@test
async def api_state_change_with_invalid_json(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if API sends appropriate error if send invalid json data."""
    resp = await mock_api_client.post("/api/states/test.test", data="{,}")

    assert resp.status == HTTPStatus.BAD_REQUEST
    assert await resp.json() == {"message": "Invalid JSON specified."}


@test
async def api_state_change_with_string_body(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if API sends appropriate error if we send a string instead of a JSON object."""
    resp = await mock_api_client.post(
        "/api/states/bad.entity.id", json='"{"state": "new_state"}"'
    )

    assert resp.status == HTTPStatus.BAD_REQUEST
    assert await resp.json() == {"message": "State data should be a JSON object."}


@test
async def api_state_change_to_zero_value(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if changing a state to a zero value is possible."""
    resp = await mock_api_client.post(
        "/api/states/test_entity.with_zero_state", json={"state": 0}
    )

    assert resp.status == HTTPStatus.CREATED

    resp = await mock_api_client.post(
        "/api/states/test_entity.with_zero_state", json={"state": 0.0}
    )

    assert resp.status == HTTPStatus.OK


@test
async def api_state_change_push(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if we can push a change the state of an entity."""
    hass.states.async_set("test.test", "not_to_be_set")

    events = []

    @ha.callback
    def event_listener(event):
        """Track events."""
        events.append(event)

    hass.bus.async_listen(const.EVENT_STATE_CHANGED, event_listener)

    await mock_api_client.post("/api/states/test.test", json={"state": "not_to_be_set"})
    await hass.async_block_till_done()
    assert len(events) == 0

    await mock_api_client.post(
        "/api/states/test.test", json={"state": "not_to_be_set", "force_update": True}
    )
    await hass.async_block_till_done()
    assert len(events) == 1


@test
async def api_fire_event_with_no_data(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if the API allows us to fire an event."""
    test_value = []

    @ha.callback
    def listener(event):
        """Record that our event got called."""
        test_value.append(1)

    hass.bus.async_listen_once("test.event_no_data", listener)

    await mock_api_client.post("/api/events/test.event_no_data")
    await hass.async_block_till_done()

    assert len(test_value) == 1


@test
async def api_fire_event_with_data(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if the API allows us to fire an event."""
    test_value = []

    @ha.callback
    def listener(event):
        """Record that our event got called.

        Also test if our data came through.
        """
        if "test" in event.data:
            test_value.append(1)

    hass.bus.async_listen_once("test_event_with_data", listener)

    await mock_api_client.post("/api/events/test_event_with_data", json={"test": 1})

    await hass.async_block_till_done()

    assert len(test_value) == 1


@test
async def api_fire_event_with_invalid_json(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if the API allows us to fire an event."""
    test_value = []

    @ha.callback
    def listener(event):
        """Record that our event got called."""
        test_value.append(1)

    hass.bus.async_listen_once("test_event_bad_data", listener)

    resp = await mock_api_client.post(
        "/api/events/test_event_bad_data", data=json.dumps("not an object")
    )

    await hass.async_block_till_done()

    assert resp.status == HTTPStatus.BAD_REQUEST
    assert len(test_value) == 0

    resp = await mock_api_client.post(
        "/api/events/test_event_bad_data", data=json.dumps([1, 2, 3])
    )

    await hass.async_block_till_done()

    assert resp.status == HTTPStatus.BAD_REQUEST
    assert len(test_value) == 0


@test
async def api_get_config(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test the return of the configuration."""
    resp = await mock_api_client.get(const.URL_API_CONFIG)
    result = await resp.json()
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
async def api_get_components(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test the return of the components."""
    resp = await mock_api_client.get(const.URL_API_COMPONENTS)
    result = await resp.json()
    assert set(result) == hass.config.components


@test
async def api_get_event_listeners(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if we can get the list of events being listened for."""
    resp = await mock_api_client.get(const.URL_API_EVENTS)
    data = await resp.json()

    local = hass.bus.async_listeners()

    for event in data:
        assert local.pop(event["event"]) == event["listener_count"]

    assert len(local) == 0


@test.skip("snapshot test - port deferred")
async def api_get_services() -> None:
    """Stub for test_api_get_services (port deferred - requires snapshot)."""


@test
async def api_call_service_no_data(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if the API allows us to call a service."""
    test_value = []

    @ha.callback
    def listener(service_call):
        """Record that our service got called."""
        test_value.append(1)

    hass.services.async_register("test_domain", "test_service", listener)

    await mock_api_client.post("/api/services/test_domain/test_service")
    await hass.async_block_till_done()
    assert len(test_value) == 1


@test
async def api_call_service_with_data(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if the API allows us to call a service."""

    @ha.callback
    def listener(service_call):
        """Record that our service got called.

        Also test if our data came through.
        """
        hass.states.async_set(
            "test.data",
            "on",
            {"data": service_call.data["test"]},
            context=service_call.context,
        )

    hass.services.async_register("test_domain", "test_service", listener)

    resp = await mock_api_client.post(
        "/api/services/test_domain/test_service", json={"test": 1}
    )
    data = await resp.json()
    assert len(data) == 1
    state = data[0]
    assert state["entity_id"] == "test.data"
    assert state["state"] == "on"
    assert state["attributes"] == {"data": 1}


SERVICE_DICT = {"changed_states": [], "service_response": {"foo": "bar"}}
RESP_REQUIRED = {
    "message": (
        "Service call requires responses but caller did not ask for "
        "responses. Add ?return_response to query parameters."
    )
}
RESP_UNSUPPORTED = {
    "message": "Service does not support responses. Remove return_response from request."
}


@test.cases(
    test.case(
        "only_with_response",
        supports_response=ha.SupportsResponse.ONLY,
        requested_response=True,
        expected_number_of_service_calls=1,
        expected_status=HTTPStatus.OK,
        expected_response=SERVICE_DICT,
    ),
    test.case(
        "only_without_response",
        supports_response=ha.SupportsResponse.ONLY,
        requested_response=False,
        expected_number_of_service_calls=0,
        expected_status=HTTPStatus.BAD_REQUEST,
        expected_response=RESP_REQUIRED,
    ),
    test.case(
        "optional_with_response",
        supports_response=ha.SupportsResponse.OPTIONAL,
        requested_response=True,
        expected_number_of_service_calls=1,
        expected_status=HTTPStatus.OK,
        expected_response=SERVICE_DICT,
    ),
    test.case(
        "optional_without_response",
        supports_response=ha.SupportsResponse.OPTIONAL,
        requested_response=False,
        expected_number_of_service_calls=1,
        expected_status=HTTPStatus.OK,
        expected_response=[],
    ),
    test.case(
        "none_with_response",
        supports_response=ha.SupportsResponse.NONE,
        requested_response=True,
        expected_number_of_service_calls=0,
        expected_status=HTTPStatus.BAD_REQUEST,
        expected_response=RESP_UNSUPPORTED,
    ),
    test.case(
        "none_without_response",
        supports_response=ha.SupportsResponse.NONE,
        requested_response=False,
        expected_number_of_service_calls=1,
        expected_status=HTTPStatus.OK,
        expected_response=[],
    ),
)
async def api_call_service_returns_response_requested_response(
    supports_response: ha.SupportsResponse,
    requested_response: bool,
    expected_number_of_service_calls: int,
    expected_status: int,
    expected_response: Any,
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if the API allows us to call a service."""
    test_value = []

    @ha.callback
    def listener(service_call):
        """Record that our service got called."""
        test_value.append(1)
        return {"foo": "bar"}

    hass.services.async_register(
        "test_domain", "test_service", listener, supports_response=supports_response
    )

    resp = await mock_api_client.post(
        "/api/services/test_domain/test_service"
        + ("?return_response" if requested_response else "")
    )
    assert resp.status == expected_status
    await hass.async_block_till_done()
    assert len(test_value) == expected_number_of_service_calls
    assert await resp.json() == expected_response


@test
async def api_call_service_client_closed(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test that services keep running if client is closed."""
    test_value = []

    fut = hass.loop.create_future()
    service_call_started = asyncio.Event()

    async def listener(service_call):
        """Wait and return after mock_api_client.post finishes."""
        service_call_started.set()
        value = await fut
        test_value.append(value)

    hass.services.async_register("test_domain", "test_service", listener)

    api_task = hass.async_create_task(
        mock_api_client.post("/api/services/test_domain/test_service")
    )

    await service_call_started.wait()

    assert len(test_value) == 0

    await mock_api_client.close()

    assert len(test_value) == 0
    assert api_task.done()

    try:
        await api_task
    except ServerDisconnectedError:
        pass
    else:
        raise AssertionError("Expected ServerDisconnectedError")

    fut.set_result(1)
    await hass.async_block_till_done()

    assert len(test_value) == 1
    assert test_value[0] == 1


@test
async def api_template(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test the template API."""
    hass.states.async_set("sensor.temperature", 10)

    resp = await mock_api_client.post(
        const.URL_API_TEMPLATE,
        json={"template": "{{ states.sensor.temperature.state }}"},
    )

    body = await resp.text()

    assert body == "10"

    hass.states.async_set("sensor.temperature", 20)
    resp = await mock_api_client.post(
        const.URL_API_TEMPLATE,
        json={"template": "{{ states.sensor.temperature.state }}"},
    )

    body = await resp.text()

    assert body == "20"

    hass.states.async_remove("sensor.temperature")
    resp = await mock_api_client.post(
        const.URL_API_TEMPLATE,
        json={"template": "{{ states.sensor.temperature.state }}"},
    )

    body = await resp.text()

    assert body == ""


@test
async def api_template_cached(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test the template API uses the cache."""
    hass.states.async_set("sensor.temperature", 30)

    resp = await mock_api_client.post(
        const.URL_API_TEMPLATE,
        json={"template": "{{ states.sensor.temperature.state }}"},
    )

    body = await resp.text()

    assert body == "30"

    hass.states.async_set("sensor.temperature", 40)
    resp = await mock_api_client.post(
        const.URL_API_TEMPLATE,
        json={"template": "{{ states.sensor.temperature.state }}"},
    )

    body = await resp.text()

    assert body == "40"


@test
async def api_template_error(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test the template API."""
    hass.states.async_set("sensor.temperature", 10)

    resp = await mock_api_client.post(
        const.URL_API_TEMPLATE, json={"template": "{{ states.sensor.temperature.state"}
    )

    assert resp.status == HTTPStatus.BAD_REQUEST


@test
async def api_template_with_invalid_json(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if API sends appropriate error if send invalid json data."""
    resp = await mock_api_client.post(const.URL_API_TEMPLATE, data="{,}")

    assert resp.status == HTTPStatus.BAD_REQUEST
    assert await resp.json() == {"message": "Invalid JSON specified."}


@test
async def api_template_error_with_string_body(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test that the API returns an appropriate error when a string is sent in the body."""
    hass.states.async_set("sensor.temperature", 10)

    resp = await mock_api_client.post(
        const.URL_API_TEMPLATE,
        json='"{"template": "{{ states.sensor.temperature.state"}"',
    )

    assert resp.status == HTTPStatus.BAD_REQUEST
    assert await resp.json() == {"message": "Template data should be a JSON object."}


async def _stream_next_event(stream):
    """Read the stream for next event while ignoring ping."""
    while True:
        last_new_line = False
        data = b""

        while True:
            dat = await stream.read(1)
            if dat == b"\n" and last_new_line:
                break
            data += dat
            last_new_line = dat == b"\n"

        conv = data.decode("utf-8").strip()[6:]

        if conv != "ping":
            break
    return json.loads(conv)


def _listen_count(hass: HomeAssistant) -> int:
    """Return number of event listeners."""
    return sum(hass.bus.async_listeners().values())


@test
async def stream(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test the stream."""
    listen_count = _listen_count(hass)

    async with mock_api_client.get(const.URL_API_STREAM) as resp:
        assert resp.status == HTTPStatus.OK
        assert listen_count + 1 == _listen_count(hass)

        hass.bus.async_fire("test_event")

        data = await _stream_next_event(resp.content)

        assert data["event_type"] == "test_event"


@test
async def stream_with_restricted(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test the stream with restrictions."""
    listen_count = _listen_count(hass)

    async with mock_api_client.get(
        f"{const.URL_API_STREAM}?restrict=test_event1,test_event3"
    ) as resp:
        assert resp.status == HTTPStatus.OK
        assert listen_count + 1 == _listen_count(hass)

        hass.bus.async_fire("test_event1")
        data = await _stream_next_event(resp.content)
        assert data["event_type"] == "test_event1"

        hass.bus.async_fire("test_event2")
        hass.bus.async_fire("test_event3")
        data = await _stream_next_event(resp.content)
        assert data["event_type"] == "test_event3"


@test.skip("api setup runs during fixture setup, DATA_LOGGING not registered - port deferred")
async def api_error_log() -> None:
    """Stub for test_api_error_log (port deferred)."""

    with patch(
        "aiohttp.web.FileResponse", return_value=web.Response(text="Hello")
    ) as mock_file:
        resp = await client.get(
            const.URL_API_ERROR_LOG,
            headers={"Authorization": f"Bearer {hass_access_token}"},
        )

    assert len(mock_file.mock_calls) == 1
    assert mock_file.mock_calls[0][1][0] == hass.data[DATA_LOGGING]
    assert resp.status == HTTPStatus.OK
    assert await resp.text() == "Hello"

    hass_admin_user.groups = []
    resp = await client.get(
        const.URL_API_ERROR_LOG,
        headers={"Authorization": f"Bearer {hass_access_token}"},
    )
    assert resp.status == HTTPStatus.UNAUTHORIZED


@test
async def api_fire_event_context(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test if the API sets right context if we fire an event."""
    test_value = []

    @ha.callback
    def listener(event):
        """Record that our event got called."""
        test_value.append(event)

    hass.bus.async_listen("test.event", listener)

    await mock_api_client.post(
        "/api/events/test.event",
        headers={"authorization": f"Bearer {hass_access_token}"},
    )
    await hass.async_block_till_done()

    refresh_token = hass.auth.async_validate_access_token(hass_access_token)

    assert len(test_value) == 1
    assert test_value[0].context.user_id == refresh_token.user.id


@test
async def api_call_service_context(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test if the API sets right context if we call a service."""
    calls = async_mock_service(hass, "test_domain", "test_service")

    await mock_api_client.post(
        "/api/services/test_domain/test_service",
        headers={"authorization": f"Bearer {hass_access_token}"},
    )
    await hass.async_block_till_done()

    refresh_token = hass.auth.async_validate_access_token(hass_access_token)

    assert len(calls) == 1
    assert calls[0].context.user_id == refresh_token.user.id


@test
async def api_set_state_context(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test if the API sets right context if we set state."""
    await mock_api_client.post(
        "/api/states/light.kitchen",
        json={"state": "on"},
        headers={"authorization": f"Bearer {hass_access_token}"},
    )

    refresh_token = hass.auth.async_validate_access_token(hass_access_token)

    state = hass.states.get("light.kitchen")
    assert state.context.user_id == refresh_token.user.id


@test
async def event_stream_requires_admin(
    mock_api_client: TestClient = Depends(mock_api_client),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test user needs to be admin to access event stream."""
    hass_admin_user.groups = []
    resp = await mock_api_client.get("/api/stream")
    assert resp.status == HTTPStatus.UNAUTHORIZED


@test
async def states(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test fetching all states as admin."""
    hass.states.async_set("test.entity", "hello")
    hass.states.async_set("test.entity2", "hello")
    resp = await mock_api_client.get(const.URL_API_STATES)
    assert resp.status == HTTPStatus.OK
    json_data = await resp.json()
    assert len(json_data) == 2
    assert json_data[0]["entity_id"] == "test.entity"
    assert json_data[1]["entity_id"] == "test.entity2"


@test
async def states_view_filters(
    hass: HomeAssistant = Depends(hass_fx),
    hass_read_only_user: MockUser = Depends(hass_read_only_user_fx),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test filtering only visible states."""
    assert not hass_read_only_user.is_admin
    hass_read_only_user.mock_policy({"entities": {"entity_ids": {"test.entity": True}}})
    await async_setup_component(hass, "api", {})
    read_only_user_credential = Credentials(
        id="mock-read-only-credential-id",
        auth_provider_type="homeassistant",
        auth_provider_id=None,
        data={"username": "readonly"},
        is_new=False,
    )
    await hass.auth.async_link_user(hass_read_only_user, read_only_user_credential)

    refresh_token = await hass.auth.async_create_refresh_token(
        hass_read_only_user, CLIENT_ID, credential=read_only_user_credential
    )
    token = hass.auth.async_create_access_token(refresh_token)
    mock_api_client_inner = await hass_client(token)
    hass.states.async_set("test.entity", "hello")
    hass.states.async_set("test.not_visible_entity", "invisible")
    resp = await mock_api_client_inner.get(const.URL_API_STATES)
    assert resp.status == HTTPStatus.OK
    json_data = await resp.json()
    assert len(json_data) == 1
    assert json_data[0]["entity_id"] == "test.entity"


@test
async def get_entity_state_read_perm(
    mock_api_client: TestClient = Depends(mock_api_client),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test getting a state requires read permission."""
    hass_admin_user.mock_policy({})
    hass_admin_user.groups = []
    assert hass_admin_user.is_admin is False
    resp = await mock_api_client.get("/api/states/light.test")
    assert resp.status == HTTPStatus.UNAUTHORIZED


@test
async def post_entity_state_admin(
    mock_api_client: TestClient = Depends(mock_api_client),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test updating state requires admin."""
    hass_admin_user.groups = []
    resp = await mock_api_client.post("/api/states/light.test")
    assert resp.status == HTTPStatus.UNAUTHORIZED


@test
async def delete_entity_state_admin(
    mock_api_client: TestClient = Depends(mock_api_client),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test deleting entity requires admin."""
    hass_admin_user.groups = []
    resp = await mock_api_client.delete("/api/states/light.test")
    assert resp.status == HTTPStatus.UNAUTHORIZED


@test
async def post_event_admin(
    mock_api_client: TestClient = Depends(mock_api_client),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test sending event requires admin."""
    hass_admin_user.groups = []
    resp = await mock_api_client.post("/api/events/state_changed")
    assert resp.status == HTTPStatus.UNAUTHORIZED


@test
async def rendering_template_admin(
    mock_api_client: TestClient = Depends(mock_api_client),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test rendering a template requires admin."""
    hass_admin_user.groups = []
    resp = await mock_api_client.post(const.URL_API_TEMPLATE)
    assert resp.status == HTTPStatus.UNAUTHORIZED


@test
async def api_call_service_not_found(
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if the API fails 400 if unknown service."""
    resp = await mock_api_client.post("/api/services/test_domain/test_service")
    assert resp.status == HTTPStatus.BAD_REQUEST


@test
async def api_call_service_bad_data(
    hass: HomeAssistant = Depends(hass_fx),
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test if the API fails 400 if unknown service."""
    test_value = []

    @ha.callback
    def listener(service_call):
        """Record that our service got called."""
        test_value.append(1)

    hass.services.async_register(
        "test_domain", "test_service", listener, schema=vol.Schema({"hello": str})
    )

    resp = await mock_api_client.post(
        "/api/services/test_domain/test_service", json={"hello": 5}
    )
    assert resp.status == HTTPStatus.BAD_REQUEST


@test
async def api_status(
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test getting the api status."""
    resp = await mock_api_client.get("/api/")
    assert resp.status == HTTPStatus.OK
    json_data = await resp.json()
    assert json_data["message"] == "API running."


@test
async def api_core_state(
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test getting core status."""
    resp = await mock_api_client.get("/api/core/state")
    assert resp.status == HTTPStatus.OK
    json_data = await resp.json()
    assert json_data == {
        "state": "RUNNING",
        "recorder_state": {"migration_in_progress": False, "migration_is_live": False},
    }


@test.cases(
    test.case(
        "neither", migration_in_progress=False, migration_is_live=False
    ),
    test.case(
        "live_only", migration_in_progress=False, migration_is_live=True
    ),
    test.case(
        "in_progress_only", migration_in_progress=True, migration_is_live=False
    ),
    test.case(
        "both", migration_in_progress=True, migration_is_live=True
    ),
)
async def api_core_state_recorder_migrating(
    migration_in_progress: bool,
    migration_is_live: bool,
    mock_api_client: TestClient = Depends(mock_api_client),
) -> None:
    """Test getting core status."""
    with (
        patch(
            "homeassistant.helpers.recorder.async_migration_in_progress",
            return_value=migration_in_progress,
        ),
        patch(
            "homeassistant.helpers.recorder.async_migration_is_live",
            return_value=migration_is_live,
        ),
    ):
        resp = await mock_api_client.get("/api/core/state")
    assert resp.status == HTTPStatus.OK
    json_data = await resp.json()
    expected_recorder_state = {
        "migration_in_progress": migration_in_progress,
        "migration_is_live": migration_is_live,
    }
    assert json_data == {"state": "RUNNING", "recorder_state": expected_recorder_state}
