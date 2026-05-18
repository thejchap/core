"""The tests for the webhook automation trigger."""

from ipaddress import ip_address
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant, callback
from homeassistant.setup import async_setup_component

from tests.common import async_capture_events
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)


@fixture
async def setup_http(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Set up http."""
    assert await async_setup_component(hass, "http", {})
    assert await async_setup_component(hass, "webhook", {})
    await hass.async_block_till_done()
    return hass


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    return 0


@test
async def webhook_json(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_http),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Test triggering with a JSON webhook."""
    events = []

    @callback
    def store_event(event):
        """Help store events."""
        events.append(event)

    hass.bus.async_listen("test_success", store_event)

    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "trigger": {"platform": "webhook", "webhook_id": "json_webhook"},
                "action": {
                    "event": "test_success",
                    "event_data_template": {
                        "hello": "yo {{ trigger.json.hello }}",
                        "id": "{{ trigger.id}}",
                    },
                },
            }
        },
    )
    await hass.async_block_till_done()

    client = await client_gen()

    await client.post("/api/webhook/json_webhook", json={"hello": "world"})
    await hass.async_block_till_done()

    expect(len(events)).to_equal(1)
    expect(events[0].data["hello"]).to_equal("yo world")
    expect(events[0].data["id"]).to_equal(0)


@test
async def webhook_post(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_http),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Test triggering with a POST webhook."""
    # Set up fake cloud
    hass.config.components.add("cloud")

    events = []

    @callback
    def store_event(event):
        """Help store events."""
        events.append(event)

    hass.bus.async_listen("test_success", store_event)

    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "trigger": {
                    "platform": "webhook",
                    "webhook_id": "post_webhook",
                    "local_only": True,
                },
                "action": {
                    "event": "test_success",
                    "event_data_template": {"hello": "yo {{ trigger.data.hello }}"},
                },
            }
        },
    )
    await hass.async_block_till_done()

    client = await client_gen()

    await client.post("/api/webhook/post_webhook", data={"hello": "world"})
    await hass.async_block_till_done()

    expect(len(events)).to_equal(1)
    expect(events[0].data["hello"]).to_equal("yo world")

    # Request from remote IP
    with patch(
        "homeassistant.components.webhook.ip_address",
        return_value=ip_address("123.123.123.123"),
    ):
        await client.post("/api/webhook/post_webhook", data={"hello": "world"})
    # No hook received
    await hass.async_block_till_done()
    expect(len(events)).to_equal(1)

    # Request from Home Assistant Cloud remote UI
    with patch(
        "hass_nabucasa.remote.is_cloud_request", Mock(get=Mock(return_value=True))
    ):
        await client.post("/api/webhook/post_webhook", data={"hello": "world"})

    # No hook received
    await hass.async_block_till_done()
    expect(len(events)).to_equal(1)


@test
async def webhook_allowed_methods_internet(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_http),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Test the webhook obeys allowed_methods and local_only options."""
    events = []

    @callback
    def store_event(event):
        """Help store events."""
        events.append(event)

    hass.bus.async_listen("test_success", store_event)

    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "trigger": {
                    "platform": "webhook",
                    "webhook_id": "post_webhook",
                    "allowed_methods": "PUT",
                    "local_only": False,
                },
                "action": {
                    "event": "test_success",
                },
            }
        },
    )
    await hass.async_block_till_done()

    client = await client_gen()

    await client.post("/api/webhook/post_webhook")
    await hass.async_block_till_done()

    expect(len(events)).to_equal(0)

    # Request from remote IP
    with patch(
        "homeassistant.components.webhook.ip_address",
        return_value=ip_address("123.123.123.123"),
    ):
        await client.put("/api/webhook/post_webhook")
    await hass.async_block_till_done()
    expect(len(events)).to_equal(1)


