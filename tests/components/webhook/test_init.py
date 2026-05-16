"""Test the webhook component."""

from http import HTTPStatus
from ipaddress import ip_address
from unittest.mock import Mock, patch

from aiohttp import web
from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant.components import webhook
from homeassistant.components.websocket_api import auth, http
from homeassistant.core import HomeAssistant
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.setup import async_setup_component
from homeassistant.util.aiohttp import MockRequest

from tests.hass_fixtures import (
    ClientSessionGenerator,
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    hass_access_token as hass_access_token_fixture,
    hass_client as hass_client_fixture,
    hass_client_no_auth as hass_client_no_auth_fixture,
    hass_ws_client as hass_ws_client_fixture,
)
from tests.test_util import mock_real_ip


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
async def mock_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> TestClient:
    """Create http client for webhooks."""
    await async_setup_component(hass, "webhook", {})
    return await hass_client()


@test
async def unregistering_webhook(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test unregistering a webhook."""
    hooks = []
    webhook_id = webhook.async_generate_id()

    async def handle(*args):
        """Handle webhook."""
        hooks.append(args)

    webhook.async_register(hass, "test", "Test hook", webhook_id, handle)

    resp = await mock_client.post(f"/api/webhook/{webhook_id}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(hooks).to_have_length(1)

    webhook.async_unregister(hass, webhook_id)

    resp = await mock_client.post(f"/api/webhook/{webhook_id}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(hooks).to_have_length(1)


@test
async def generate_webhook_url(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we generate a webhook url correctly."""
    await async_process_ha_core_config(
        hass,
        {"external_url": "https://example.com"},
    )
    url = webhook.async_generate_url(hass, "some_id")

    expect(url).to_equal("https://example.com/api/webhook/some_id")


@test
async def generate_webhook_url_internal(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can get the internal URL."""
    await async_process_ha_core_config(
        hass,
        {
            "internal_url": "http://192.168.1.100:8123",
            "external_url": "https://example.com",
        },
    )
    url = webhook.async_generate_url(
        hass, "some_id", allow_external=False, allow_ip=True
    )

    expect(url).to_equal("http://192.168.1.100:8123/api/webhook/some_id")


@test
async def async_generate_path(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test generating just the path component of the url correctly."""
    path = webhook.async_generate_path("some_id")
    expect(path).to_equal("/api/webhook/some_id")


@test
async def posting_webhook_nonexisting(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test posting to a nonexisting webhook."""
    resp = await mock_client.post("/api/webhook/non-existing")
    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def posting_webhook_invalid_json(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test posting to a nonexisting webhook."""
    webhook.async_register(hass, "test", "Test hook", "hello", None)
    resp = await mock_client.post("/api/webhook/hello", data="not-json")
    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def posting_webhook_json(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test posting a webhook with JSON data."""
    hooks = []
    webhook_id = webhook.async_generate_id()

    async def handle(*args):
        """Handle webhook."""
        hooks.append((args[0], args[1], await args[2].text()))

    webhook.async_register(hass, "test", "Test hook", webhook_id, handle)

    resp = await mock_client.post(f"/api/webhook/{webhook_id}", json={"data": True})
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(hooks).to_have_length(1)
    expect(hooks[0][0]).to_be(hass)
    expect(hooks[0][1]).to_equal(webhook_id)
    expect(hooks[0][2]).to_equal('{"data": true}')


@test
async def posting_webhook_no_data(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test posting a webhook with no data."""
    hooks = []
    webhook_id = webhook.async_generate_id()

    async def handle(*args):
        """Handle webhook."""
        hooks.append(args)

    webhook.async_register(hass, "test", "Test hook", webhook_id, handle)

    resp = await mock_client.post(f"/api/webhook/{webhook_id}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(hooks).to_have_length(1)
    expect(hooks[0][0]).to_be(hass)
    expect(hooks[0][1]).to_equal(webhook_id)
    expect(hooks[0][2].method).to_equal("POST")
    expect(await hooks[0][2].text()).to_equal("")


@test
async def webhook_put(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test sending a put request to a webhook."""
    hooks = []
    webhook_id = webhook.async_generate_id()

    async def handle(*args):
        """Handle webhook."""
        hooks.append(args)

    webhook.async_register(hass, "test", "Test hook", webhook_id, handle)

    resp = await mock_client.put(f"/api/webhook/{webhook_id}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(hooks).to_have_length(1)
    expect(hooks[0][0]).to_be(hass)
    expect(hooks[0][1]).to_equal(webhook_id)
    expect(hooks[0][2].method).to_equal("PUT")


@test
async def webhook_head(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test sending a head request to a webhook."""
    hooks = []
    webhook_id = webhook.async_generate_id()

    async def handle(*args):
        """Handle webhook."""
        hooks.append(args)

    webhook.async_register(
        hass, "test", "Test hook", webhook_id, handle, allowed_methods=["HEAD"]
    )

    resp = await mock_client.head(f"/api/webhook/{webhook_id}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(hooks).to_have_length(1)
    expect(hooks[0][0]).to_be(hass)
    expect(hooks[0][1]).to_equal(webhook_id)
    expect(hooks[0][2].method).to_equal("HEAD")

    # Test that status is HTTPStatus.OK even when HEAD is not allowed.
    webhook.async_unregister(hass, webhook_id)
    webhook.async_register(
        hass, "test", "Test hook", webhook_id, handle, allowed_methods=["PUT"]
    )
    resp = await mock_client.head(f"/api/webhook/{webhook_id}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(hooks).to_have_length(1)  # Should not have been called


@test
async def webhook_get(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test sending a get request to a webhook."""
    hooks = []
    webhook_id = webhook.async_generate_id()

    async def handle(*args):
        """Handle webhook."""
        hooks.append(args)

    webhook.async_register(
        hass, "test", "Test hook", webhook_id, handle, allowed_methods=["GET"]
    )

    resp = await mock_client.get(f"/api/webhook/{webhook_id}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(hooks).to_have_length(1)
    expect(hooks[0][0]).to_be(hass)
    expect(hooks[0][1]).to_equal(webhook_id)
    expect(hooks[0][2].method).to_equal("GET")

    # Test that status is HTTPStatus.METHOD_NOT_ALLOWED even when GET is not allowed.
    webhook.async_unregister(hass, webhook_id)
    webhook.async_register(
        hass, "test", "Test hook", webhook_id, handle, allowed_methods=["PUT"]
    )
    resp = await mock_client.get(f"/api/webhook/{webhook_id}")
    expect(resp.status).to_equal(HTTPStatus.METHOD_NOT_ALLOWED)
    expect(hooks).to_have_length(1)  # Should not have been called


@test
async def webhook_not_allowed_method(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that an exception is raised if an unsupported method is used."""
    webhook_id = webhook.async_generate_id()

    async def handle(*args):
        pass

    expect(
        lambda: webhook.async_register(
            hass, "test", "Test hook", webhook_id, handle, allowed_methods=["PATCH"]
        )
    ).to_raise(ValueError)


@test
async def webhook_local_only(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: TestClient = Depends(mock_client),
) -> None:
    """Test posting a webhook with local only."""
    hass.config.components.add("cloud")

    hooks = []
    webhook_id = webhook.async_generate_id()

    async def handle(*args):
        """Handle webhook."""
        hooks.append((args[0], args[1], await args[2].text()))

    webhook.async_register(
        hass, "test", "Test hook", webhook_id, handle, local_only=True
    )

    resp = await mock_client.post(f"/api/webhook/{webhook_id}", json={"data": True})
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(hooks).to_have_length(1)
    expect(hooks[0][0]).to_be(hass)
    expect(hooks[0][1]).to_equal(webhook_id)
    expect(hooks[0][2]).to_equal('{"data": true}')

    # Request from remote IP
    with patch(
        "homeassistant.components.webhook.ip_address",
        return_value=ip_address("123.123.123.123"),
    ):
        resp = await mock_client.post(f"/api/webhook/{webhook_id}", json={"data": True})
    expect(resp.status).to_equal(HTTPStatus.OK)
    # No hook received
    expect(hooks).to_have_length(1)

    # Request from Home Assistant Cloud remote UI
    with patch(
        "hass_nabucasa.remote.is_cloud_request", Mock(get=Mock(return_value=True))
    ):
        resp = await mock_client.post(f"/api/webhook/{webhook_id}", json={"data": True})

    # No hook received
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(hooks).to_have_length(1)


@test.cases(
    test.case("remote_none", remote=None, expected_calls=0),
    test.case("remote_public", remote="123.123.123.123", expected_calls=0),
    test.case("remote_not_an_ip", remote="not-an-ip", expected_calls=0),
    test.case("remote_local", remote="192.168.1.50", expected_calls=1),
)
async def webhook_local_only_mock_request(
    remote: str | None,
    expected_calls: int,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test local_only webhooks for MockRequests with various remote values."""
    await async_setup_component(hass, "webhook", {})

    hooks = []
    webhook_id = webhook.async_generate_id()

    async def handle(hass: HomeAssistant, webhook_id: str, request: web.Request):
        """Handle webhook."""
        hooks.append((hass, webhook_id, await request.text()))

    webhook.async_register(
        hass, "test", "Test hook", webhook_id, handle, local_only=True
    )

    request = MockRequest(
        content=b'{"data": true}',
        headers={"Content-Type": "application/json"},
        method="POST",
        query_string="",
        mock_source="test",
        remote=remote,
    )
    resp = await webhook.async_handle_webhook(hass, webhook_id, request)
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(hooks).to_have_length(expected_calls)


@test
async def listing_webhook(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fixture),
    hass_access_token: str = Depends(hass_access_token_fixture),
) -> None:
    """Test unregistering a webhook."""
    # Equivalent of enable_custom_integrations
    hass.data.pop("custom_components", None)
    expect(await async_setup_component(hass, "webhook", {})).to_be(True)
    client = await hass_ws_client(hass, hass_access_token)

    webhook.async_register(hass, "test", "Test hook", "my-id", None)
    webhook.async_register(
        hass,
        "test",
        "Test hook",
        "my-2",
        None,
        local_only=True,
        allowed_methods=["GET"],
    )

    await client.send_json({"id": 5, "type": "webhook/list"})

    msg = await client.receive_json()
    expect(msg["id"]).to_equal(5)
    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        [
            {
                "webhook_id": "my-id",
                "domain": "test",
                "name": "Test hook",
                "local_only": False,
                "allowed_methods": ["POST", "PUT"],
            },
            {
                "webhook_id": "my-2",
                "domain": "test",
                "name": "Test hook",
                "local_only": True,
                "allowed_methods": ["GET"],
            },
        ]
    )


@test
async def ws_webhook(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test sending webhook msg via WS API."""
    expect(await async_setup_component(hass, "webhook", {})).to_be(True)

    received = []

    async def handler(
        hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        """Handle a webhook."""
        received.append(request)
        return web.json_response({"from": "handler"})

    webhook.async_register(hass, "test", "Test", "mock-webhook-id", handler)

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 5,
            "type": "webhook/handle",
            "webhook_id": "mock-webhook-id",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": '{"hello": "world"}',
            "query": "a=2",
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    expect(result["result"]).to_equal(
        {
            "status": 200,
            "body": '{"from": "handler"}',
            "headers": {"Content-Type": "application/json"},
        }
    )

    expect(received).to_have_length(1)
    expect(received[0].headers["content-type"]).to_equal("application/json")
    expect(received[0].query).to_equal({"a": "2"})
    expect(await received[0].json()).to_equal({"hello": "world"})
    # The MockRequest is created with the websocket connection's remote IP
    expect(received[0].remote).not_.to_be_none()

    # Non existing webhook
    caplog.clear()

    await client.send_json(
        {
            "id": 6,
            "type": "webhook/handle",
            "webhook_id": "mock-nonexisting-id",
            "method": "POST",
            "body": '{"nonexisting": "payload"}',
        }
    )

    result = await client.receive_json()
    expect(result["success"]).to_be(True)
    expect(result["result"]).to_equal(
        {
            "status": 200,
            "body": None,
            "headers": {"Content-Type": "application/octet-stream"},
        }
    )

    expect(caplog.text).to_contain(
        "Received message for unregistered webhook mock-nonexisting-id from webhook/ws"
    )
    expect(caplog.text).to_contain('{"nonexisting": "payload"}')


@test.cases(
    test.case("local_ip", remote_ip="192.168.1.50", expected_calls=1),
    test.case("remote_ip", remote_ip="123.123.123.123", expected_calls=0),
)
async def ws_webhook_local_only(
    remote_ip: str,
    expected_calls: int,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    hass_access_token: str = Depends(hass_access_token_fixture),
) -> None:
    """Test a local_only webhook over the websocket connection."""
    a = hass.http.app.frozen if hasattr(hass, "http") else "no http yet"
    expect(await async_setup_component(hass, "webhook", {})).to_be(True)
    b = hass.http.app.frozen
    expect(await async_setup_component(hass, "websocket_api", {})).to_be(True)
    c = hass.http.app.frozen
    await hass.async_block_till_done()
    d = hass.http.app.frozen
    raise RuntimeError(f"a={a} b={b} c={c} d={d}")

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

    set_mock_ip = mock_real_ip(hass.http.app)
    set_mock_ip(remote_ip)

    client = await hass_client_no_auth()

    async with client.ws_connect(http.URL) as ws:
        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(auth.TYPE_AUTH_REQUIRED)

        await ws.send_json({"type": auth.TYPE_AUTH, "access_token": hass_access_token})
        auth_msg = await ws.receive_json()
        expect(auth_msg["type"]).to_equal(auth.TYPE_AUTH_OK)

        await ws.send_json(
            {
                "id": 5,
                "type": "webhook/handle",
                "webhook_id": "mock-webhook-id",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": '{"hello": "world"}',
                "query": "",
            }
        )
        result = await ws.receive_json()

    expect(result["success"]).to_be(True)
    expect(result["result"]["status"]).to_equal(HTTPStatus.OK)
    expect(received).to_have_length(expected_calls)
    if expected_calls:
        expect(received[0].remote).to_equal(remote_ip)
