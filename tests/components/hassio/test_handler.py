"""The tests for the hassio component."""

from typing import Any, Literal

from aiohttp import hdrs, web
from aiohttp.test_utils import RawTestServer
from pytest_socket import enable_socket, socket_allow_hosts
from tryke import Depends, expect, fixture, test

from homeassistant.components.hassio.handler import HassIO, HassioAPIError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ._fixtures import hassio_stubs
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@fixture
def socket_enabled() -> None:
    """Re-enable sockets for tests that need a real loopback server."""
    socket_allow_hosts(["127.0.0.1", "localhost", "::1"], allow_unix_socket=True)
    enable_socket()


@test.cases(
    test.case("ingress_panels", api_call="/ingress/panels", method="GET", payload=None),
    test.case(
        "supervisor_options",
        api_call="/supervisor/options",
        method="POST",
        payload={"diagnostics": True},
    ),
    test.case(
        "supervisor_update", api_call="/supervisor/update", method="POST", payload=None
    ),
)
async def api_headers(
    api_call: str,
    method: Literal["GET", "POST"],
    payload: Any,
    _socket_enabled: None = Depends(socket_enabled),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test headers are forwarded correctly."""
    received_request: web.BaseRequest | None = None

    async def mock_handler(request: web.BaseRequest) -> web.Response:
        """Return OK."""
        nonlocal received_request
        received_request = request
        return web.json_response({"result": "ok", "data": None})

    server = RawTestServer(mock_handler)
    await server.start_server()
    try:
        hassio_handler = HassIO(
            hass.loop,
            async_get_clientsession(hass),
            f"{server.host}:{server.port}",
        )

        await hassio_handler.send_command(api_call, method, payload)
        expect(received_request is not None).to_equal(True)

        expect(received_request.method).to_equal(method)
        expect(received_request.headers.get("X-Hass-Source")).to_equal("core.handler")

        if method == "GET":
            expect(hdrs.CONTENT_TYPE in received_request.headers).to_equal(False)
        else:
            expect(hdrs.CONTENT_TYPE in received_request.headers).to_equal(True)
            if payload:
                expect(received_request.headers[hdrs.CONTENT_TYPE]).to_equal(
                    "application/json"
                )
            else:
                expect(received_request.headers[hdrs.CONTENT_TYPE]).to_equal(
                    "application/octet-stream"
                )
    finally:
        await server.close()


@test
async def send_command_invalid_command(
    _stubs: None = Depends(hassio_stubs),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test send command fails when command is invalid."""
    hassio: HassIO = hass.data["hassio"]
    # absolute path
    async with expect_raises_async(HassioAPIError):
        await hassio.send_command("/test/../bad")
    # relative path
    async with expect_raises_async(HassioAPIError):
        await hassio.send_command("test/../bad")
    # relative path with percent encoding
    async with expect_raises_async(HassioAPIError):
        await hassio.send_command("test/%2E%2E/bad")
