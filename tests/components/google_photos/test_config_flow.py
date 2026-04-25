"""Test the Google Photos config flow."""

from typing import Any
from unittest.mock import Mock

from google_photos_library_api.exceptions import GooglePhotosApiError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.google_photos.const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    EXPIRES_IN,
    FAKE_ACCESS_TOKEN,
    FAKE_REFRESH_TOKEN,
    USER_IDENTIFIER,
    mock_api,
    mock_patch_api,
    mock_setup,
    setup_credentials,
    token_entry,
)

from tests.hass_fixtures import (
    ClientSessionGenerator,
    aioclient_mock as aioclient_mock_fixture,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _credentials: None = Depends(setup_credentials),
    _request: None = Depends(current_request_with_host),
    _patch_api: None = Depends(mock_patch_api),
) -> None:
    """Apply autouse-equivalent fixtures."""


@fixture
def mock_oauth_token_request(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    token_data: dict[str, Any] = Depends(token_entry),
) -> None:
    """Provide a fake response from the oauth token endpoint."""
    aioclient_mock.clear_requests()
    aioclient_mock.post(OAUTH2_TOKEN, json=token_data)


@test.cases(test.case("list_mediaitems", fixture_name="list_mediaitems.json"))
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    setup_mock: Mock = Depends(mock_setup),
    _api: Mock = Depends(mock_api),
    _token: None = Depends(mock_oauth_token_request),
    *,
    fixture_name: str,
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        "&scope=https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata"
        "+https://www.googleapis.com/auth/photoslibrary.appendonly"
        "+https://www.googleapis.com/auth/userinfo.profile"
        "&access_type=offline&prompt=consent"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    config_entry = result["result"]
    expect(config_entry.unique_id).to_equal(USER_IDENTIFIER)
    expect(config_entry.title).to_equal("Test Name")
    config_entry_data = dict(config_entry.data)
    expect("token" in config_entry_data).to_be(True)
    expect("expires_at" in config_entry_data["token"]).to_be(True)
    del config_entry_data["token"]["expires_at"]
    expect(config_entry_data).to_equal(
        {
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": FAKE_ACCESS_TOKEN,
                "expires_in": EXPIRES_IN,
                "refresh_token": FAKE_REFRESH_TOKEN,
                "type": "Bearer",
                "scope": (
                    "https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata"
                    " https://www.googleapis.com/auth/photoslibrary.appendonly"
                    " https://www.googleapis.com/auth/userinfo.profile"
                ),
            },
        }
    )
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(setup_mock.mock_calls)).to_equal(1)


@fixture
def api_error_value() -> Exception:
    """Provide a GooglePhotosApiError."""
    return GooglePhotosApiError("some error")


@test
async def api_not_enabled(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    api: Mock = Depends(mock_api),
    _token: None = Depends(mock_oauth_token_request),
) -> None:
    """Check flow aborts if api is not enabled."""
    api.list_media_items.side_effect = GooglePhotosApiError("some error")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        "&scope=https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata"
        "+https://www.googleapis.com/auth/photoslibrary.appendonly"
        "+https://www.googleapis.com/auth/userinfo.profile"
        "&access_type=offline&prompt=consent"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("access_not_configured")
    expect(result["description_placeholders"]["message"].endswith("some error")).to_be(
        True
    )


@test
async def general_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    api: Mock = Depends(mock_api),
    _token: None = Depends(mock_oauth_token_request),
) -> None:
    """Check flow aborts if exception happens."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        "&scope=https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata"
        "+https://www.googleapis.com/auth/photoslibrary.appendonly"
        "+https://www.googleapis.com/auth/userinfo.profile"
        "&access_type=offline&prompt=consent"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    api.list_media_items.side_effect = Exception

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test.skip("requires complex setup_integration parametrization")
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the re-authentication case updates the correct config entry."""
