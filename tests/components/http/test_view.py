"""Tests for Home Assistant View."""

from decimal import Decimal
from http import HTTPStatus
import json
import math
from unittest.mock import AsyncMock, Mock, patch

from aiohttp.web_exceptions import (
    HTTPBadRequest,
    HTTPInternalServerError,
    HTTPUnauthorized,
)
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components.http import KEY_HASS
from homeassistant.components.http.view import (
    HomeAssistantView,
    request_handler_factory,
)
from homeassistant.exceptions import ServiceNotFound, Unauthorized
from homeassistant.helpers.network import NoURLAvailableError

from tests.hass_fixtures import LogCapture, caplog as caplog_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


@fixture
def mock_request() -> Mock:
    """Mock a request."""
    return Mock(app={KEY_HASS: Mock(is_stopping=False)}, match_info={})


@fixture
def mock_request_with_stopping() -> Mock:
    """Mock a request."""
    return Mock(app={KEY_HASS: Mock(is_stopping=True)}, match_info={})


@test
async def invalid_json(caplog: LogCapture = Depends(caplog_fixture)) -> None:
    """Test trying to return invalid JSON."""
    expect(lambda: HomeAssistantView.json({"hello": Decimal("2.0")})).to_raise(
        HTTPInternalServerError
    )

    expect(
        "Unable to serialize to JSON. Bad data found at $.hello=2.0(<class 'decimal.Decimal'>"
        in caplog.text
    ).to_be(True)


@test
async def nan_serialized_to_null() -> None:
    """Test nan serialized to null JSON."""
    response = HomeAssistantView.json(math.nan)
    expect(json.loads(response.body.decode("utf-8"))).to_be(None)


@test
async def handling_unauthorized(
    mock_request: Mock = Depends(mock_request),
) -> None:
    """Test handling unauth exceptions."""
    async with expect_raises_async(HTTPUnauthorized):
        await request_handler_factory(
            mock_request.app[KEY_HASS],
            Mock(requires_auth=False),
            AsyncMock(side_effect=Unauthorized),
        )(mock_request)


@test
async def handling_invalid_data(
    mock_request: Mock = Depends(mock_request),
) -> None:
    """Test handling unauth exceptions."""
    async with expect_raises_async(HTTPBadRequest):
        await request_handler_factory(
            mock_request.app[KEY_HASS],
            Mock(requires_auth=False),
            AsyncMock(side_effect=vol.Invalid("yo")),
        )(mock_request)


@test
async def handling_service_not_found(
    mock_request: Mock = Depends(mock_request),
) -> None:
    """Test handling unauth exceptions."""
    async with expect_raises_async(HTTPInternalServerError):
        await request_handler_factory(
            mock_request.app[KEY_HASS],
            Mock(requires_auth=False),
            AsyncMock(side_effect=ServiceNotFound("test", "test")),
        )(mock_request)


@test
async def not_running(
    mock_request_with_stopping: Mock = Depends(mock_request_with_stopping),
) -> None:
    """Test we get a 503 when not running."""
    response = await request_handler_factory(
        mock_request_with_stopping.app[KEY_HASS],
        Mock(requires_auth=False),
        AsyncMock(side_effect=Unauthorized),
    )(mock_request_with_stopping)
    expect(response.status).to_equal(HTTPStatus.SERVICE_UNAVAILABLE)


@test
async def invalid_handler(
    mock_request: Mock = Depends(mock_request),
) -> None:
    """Test an invalid handler."""
    async with expect_raises_async(TypeError):
        await request_handler_factory(
            mock_request.app[KEY_HASS],
            Mock(requires_auth=False),
            AsyncMock(return_value=["not valid"]),
        )(mock_request)


@test
async def requires_auth_includes_www_authenticate(
    mock_request: Mock = Depends(mock_request),
) -> None:
    """Test that 401 responses include WWW-Authenticate header per RFC9728."""
    mock_request.get = Mock(return_value=False)
    raised: HTTPUnauthorized | None = None
    with patch(
        "homeassistant.helpers.network.get_url",
        return_value="https://example.com",
    ):
        try:
            await request_handler_factory(
                mock_request.app[KEY_HASS],
                Mock(requires_auth=True),
                AsyncMock(),
            )(mock_request)
        except HTTPUnauthorized as exc:
            raised = exc
    expect(raised).not_.to_be_none()
    expect(raised.headers["WWW-Authenticate"]).to_equal(
        "Bearer resource_metadata="
        '"https://example.com/.well-known/oauth-protected-resource"'
    )


@test
async def requires_auth_omits_www_authenticate_without_url(
    mock_request: Mock = Depends(mock_request),
) -> None:
    """Test that 401 responses omit WWW-Authenticate header when no URL is configured."""
    mock_request.get = Mock(return_value=False)
    raised: HTTPUnauthorized | None = None
    with patch(
        "homeassistant.helpers.network.get_url",
        side_effect=NoURLAvailableError,
    ):
        try:
            await request_handler_factory(
                mock_request.app[KEY_HASS],
                Mock(requires_auth=True),
                AsyncMock(),
            )(mock_request)
        except HTTPUnauthorized as exc:
            raised = exc
    expect(raised).not_.to_be_none()
    expect("WWW-Authenticate" not in raised.headers).to_be(True)
