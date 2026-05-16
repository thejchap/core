"""Integration tests for the auth component."""

from datetime import timedelta
from http import HTTPStatus
import logging
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.auth import InvalidAuthError
from homeassistant.auth.models import (
    TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
    TOKEN_TYPE_NORMAL,
    Credentials,
    RefreshToken,
)
from homeassistant.components import auth
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow

from . import async_setup_auth
from ._fixtures import aiohttp_client as aiohttp_client_fx

from tests.common import CLIENT_ID, CLIENT_REDIRECT_URI, MockUser
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
    freezer as freezer_fx,
    hass as hass_fx,
    hass_access_token as hass_access_token_fx,
    hass_admin_credential as hass_admin_credential_fx,
    hass_admin_user as hass_admin_user_fx,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)
from tests.typing import ClientSessionGenerator, WebSocketGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_credential() -> Credentials:
    """Return a mock credential."""
    return Credentials(
        id="mock-credential-id",
        auth_provider_type="insecure_example",
        auth_provider_id=None,
        data={"username": "test-user"},
        is_new=False,
    )


async def async_setup_user_refresh_token(hass: HomeAssistant) -> RefreshToken:
    """Create a testing user with a connected credential."""
    user = await hass.auth.async_create_user("Test User")

    credential = Credentials(
        id="mock-credential-id",
        auth_provider_type="insecure_example",
        auth_provider_id=None,
        data={"username": "test-user"},
        is_new=False,
    )
    user.credentials.append(credential)

    return await hass.auth.async_create_refresh_token(
        user, CLIENT_ID, credential=credential
    )


