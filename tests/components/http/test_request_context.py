"""Test request context middleware."""

from contextvars import ContextVar
from http import HTTPStatus

from aiohttp import web
from tryke import Depends, expect, fixture, test

from homeassistant.components.http.request_context import setup_request_context

from tests.hass_fixtures import (
    aiohttp_client as aiohttp_client_fixture,
    mock_network,
)
from tests.typing import ClientSessionGenerator


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def request_context_middleware(
    _trigger: None = Depends(_trigger_executor),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
) -> None:
    """Test that request context is set from middleware."""
    context = ContextVar("request", default=None)
    app = web.Application()

    async def mock_handler(request):
        """Return the real IP as text."""
        request_context = context.get()
        assert request_context
        assert request_context == request

        return web.Response(text="hi!")

    app.router.add_get("/", mock_handler)
    setup_request_context(app, context)
    mock_api_client = await aiohttp_client(app)

    resp = await mock_api_client.get("/")
    expect(resp.status).to_equal(HTTPStatus.OK)

    text = await resp.text()
    expect(text).to_equal("hi!")

    expect(context.get() is None).to_be(True)
