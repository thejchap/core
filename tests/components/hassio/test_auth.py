"""The tests for the hassio component."""

from http import HTTPStatus
from unittest.mock import Mock, patch

from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant.auth.providers.homeassistant import InvalidAuth

from ._fixtures import (
    hassio_client,
    hassio_client_supervisor,
    hassio_noauth_client,
)


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def auth_success(
    hassio_client_supervisor: TestClient = Depends(hassio_client_supervisor),
) -> None:
    """Test no auth needed for ."""
    with patch(
        "homeassistant.auth.providers.homeassistant."
        "HassAuthProvider.async_validate_login",
    ) as mock_login:
        resp = await hassio_client_supervisor.post(
            "/api/hassio_auth",
            json={"username": "test", "password": "123456", "addon": "samba"},
        )

        expect(resp.status).to_equal(HTTPStatus.OK)
        mock_login.assert_called_with("test", "123456")


@test
async def auth_fails_no_supervisor(
    hassio_client: TestClient = Depends(hassio_client),
) -> None:
    """Test if only supervisor can access."""
    with patch(
        "homeassistant.auth.providers.homeassistant."
        "HassAuthProvider.async_validate_login",
    ) as mock_login:
        resp = await hassio_client.post(
            "/api/hassio_auth",
            json={"username": "test", "password": "123456", "addon": "samba"},
        )

        expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
        expect(mock_login.called).to_equal(False)


@test
async def auth_fails_no_auth(
    hassio_noauth_client: TestClient = Depends(hassio_noauth_client),
) -> None:
    """Test if only supervisor can access."""
    with patch(
        "homeassistant.auth.providers.homeassistant."
        "HassAuthProvider.async_validate_login",
    ) as mock_login:
        resp = await hassio_noauth_client.post(
            "/api/hassio_auth",
            json={"username": "test", "password": "123456", "addon": "samba"},
        )

        expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)
        expect(mock_login.called).to_equal(False)


@test
async def login_error(
    hassio_client_supervisor: TestClient = Depends(hassio_client_supervisor),
) -> None:
    """Test no auth needed for error."""
    with patch(
        "homeassistant.auth.providers.homeassistant."
        "HassAuthProvider.async_validate_login",
        Mock(side_effect=InvalidAuth()),
    ) as mock_login:
        resp = await hassio_client_supervisor.post(
            "/api/hassio_auth",
            json={"username": "test", "password": "123456", "addon": "samba"},
        )

        expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)
        mock_login.assert_called_with("test", "123456")


@test
async def login_no_data(
    hassio_client_supervisor: TestClient = Depends(hassio_client_supervisor),
) -> None:
    """Test auth with no data -> error."""
    with patch(
        "homeassistant.auth.providers.homeassistant."
        "HassAuthProvider.async_validate_login",
        Mock(side_effect=InvalidAuth()),
    ) as mock_login:
        resp = await hassio_client_supervisor.post("/api/hassio_auth")

        expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
        expect(mock_login.called).to_equal(False)


@test
async def login_no_username(
    hassio_client_supervisor: TestClient = Depends(hassio_client_supervisor),
) -> None:
    """Test auth with no username in data -> error."""
    with patch(
        "homeassistant.auth.providers.homeassistant."
        "HassAuthProvider.async_validate_login",
        Mock(side_effect=InvalidAuth()),
    ) as mock_login:
        resp = await hassio_client_supervisor.post(
            "/api/hassio_auth", json={"password": "123456", "addon": "samba"}
        )

        expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
        expect(mock_login.called).to_equal(False)


@test
async def login_success_extra(
    hassio_client_supervisor: TestClient = Depends(hassio_client_supervisor),
) -> None:
    """Test auth with extra data."""
    with patch(
        "homeassistant.auth.providers.homeassistant."
        "HassAuthProvider.async_validate_login",
    ) as mock_login:
        resp = await hassio_client_supervisor.post(
            "/api/hassio_auth",
            json={
                "username": "test",
                "password": "123456",
                "addon": "samba",
                "path": "/share",
            },
        )

        expect(resp.status).to_equal(HTTPStatus.OK)
        mock_login.assert_called_with("test", "123456")


@test
async def password_success(
    hassio_client_supervisor: TestClient = Depends(hassio_client_supervisor),
) -> None:
    """Test no auth needed for ."""
    with patch(
        "homeassistant.auth.providers.homeassistant."
        "HassAuthProvider.async_change_password",
    ) as mock_change:
        resp = await hassio_client_supervisor.post(
            "/api/hassio_auth/password_reset",
            json={"username": "test", "password": "123456"},
        )

        expect(resp.status).to_equal(HTTPStatus.OK)
        mock_change.assert_called_with("test", "123456")


@test
async def password_fails_no_supervisor(
    hassio_client: TestClient = Depends(hassio_client),
) -> None:
    """Test if only supervisor can access."""
    resp = await hassio_client.post(
        "/api/hassio_auth/password_reset",
        json={"username": "test", "password": "123456"},
    )

    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)


@test
async def password_fails_no_auth(
    hassio_noauth_client: TestClient = Depends(hassio_noauth_client),
) -> None:
    """Test if only supervisor can access."""
    resp = await hassio_noauth_client.post(
        "/api/hassio_auth/password_reset",
        json={"username": "test", "password": "123456"},
    )

    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)


@test
async def password_no_user(
    hassio_client_supervisor: TestClient = Depends(hassio_client_supervisor),
) -> None:
    """Test changing password for invalid user."""
    resp = await hassio_client_supervisor.post(
        "/api/hassio_auth/password_reset",
        json={"username": "test", "password": "123456"},
    )

    expect(resp.status).to_equal(HTTPStatus.NOT_FOUND)