@test
async def login_new_user_and_trying_refresh_token(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test logging in with new user and refreshing tokens."""
    client = await async_setup_auth(hass, aiohttp_client, setup_api=True)
    resp = await client.post(
        "/auth/login_flow",
        json={
            "client_id": CLIENT_ID,
            "handler": ["insecure_example", None],
            "redirect_uri": CLIENT_REDIRECT_URI,
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()

    resp = await client.post(
        f"/auth/login_flow/{step['flow_id']}",
        json={
            "client_id": CLIENT_ID,
            "username": "test-user",
            "password": "test-pass",
        },
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()
    code = step["result"]

    # Exchange code for tokens
    resp = await client.post(
        "/auth/token",
        data={"client_id": CLIENT_ID, "grant_type": "authorization_code", "code": code},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    tokens = await resp.json()

    expect(hass.auth.async_validate_access_token(tokens["access_token"])).not_.to_be_none()
    expect(tokens["ha_auth_provider"]).to_equal("insecure_example")

    # Use refresh token to get more tokens.
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        },
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    tokens = await resp.json()
    expect("refresh_token" in tokens).to_be_falsy()
    expect(hass.auth.async_validate_access_token(tokens["access_token"])).not_.to_be_none()

    # Test using access token to hit API.
    resp = await client.get("/api/")
    expect(resp.status).to_equal(HTTPStatus.UNAUTHORIZED)

    resp = await client.get(
        "/api/", headers={"authorization": f"Bearer {tokens['access_token']}"}
    )
    expect(resp.status).to_equal(HTTPStatus.OK)


@test
async def auth_code_checks_local_only_user(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test local only user cannot exchange auth code for refresh tokens when external."""
    client = await async_setup_auth(hass, aiohttp_client, setup_api=True)
    resp = await client.post(
        "/auth/login_flow",
        json={
            "client_id": CLIENT_ID,
            "handler": ["insecure_example", None],
            "redirect_uri": CLIENT_REDIRECT_URI,
        },
    )
    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()

    resp = await client.post(
        f"/auth/login_flow/{step['flow_id']}",
        json={
            "client_id": CLIENT_ID,
            "username": "test-user",
            "password": "test-pass",
        },
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    step = await resp.json()
    code = step["result"]

    # Exchange code for tokens
    with patch(
        "homeassistant.components.auth.async_user_not_allowed_do_auth",
        return_value="User is local only",
    ):
        resp = await client.post(
            "/auth/token",
            data={
                "client_id": CLIENT_ID,
                "grant_type": "authorization_code",
                "code": code,
            },
        )

    expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)
    error = await resp.json()
    expect(error["error"]).to_equal("access_denied")


@test
def auth_code_store_expiration(
    mock_credential: Credentials = Depends(mock_credential),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test that the auth code store will not return expired tokens."""
    store, retrieve = auth._create_auth_code_store()
    client_id = "bla"
    now = utcnow()

    freezer.move_to(now)
    code = store(client_id, mock_credential)

    freezer.move_to(now + timedelta(minutes=10))
    expect(retrieve(client_id, code)).to_be_none()

    freezer.move_to(now)
    code = store(client_id, mock_credential)

    freezer.move_to(now + timedelta(minutes=9, seconds=59))
    expect(retrieve(client_id, code)).to_equal(mock_credential)


@test
def auth_code_store_requires_credentials(
    mock_credential: Credentials = Depends(mock_credential),
) -> None:
    """Test we require credentials."""
    store, _retrieve = auth._create_auth_code_store()

    expect(lambda: store(None, MockUser())).to_raise(TypeError)

    store(None, mock_credential)


@test
async def ws_current_user(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test the current user command with Home Assistant creds."""
    expect(await async_setup_component(hass, "auth", {})).to_be_truthy()

    refresh_token = hass.auth.async_validate_access_token(hass_access_token)
    user = refresh_token.user
    client = await hass_ws_client(hass, hass_access_token)

    await client.send_json({"id": 5, "type": "auth/current_user"})

    result = await client.receive_json()
    expect(result["success"]).to_be_truthy()

    user_dict = result["result"]

    expect(user_dict["name"]).to_equal(user.name)
    expect(user_dict["id"]).to_equal(user.id)
    expect(user_dict["is_owner"]).to_equal(user.is_owner)
    expect(len(user_dict["credentials"])).to_equal(1)

    hass_cred = user_dict["credentials"][0]
    expect(hass_cred["auth_provider_type"]).to_equal("homeassistant")
    expect(hass_cred["auth_provider_id"]).to_be_none()
    expect("data" in hass_cred).to_be_falsy()


@test
async def cors_on_token(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test logging in with new user and refreshing tokens."""
    client = await async_setup_auth(hass, aiohttp_client)

    resp = await client.options(
        "/auth/token",
        headers={
            "origin": "http://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    expect(resp.headers["Access-Control-Allow-Origin"]).to_equal("http://example.com")
    expect(resp.headers["Access-Control-Allow-Methods"]).to_equal("POST")

    resp = await client.post("/auth/token", headers={"origin": "http://example.com"})
    expect(resp.headers["Access-Control-Allow-Origin"]).to_equal("http://example.com")


@test
async def refresh_token_system_generated(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test that we can get access tokens for system generated user."""
    client = await async_setup_auth(hass, aiohttp_client)
    user = await hass.auth.async_create_system_user("Test System")
    refresh_token = await hass.auth.async_create_refresh_token(user, None)

    resp = await client.post(
        "/auth/token",
        data={
            "client_id": "https://this-is-not-allowed-for-system-users.com/",
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.token,
        },
    )

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    result = await resp.json()
    expect(result["error"]).to_equal("invalid_request")

    resp = await client.post(
        "/auth/token",
        data={"grant_type": "refresh_token", "refresh_token": refresh_token.token},
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    tokens = await resp.json()
    expect(hass.auth.async_validate_access_token(tokens["access_token"])).not_.to_be_none()


@test
async def refresh_token_different_client_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test that we verify client ID."""
    client = await async_setup_auth(hass, aiohttp_client)
    refresh_token = await async_setup_user_refresh_token(hass)

    # No client ID
    resp = await client.post(
        "/auth/token",
        data={"grant_type": "refresh_token", "refresh_token": refresh_token.token},
    )

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    result = await resp.json()
    expect(result["error"]).to_equal("invalid_request")

    # Different client ID
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": "http://example-different.com",
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.token,
        },
    )

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)
    result = await resp.json()
    expect(result["error"]).to_equal("invalid_request")

    # Correct
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.token,
        },
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    tokens = await resp.json()
    expect(hass.auth.async_validate_access_token(tokens["access_token"])).not_.to_be_none()


@test
async def refresh_token_checks_local_only_user(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test that we can't refresh token for a local only user when external."""
    client = await async_setup_auth(hass, aiohttp_client)
    refresh_token = await async_setup_user_refresh_token(hass)
    refresh_token.user.local_only = True

    with patch(
        "homeassistant.components.auth.async_user_not_allowed_do_auth",
        return_value="User is local only",
    ):
        resp = await client.post(
            "/auth/token",
            data={
                "client_id": CLIENT_ID,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token.token,
            },
        )

    expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)
    result = await resp.json()
    expect(result["error"]).to_equal("access_denied")


@test
async def refresh_token_provider_rejected(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    hass_admin_credential: Credentials = Depends(hass_admin_credential_fx),
) -> None:
    """Test that we verify client ID."""
    client = await async_setup_auth(hass, aiohttp_client)
    refresh_token = await async_setup_user_refresh_token(hass)

    # Rejected by provider
    with patch(
        "homeassistant.auth.providers.insecure_example.ExampleAuthProvider.async_validate_refresh_token",
        side_effect=InvalidAuthError("Invalid access"),
    ):
        resp = await client.post(
            "/auth/token",
            data={
                "client_id": CLIENT_ID,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token.token,
            },
        )

    expect(resp.status).to_equal(HTTPStatus.FORBIDDEN)
    result = await resp.json()
    expect(result["error"]).to_equal("access_denied")
    expect(result["error_description"]).to_equal("Invalid access")


@test.cases(
    test.case("token_revoke", url="/auth/token", base_data={"action": "revoke"}),
    test.case("revoke", url="/auth/revoke", base_data={}),
)
async def revoking_refresh_token(
    url: str,
    base_data: dict[str, str],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> None:
    """Test that we can revoke refresh tokens."""
    client = await async_setup_auth(hass, aiohttp_client)
    refresh_token = await async_setup_user_refresh_token(hass)

    # Test that we can create an access token
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.token,
        },
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    tokens = await resp.json()
    expect(hass.auth.async_validate_access_token(tokens["access_token"])).not_.to_be_none()

    # Revoke refresh token
    resp = await client.post(url, data={**base_data, "token": refresh_token.token})
    expect(resp.status).to_equal(HTTPStatus.OK)

    # Old access token should be no longer valid
    expect(hass.auth.async_validate_access_token(tokens["access_token"])).to_be_none()

    # Test that we no longer can create an access token
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token.token,
        },
    )

    expect(resp.status).to_equal(HTTPStatus.BAD_REQUEST)


@test
async def ws_long_lived_access_token(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test generate long-lived access token."""
    expect(await async_setup_component(hass, "auth", {"http": {}})).to_be_truthy()

    ws_client = await hass_ws_client(hass, hass_access_token)

    # verify create long-lived access token
    await ws_client.send_json(
        {
            "id": 5,
            "type": "auth/long_lived_access_token",
            "client_name": "GPS Logger",
            "lifespan": 365,
        }
    )

    result = await ws_client.receive_json()
    expect(result["success"]).to_be_truthy()

    long_lived_access_token = result["result"]
    expect(long_lived_access_token).not_.to_be_none()

    refresh_token = hass.auth.async_validate_access_token(long_lived_access_token)
    expect(refresh_token.client_id).to_be_none()
    expect(refresh_token.client_name).to_equal("GPS Logger")
    expect(refresh_token.client_icon).to_be_none()


@test
async def ws_refresh_tokens(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test fetching refresh token metadata."""
    expect(await async_setup_component(hass, "auth", {"http": {}})).to_be_truthy()

    ws_client = await hass_ws_client(hass, hass_access_token)

    await ws_client.send_json({"id": 5, "type": "auth/refresh_tokens"})

    result = await ws_client.receive_json()
    expect(result["success"]).to_be_truthy()
    expect(len(result["result"])).to_equal(1)
    token = result["result"][0]
    refresh_token = hass.auth.async_validate_access_token(hass_access_token)
    expect(token["id"]).to_equal(refresh_token.id)
    expect(token["type"]).to_equal(refresh_token.token_type)
    expect(token["client_id"]).to_equal(refresh_token.client_id)
    expect(token["client_name"]).to_equal(refresh_token.client_name)
    expect(token["client_icon"]).to_equal(refresh_token.client_icon)
    expect(token["created_at"]).to_equal(refresh_token.created_at.isoformat())
    expect(token["is_current"]).to_be(True)
    expect(token["last_used_at"]).to_equal(refresh_token.last_used_at.isoformat())
    expect(token["last_used_ip"]).to_equal(refresh_token.last_used_ip)
    expect(token["auth_provider_type"]).to_equal("homeassistant")


@test
async def ws_delete_refresh_token(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    hass_admin_credential: Credentials = Depends(hass_admin_credential_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test deleting a refresh token."""
    expect(await async_setup_component(hass, "auth", {"http": {}})).to_be_truthy()

    refresh_token = await hass.auth.async_create_refresh_token(
        hass_admin_user, CLIENT_ID, credential=hass_admin_credential
    )

    ws_client = await hass_ws_client(hass, hass_access_token)

    # verify create long-lived access token
    await ws_client.send_json(
        {
            "id": 5,
            "type": "auth/delete_refresh_token",
            "refresh_token_id": refresh_token.id,
        }
    )

    result = await ws_client.receive_json()
    expect(result["success"]).to_be_truthy()
    refresh_token = hass.auth.async_get_refresh_token(refresh_token.id)
    expect(refresh_token).to_be_none()


@test
async def ws_delete_all_refresh_tokens_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    hass_admin_credential: Credentials = Depends(hass_admin_credential_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test deleting all refresh tokens, where a revoke callback raises an error."""
    expect(await async_setup_component(hass, "auth", {"http": {}})).to_be_truthy()

    # one token already exists
    await hass.auth.async_create_refresh_token(
        hass_admin_user, CLIENT_ID, credential=hass_admin_credential
    )
    token = await hass.auth.async_create_refresh_token(
        hass_admin_user, CLIENT_ID + "_1", credential=hass_admin_credential
    )

    def cb():
        raise RuntimeError("I'm bad")

    hass.auth.async_register_revoke_token_callback(token.id, cb)

    ws_client = await hass_ws_client(hass, hass_access_token)

    # get all tokens
    await ws_client.send_json({"id": 5, "type": "auth/refresh_tokens"})
    result = await ws_client.receive_json()
    expect(result["success"]).to_be_truthy()

    tokens = result["result"]

    with patch("homeassistant.components.auth.DELETE_CURRENT_TOKEN_DELAY", 0.001):
        await ws_client.send_json(
            {
                "id": 6,
                "type": "auth/delete_all_refresh_tokens",
            }
        )

        caplog.clear()
        result = await ws_client.receive_json()
        expect(result["success"]).to_be_falsy()
        expect(result["error"]).to_equal(
            {
                "code": "token_removing_error",
                "message": "During removal, an error was raised.",
            }
        )

    records = [
        record
        for record in caplog.records
        if record.msg == "Error during refresh token removal"
    ]
    expect(len(records)).to_equal(1)
    expect(records[0].levelno).to_equal(logging.ERROR)
    expect(bool(records[0].exc_info)).to_be_truthy()
    expect(str(records[0].exc_info[1])).to_equal("I'm bad")
    expect(records[0].name).to_equal("homeassistant.components.auth")

    await hass.async_block_till_done()
    for token in tokens:
        refresh_token = hass.auth.async_get_refresh_token(token["id"])
        expect(refresh_token).to_be_none()


@test.cases(
    test.case(
        "delete_all",
        delete_token_type={},
        delete_current_token={},
        expected_remaining_normal_tokens=0,
        expected_remaining_long_lived_tokens=0,
    ),
    test.case(
        "delete_long_lived",
        delete_token_type={"token_type": TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN},
        delete_current_token={},
        expected_remaining_normal_tokens=3,
        expected_remaining_long_lived_tokens=0,
    ),
    test.case(
        "delete_normal",
        delete_token_type={"token_type": TOKEN_TYPE_NORMAL},
        delete_current_token={},
        expected_remaining_normal_tokens=0,
        expected_remaining_long_lived_tokens=1,
    ),
    test.case(
        "delete_normal_keep_current",
        delete_token_type={"token_type": TOKEN_TYPE_NORMAL},
        delete_current_token={"delete_current_token": False},
        expected_remaining_normal_tokens=1,
        expected_remaining_long_lived_tokens=1,
    ),
)
async def ws_delete_all_refresh_tokens(
    delete_token_type: dict[str, str],
    delete_current_token: dict[str, bool],
    expected_remaining_normal_tokens: int,
    expected_remaining_long_lived_tokens: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    hass_admin_credential: Credentials = Depends(hass_admin_credential_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test deleting all or some refresh tokens."""
    expect(await async_setup_component(hass, "auth", {"http": {}})).to_be_truthy()

    # one token already exists
    await hass.auth.async_create_refresh_token(
        hass_admin_user, CLIENT_ID, credential=hass_admin_credential
    )

    # create a long lived token
    await hass.auth.async_create_refresh_token(
        hass_admin_user,
        f"{CLIENT_ID}_LL",
        client_name="client_ll",
        credential=hass_admin_credential,
        token_type=TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN,
    )

    await hass.auth.async_create_refresh_token(
        hass_admin_user, f"{CLIENT_ID}_1", credential=hass_admin_credential
    )

    ws_client = await hass_ws_client(hass, hass_access_token)

    # get all tokens
    await ws_client.send_json({"id": 5, "type": "auth/refresh_tokens"})
    result = await ws_client.receive_json()
    expect(result["success"]).to_be_truthy()

    with patch("homeassistant.components.auth.DELETE_CURRENT_TOKEN_DELAY", 0.001):
        await ws_client.send_json(
            {
                "id": 6,
                "type": "auth/delete_all_refresh_tokens",
                **delete_token_type,
                **delete_current_token,
            }
        )

        result = await ws_client.receive_json()
        expect(result["success"]).to_be_truthy()

    await hass.async_block_till_done()
    # We need to enumerate the user since we may remove the token
    # that is used to authenticate the user which will prevent the websocket
    # connection from working
    remaining_tokens_by_type: dict[str, int] = {
        TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN: 0,
        TOKEN_TYPE_NORMAL: 0,
    }
    for refresh_token in hass_admin_user.refresh_tokens.values():
        remaining_tokens_by_type[refresh_token.token_type] += 1

    expect(remaining_tokens_by_type[TOKEN_TYPE_LONG_LIVED_ACCESS_TOKEN]).to_equal(
        expected_remaining_long_lived_tokens
    )
    expect(remaining_tokens_by_type[TOKEN_TYPE_NORMAL]).to_equal(
        expected_remaining_normal_tokens
    )


@test
async def ws_sign_path(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test signing a path."""
    expect(await async_setup_component(hass, "auth", {"http": {}})).to_be_truthy()
    ws_client = await hass_ws_client(hass, hass_access_token)

    with patch(
        "homeassistant.components.auth.async_sign_path", return_value="hello_world"
    ) as mock_sign:
        await ws_client.send_json(
            {
                "id": 5,
                "type": "auth/sign_path",
                "path": "/api/hello",
                "expires": 20,
            }
        )

        result = await ws_client.receive_json()
    expect(result["success"]).to_be_truthy()
    expect(result["result"]).to_equal({"path": "hello_world"})
    expect(len(mock_sign.mock_calls)).to_equal(1)
    _hass, path, expires = mock_sign.mock_calls[0][1]
    expect(path).to_equal("/api/hello")
    expect(expires.total_seconds()).to_equal(20)


@test
async def ws_refresh_token_set_expiry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    hass_admin_credential: Credentials = Depends(hass_admin_credential_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test setting expiry of a refresh token."""
    expect(await async_setup_component(hass, "auth", {"http": {}})).to_be_truthy()

    refresh_token = await hass.auth.async_create_refresh_token(
        hass_admin_user, CLIENT_ID, credential=hass_admin_credential
    )
    expect(refresh_token.expire_at).not_.to_be_none()
    ws_client = await hass_ws_client(hass, hass_access_token)

    await ws_client.send_json_auto_id(
        {
            "type": "auth/refresh_token_set_expiry",
            "refresh_token_id": refresh_token.id,
            "enable_expiry": False,
        }
    )

    result = await ws_client.receive_json()
    expect(result["success"]).to_be_truthy()
    refresh_token = hass.auth.async_get_refresh_token(refresh_token.id)
    expect(refresh_token.expire_at).to_be_none()

    await ws_client.send_json_auto_id(
        {
            "type": "auth/refresh_token_set_expiry",
            "refresh_token_id": refresh_token.id,
            "enable_expiry": True,
        }
    )

    result = await ws_client.receive_json()
    expect(result["success"]).to_be_truthy()
    refresh_token = hass.auth.async_get_refresh_token(refresh_token.id)
    expect(refresh_token.expire_at).not_.to_be_none()


@test
async def ws_refresh_token_set_expiry_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_access_token: str = Depends(hass_access_token_fx),
) -> None:
    """Test setting expiry of a invalid refresh token returns error."""
    expect(await async_setup_component(hass, "auth", {"http": {}})).to_be_truthy()

    ws_client = await hass_ws_client(hass, hass_access_token)

    await ws_client.send_json_auto_id(
        {
            "type": "auth/refresh_token_set_expiry",
            "refresh_token_id": "invalid",
            "enable_expiry": False,
        }
    )

    result = await ws_client.receive_json()
    expect(result["success"]).to_be_falsy()
    expect(result["error"]).to_equal(
        {
            "code": "invalid_token_id",
            "message": "Received invalid token",
        }
    )