@test
async def webhook_query(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_http),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Test triggering with a query POST webhook."""
    events = []

    @callback
    def store_event(event):
        """Help store events."""
        events.append(event)

    hass.bus.async_listen("test_success", store_event)

    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "trigger": {"platform": "webhook", "webhook_id": "query_webhook"},
                "action": {
                    "event": "test_success",
                    "event_data_template": {"hello": "yo {{ trigger.query.hello }}"},
                },
            }
        },
    )
    await hass.async_block_till_done()

    client = await client_gen()

    await client.post("/api/webhook/query_webhook?hello=world")
    await hass.async_block_till_done()

    expect(len(events)).to_equal(1)
    expect(events[0].data["hello"]).to_equal("yo world")


@test
async def webhook_multiple(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_http),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Test triggering multiple triggers with a POST webhook."""
    events1 = []
    events2 = []

    @callback
    def store_event1(event):
        """Help store events."""
        events1.append(event)

    @callback
    def store_event2(event):
        """Help store events."""
        events2.append(event)

    hass.bus.async_listen("test_success1", store_event1)
    hass.bus.async_listen("test_success2", store_event2)

    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": [
                {
                    "trigger": {"platform": "webhook", "webhook_id": "post_webhook"},
                    "action": {
                        "event": "test_success1",
                        "event_data_template": {"hello": "yo {{ trigger.data.hello }}"},
                    },
                },
                {
                    "trigger": {"platform": "webhook", "webhook_id": "post_webhook"},
                    "action": {
                        "event": "test_success2",
                        "event_data_template": {
                            "hello": "yo2 {{ trigger.data.hello }}"
                        },
                    },
                },
            ]
        },
    )
    await hass.async_block_till_done()

    client = await client_gen()

    await client.post("/api/webhook/post_webhook", data={"hello": "world"})
    await hass.async_block_till_done()

    expect(len(events1)).to_equal(1)
    expect(events1[0].data["hello"]).to_equal("yo world")
    expect(len(events2)).to_equal(1)
    expect(events2[0].data["hello"]).to_equal("yo2 world")


@test
async def webhook_reload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_http),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Test reloading a webhook."""
    events = []

    @callback
    def store_event(event):
        """Help store events."""
        events.append(event)

    hass.bus.async_listen("test_success", store_event)

    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "trigger": {"platform": "webhook", "webhook_id": "post_webhook"},
                "action": {
                    "event": "test_success",
                    "event_data_template": {"hello": "yo {{ trigger.data.hello }}"},
                },
            }
        },
    )
    await hass.async_block_till_done()

    client = await client_gen()

    await client.post("/api/webhook/post_webhook", data={"hello": "world"})
    await hass.async_block_till_done()

    expect(len(events)).to_equal(1)
    expect(events[0].data["hello"]).to_equal("yo world")

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            "automation": {
                "trigger": {"platform": "webhook", "webhook_id": "post_webhook"},
                "action": {
                    "event": "test_success",
                    "event_data_template": {"hello": "yo2 {{ trigger.data.hello }}"},
                },
            }
        },
    ):
        await hass.services.async_call(
            "automation",
            "reload",
            blocking=True,
        )
        await hass.async_block_till_done()

    await client.post("/api/webhook/post_webhook", data={"hello": "world"})
    await hass.async_block_till_done()

    expect(len(events)).to_equal(2)
    expect(events[1].data["hello"]).to_equal("yo2 world")


@test
async def webhook_template(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_http),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Test triggering with a template webhook."""
    # Set up fake cloud
    hass.config.components.add("cloud")

    events = []

    @callback
    def store_event(event):
        """Help store events."""
        events.append(event)

    hass.bus.async_listen("test_success", store_event)

    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "trigger": {
                    "platform": "webhook",
                    "webhook_id": "webhook-{{ sqrt(9)|round }}",
                    "local_only": True,
                },
                "action": {
                    "event": "test_success",
                    "event_data_template": {"hello": "yo {{ trigger.data.hello }}"},
                },
            }
        },
    )
    await hass.async_block_till_done()

    client = await client_gen()

    await client.post("/api/webhook/webhook-3", data={"hello": "world"})
    await hass.async_block_till_done()

    expect(len(events)).to_equal(1)
    expect(events[0].data["hello"]).to_equal("yo world")


@test
async def webhook_query_json_header_no_payload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(setup_http),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Test requests with application/json header but no payload."""
    events = async_capture_events(hass, "test_success")

    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "trigger": {
                    "platform": "webhook",
                    "webhook_id": "no_payload_webhook",
                    "local_only": True,
                    "allowed_methods": ["GET", "POST"],
                },
                "action": {
                    "event": "test_success",
                },
            }
        },
    )
    await hass.async_block_till_done()
    client = await client_gen()

    # GET
    response = await client.get(
        "/api/webhook/no_payload_webhook", headers={"Content-Type": "application/json"}
    )
    await hass.async_block_till_done()
    expect(response.status).to_equal(200)

    # POST
    response = await client.post(
        "/api/webhook/no_payload_webhook", headers={"Content-Type": "application/json"}
    )
    await hass.async_block_till_done()
    expect(response.status).to_equal(200)

    expect(len(events)).to_equal(2)
