"""Tests for the HTTP API for the cloud component."""

from copy import deepcopy
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from hass_nabucasa import AlreadyConnectedError
from hass_nabucasa.auth import (
    InvalidTotpCode,
    MFARequired,
    Unauthenticated,
    UnknownError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.assist_pipeline.pipeline import (  # pylint: disable=hass-component-root-import
    STORAGE_KEY,
)
from homeassistant.components.cloud.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import cloud as cloud_fixture, load_homeassistant

from tests.hass_fixtures import (
    ClientSessionGenerator,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    hass_storage as hass_storage_fixture,
    mock_network,
)

PIPELINE_DATA_LEGACY = {
    "items": [
        {
            "conversation_engine": "homeassistant",
            "conversation_language": "language_1",
            "id": "12345",
            "language": "language_1",
            "name": "Home Assistant Cloud",
            "stt_engine": "cloud",
            "stt_language": "language_1",
            "tts_engine": "cloud",
            "tts_language": "language_1",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": None,
            "wake_word_id": None,
        },
    ],
    "preferred_item": "12345",
}

PIPELINE_DATA = {
    "items": [
        {
            "conversation_engine": "homeassistant",
            "conversation_language": "language_1",
            "id": "12345",
            "language": "language_1",
            "name": "Home Assistant Cloud",
            "stt_engine": "stt.home_assistant_cloud",
            "stt_language": "language_1",
            "tts_engine": "cloud",
            "tts_language": "language_1",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": None,
            "wake_word_id": None,
        },
    ],
    "preferred_item": "12345",
}

PIPELINE_DATA_OTHER = {
    "items": [
        {
            "conversation_engine": "other",
            "conversation_language": "language_1",
            "id": "12345",
            "language": "language_1",
            "name": "Home Assistant",
            "stt_engine": "stt.other",
            "stt_language": "language_1",
            "tts_engine": "other",
            "tts_language": "language_1",
            "tts_voice": "Arnold Schwarzenegger",
            "wake_word_entity": None,
            "wake_word_id": None,
        },
    ],
    "preferred_item": "12345",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _load_homeassistant: None = Depends(load_homeassistant),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@fixture
async def setup_cloud(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud: MagicMock = Depends(cloud_fixture),
) -> MagicMock:
    """Fixture that sets up cloud."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "mode": "development",
                "cognito_client_id": "cognito_client_id",
                "user_pool_id": "user_pool_id",
                "region": "region",
                "relayer_server": "relayer",
                "acme_server": "cert-server",
                "api_server": "api-test.example.com",
                "google_actions": {"filter": {"include_domains": "light"}},
                "alexa": {
                    "filter": {"include_entities": ["light.kitchen", "switch.ac"]}
                },
            },
        },
    )
    await hass.async_block_till_done()
    await cloud.login("test-user", "test-pass")
    cloud.login.reset_mock()
    return cloud


@test
async def google_actions_sync(
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    cloud: MagicMock = Depends(cloud_fixture),
) -> None:
    """Test syncing Google Actions."""
    cloud_client = await hass_client()

    cloud.google_report_state.request_sync = AsyncMock(
        return_value=Mock(status=HTTPStatus.OK)
    )

    req = await cloud_client.post("/api/cloud/google_actions/sync")
    expect(req.status).to_equal(HTTPStatus.OK)
    expect(cloud.google_report_state.request_sync.mock_calls).to_have_length(1)


@test
async def google_actions_sync_fails(
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    cloud: MagicMock = Depends(cloud_fixture),
) -> None:
    """Test syncing Google Actions gone bad."""
    cloud_client = await hass_client()
    cloud.google_report_state.request_sync = AsyncMock(
        return_value=Mock(status=HTTPStatus.INTERNAL_SERVER_ERROR)
    )

    req = await cloud_client.post("/api/cloud/google_actions/sync")
    expect(req.status).to_equal(HTTPStatus.INTERNAL_SERVER_ERROR)
    expect(cloud.google_report_state.request_sync.mock_calls).to_have_length(1)


@test.cases(
    test.case("stt", entity_id="stt.home_assistant_cloud"),
    test.case("tts", entity_id="tts.home_assistant_cloud"),
)
async def login_view_missing_entity(
    entity_id: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test logging in when a cloud assist pipeline needed entity is missing."""
    entity_registry.async_remove(entity_id)
    await hass.async_block_till_done()

    cloud_client = await hass_client()

    with patch(
        "homeassistant.components.cloud.assist_pipeline.async_create_default_pipeline",
    ) as create_pipeline_mock:
        req = await cloud_client.post(
            "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
        )

    expect(req.status).to_equal(HTTPStatus.OK)
    result = await req.json()
    expect(result).to_equal({"success": True, "cloud_pipeline": None})
    create_pipeline_mock.assert_not_awaited()


@test.cases(
    test.case("modern", pipeline_data=PIPELINE_DATA),
    test.case("legacy", pipeline_data=PIPELINE_DATA_LEGACY),
)
async def login_view_existing_pipeline(
    pipeline_data: dict[str, Any],
    hass: HomeAssistant = Depends(hass_fixture),
    cloud: MagicMock = Depends(cloud_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test logging in when an assist pipeline is available."""
    hass_storage[STORAGE_KEY] = {
        "version": 1,
        "minor_version": 1,
        "key": STORAGE_KEY,
        "data": deepcopy(pipeline_data),
    }

    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    expect(await async_setup_component(hass, DOMAIN, {"cloud": {}})).to_be(True)
    await hass.async_block_till_done()

    cloud_client = await hass_client()

    with patch(
        "homeassistant.components.cloud.assist_pipeline.async_create_default_pipeline",
    ) as create_pipeline_mock:
        req = await cloud_client.post(
            "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
        )

    expect(req.status).to_equal(HTTPStatus.OK)
    result = await req.json()
    expect(result).to_equal({"success": True, "cloud_pipeline": None})
    create_pipeline_mock.assert_not_awaited()


@test
async def login_view_create_pipeline(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud: MagicMock = Depends(cloud_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test logging in when no existing cloud assist pipeline is available."""
    hass_storage[STORAGE_KEY] = {
        "version": 1,
        "minor_version": 1,
        "key": STORAGE_KEY,
        "data": deepcopy(PIPELINE_DATA_OTHER),
    }

    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    expect(await async_setup_component(hass, "assist_pipeline", {})).to_be(True)
    expect(await async_setup_component(hass, DOMAIN, {"cloud": {}})).to_be(True)
    await hass.async_block_till_done()

    cloud_client = await hass_client()

    with patch(
        "homeassistant.components.cloud.assist_pipeline.async_create_default_pipeline",
        return_value=AsyncMock(id="12345"),
    ) as create_pipeline_mock:
        req = await cloud_client.post(
            "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
        )

    expect(req.status).to_equal(HTTPStatus.OK)
    result = await req.json()
    expect(result).to_equal({"success": True, "cloud_pipeline": "12345"})
    create_pipeline_mock.assert_awaited_once_with(
        hass,
        stt_engine_id="stt.home_assistant_cloud",
        tts_engine_id="tts.home_assistant_cloud",
        pipeline_name="Home Assistant Cloud",
    )


@test
async def login_view_create_pipeline_fail(
    hass: HomeAssistant = Depends(hass_fixture),
    cloud: MagicMock = Depends(cloud_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test logging in when no assist pipeline is available."""
    hass_storage[STORAGE_KEY] = {
        "version": 1,
        "minor_version": 1,
        "key": STORAGE_KEY,
        "data": deepcopy(PIPELINE_DATA_OTHER),
    }

    expect(await async_setup_component(hass, "homeassistant", {})).to_be(True)
    expect(await async_setup_component(hass, "assist_pipeline", {})).to_be(True)
    expect(await async_setup_component(hass, DOMAIN, {"cloud": {}})).to_be(True)
    await hass.async_block_till_done()

    cloud_client = await hass_client()

    with patch(
        "homeassistant.components.cloud.assist_pipeline.async_create_default_pipeline",
        return_value=None,
    ) as create_pipeline_mock:
        req = await cloud_client.post(
            "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
        )

    expect(req.status).to_equal(HTTPStatus.OK)
    result = await req.json()
    expect(result).to_equal({"success": True, "cloud_pipeline": None})
    create_pipeline_mock.assert_awaited_once_with(
        hass,
        stt_engine_id="stt.home_assistant_cloud",
        tts_engine_id="tts.home_assistant_cloud",
        pipeline_name="Home Assistant Cloud",
    )


@test
async def login_view_random_exception(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Try logging in with random exception."""
    cloud_client = await hass_client()
    cloud.login.side_effect = ValueError("Boom")

    req = await cloud_client.post(
        "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
    )

    expect(req.status).to_equal(HTTPStatus.BAD_GATEWAY)
    resp = await req.json()
    expect(resp).to_equal({"code": "valueerror", "message": "Unexpected error: Boom"})


@test
async def login_view_invalid_json(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Try logging in with invalid JSON."""
    cloud_client = await hass_client()
    mock_login = cloud.login

    req = await cloud_client.post("/api/cloud/login", data="Not JSON")

    expect(req.status).to_equal(HTTPStatus.BAD_REQUEST)
    expect(mock_login.call_count).to_equal(0)


@test
async def login_view_invalid_schema(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Try logging in with invalid schema."""
    cloud_client = await hass_client()
    mock_login = cloud.login

    req = await cloud_client.post("/api/cloud/login", json={"invalid": "schema"})

    expect(req.status).to_equal(HTTPStatus.BAD_REQUEST)
    expect(mock_login.call_count).to_equal(0)


@test
async def login_view_request_timeout(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test request timeout while trying to log in."""
    cloud_client = await hass_client()
    cloud.login.side_effect = TimeoutError

    req = await cloud_client.post(
        "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
    )

    expect(cloud.login.call_args[1]["check_connection"]).to_be(False)
    expect(req.status).to_equal(HTTPStatus.BAD_GATEWAY)


@test
async def login_view_with_already_existing_connection(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test request timeout while trying to log in."""
    cloud_client = await hass_client()
    cloud.login.side_effect = AlreadyConnectedError(
        details={"remote_ip_address": "127.0.0.1", "connected_at": "1"}
    )

    req = await cloud_client.post(
        "/api/cloud/login",
        json={
            "email": "my_username",
            "password": "my_password",
            "check_connection": True,
        },
    )

    expect(cloud.login.call_args[1]["check_connection"]).to_be(True)
    expect(req.status).to_equal(HTTPStatus.CONFLICT)
    resp = await req.json()
    expect(resp).to_equal(
        {
            "code": "alreadyconnectederror",
            "message": '{"remote_ip_address": "127.0.0.1", "connected_at": "1"}',
        }
    )


@test
async def login_view_invalid_credentials(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test logging in with invalid credentials."""
    cloud_client = await hass_client()
    cloud.login.side_effect = Unauthenticated

    req = await cloud_client.post(
        "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
    )

    expect(req.status).to_equal(HTTPStatus.UNAUTHORIZED)


@test
async def login_view_mfa_required(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test logging in when MFA is required."""
    cloud_client = await hass_client()
    cloud.login.side_effect = MFARequired(mfa_tokens={"session": "tokens"})

    req = await cloud_client.post(
        "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
    )

    expect(req.status).to_equal(HTTPStatus.UNAUTHORIZED)
    res = await req.json()
    expect(res["code"]).to_equal("mfarequired")


@test
async def login_view_mfa_required_tokens_missing(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test logging in when MFA is required, code is provided, but session tokens are missing."""
    cloud_client = await hass_client()
    cloud.login.side_effect = MFARequired(mfa_tokens={})

    req = await cloud_client.post(
        "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
    )

    expect(req.status).to_equal(HTTPStatus.UNAUTHORIZED)
    res = await req.json()
    expect(res["code"]).to_equal("mfarequired")

    req = await cloud_client.post(
        "/api/cloud/login",
        json={"email": "my_username", "code": "123346"},
    )

    expect(req.status).to_equal(HTTPStatus.BAD_REQUEST)
    res = await req.json()
    expect(res["code"]).to_equal("mfaexpiredornotstarted")


@test
async def login_view_mfa_password_and_totp_provided(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test logging in when password and TOTP code provided at once."""
    cloud_client = await hass_client()

    req = await cloud_client.post(
        "/api/cloud/login",
        json={"email": "my_username", "password": "my_password", "code": "123346"},
    )

    expect(req.status).to_equal(HTTPStatus.BAD_REQUEST)


@test
async def login_view_invalid_totp_code(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test logging in when MFA is required and invalid code is provided."""
    cloud_client = await hass_client()
    cloud.login.side_effect = MFARequired(mfa_tokens={"session": "tokens"})
    cloud.login_verify_totp.side_effect = InvalidTotpCode

    req = await cloud_client.post(
        "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
    )

    expect(req.status).to_equal(HTTPStatus.UNAUTHORIZED)
    res = await req.json()
    expect(res["code"]).to_equal("mfarequired")

    req = await cloud_client.post(
        "/api/cloud/login",
        json={"email": "my_username", "code": "123346"},
    )

    expect(req.status).to_equal(HTTPStatus.BAD_REQUEST)
    res = await req.json()
    expect(res["code"]).to_equal("invalidtotpcode")


@test
async def login_view_valid_totp_provided(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test logging in with valid TOTP code."""
    cloud_client = await hass_client()
    cloud.login.side_effect = MFARequired(mfa_tokens={"session": "tokens"})

    req = await cloud_client.post(
        "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
    )

    expect(req.status).to_equal(HTTPStatus.UNAUTHORIZED)
    res = await req.json()
    expect(res["code"]).to_equal("mfarequired")

    req = await cloud_client.post(
        "/api/cloud/login",
        json={"email": "my_username", "code": "123346"},
    )

    expect(req.status).to_equal(HTTPStatus.OK)
    result = await req.json()
    expect(result).to_equal({"success": True, "cloud_pipeline": None})


@test
async def login_view_unknown_error(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test unknown error while logging in."""
    cloud_client = await hass_client()
    cloud.login.side_effect = UnknownError

    req = await cloud_client.post(
        "/api/cloud/login", json={"email": "my_username", "password": "my_password"}
    )

    expect(req.status).to_equal(HTTPStatus.BAD_GATEWAY)


@test
async def logout_view(
    cloud: MagicMock = Depends(cloud_fixture),
    _setup_cloud: MagicMock = Depends(setup_cloud),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test logging out."""
    cloud_client = await hass_client()
    req = await cloud_client.post("/api/cloud/logout")

    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    expect(data).to_equal({"message": "ok"})
    expect(cloud.logout.call_count).to_equal(1)
