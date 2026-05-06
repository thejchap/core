"""Test the Google Drive config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from google_drive_api.exceptions import GoogleDriveApiError
from tryke import Depends, expect, fixture, test

from homeassistant.components.google_drive.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    CLIENT_ID,
    TEST_USER_EMAIL,
    config_entry as config_entry_fx,
    mock_api,
    mock_instance_id,
    setup_credentials,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    aioclient_mock as aioclient_mock_fx,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
FOLDER_ID = "google-folder-id"
FOLDER_NAME = "folder name"
TITLE = "Google Drive"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _request: None = Depends(current_request_with_host),
    _credentials: None = Depends(setup_credentials),
    _instance: None = Depends(mock_instance_id),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "&access_type=offline&prompt=consent"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    api.get_user = AsyncMock(
        return_value={"user": {"emailAddress": TEST_USER_EMAIL}}
    )
    api.list_files = AsyncMock(return_value={"files": []})
    api.create_file = AsyncMock(return_value={"id": FOLDER_ID, "name": FOLDER_NAME})

    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.google_drive.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(aioclient_mock.mock_calls)).to_equal(1)

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(TITLE)
    expect(result.get("description_placeholders")).to_equal(
        {
            "folder_name": FOLDER_NAME,
            "url": f"https://drive.google.com/drive/folders/{FOLDER_ID}",
        }
    )
    expect("result" in result).to_be(True)
    expect(result.get("result").unique_id).to_equal(TEST_USER_EMAIL)
    expect("token" in result.get("result").data).to_be(True)
    expect(result.get("result").data["token"].get("access_token")).to_equal(
        "mock-access-token"
    )
    expect(result.get("result").data["token"].get("refresh_token")).to_equal(
        "mock-refresh-token"
    )


@test
async def create_folder_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test case where creating the folder fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "&access_type=offline&prompt=consent"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    api.get_user = AsyncMock(
        return_value={"user": {"emailAddress": TEST_USER_EMAIL}}
    )
    api.list_files = AsyncMock(return_value={"files": []})
    api.create_file = AsyncMock(side_effect=GoogleDriveApiError("some error"))

    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("create_folder_failure")
    expect(result.get("description_placeholders")).to_equal({"message": "some error"})


@test.cases(
    test.case(
        "api_not_enabled",
        exception=GoogleDriveApiError("some error"),
        expected_abort_reason="access_not_configured",
        expected_placeholders={"message": "some error"},
    ),
    test.case(
        "general_exception",
        exception=Exception,
        expected_abort_reason="unknown",
        expected_placeholders=None,
    ),
)
async def get_email_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    api: MagicMock = Depends(mock_api),
    *,
    exception: Exception | type[Exception],
    expected_abort_reason: str,
    expected_placeholders: dict[str, str] | None,
) -> None:
    """Test case where getting the email address fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "&access_type=offline&prompt=consent"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    api.get_user = AsyncMock(side_effect=exception)
    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal(expected_abort_reason)
    expect(result.get("description_placeholders")).to_equal(expected_placeholders)


@test.cases(
    test.case(
        "reauth_successful",
        new_email=TEST_USER_EMAIL,
        expected_abort_reason="reauth_successful",
        expected_placeholders=None,
        expected_access_token="updated-access-token",
        expected_setup_calls=1,
    ),
    test.case(
        "wrong_account",
        new_email="other.user@domain.com",
        expected_abort_reason="wrong_account",
        expected_placeholders={"email": TEST_USER_EMAIL},
        expected_access_token="mock-access-token",
        expected_setup_calls=0,
    ),
)
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    api: MagicMock = Depends(mock_api),
    *,
    new_email: str,
    expected_abort_reason: str,
    expected_placeholders: dict[str, str] | None,
    expected_access_token: str,
    expected_setup_calls: int,
) -> None:
    """Test the reauthentication flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)

    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "&access_type=offline&prompt=consent"
    )
    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    api.get_user = AsyncMock(return_value={"user": {"emailAddress": new_email}})
    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.google_drive.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(expected_setup_calls)

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal(expected_abort_reason)
    expect(result.get("description_placeholders")).to_equal(expected_placeholders)

    expect(config_entry.unique_id).to_equal(TEST_USER_EMAIL)
    expect("token" in config_entry.data).to_be(True)
    expect(config_entry.data["token"].get("access_token")).to_equal(
        expected_access_token
    )
    expect(config_entry.data["token"].get("refresh_token")).to_equal(
        "mock-refresh-token"
    )


@test.cases(
    test.case(
        "reconfigure_successful",
        new_email=TEST_USER_EMAIL,
        expected_abort_reason="reconfigure_successful",
        expected_placeholders=None,
        expected_access_token="updated-access-token",
        expected_setup_calls=1,
    ),
    test.case(
        "wrong_account",
        new_email="other.user@domain.com",
        expected_abort_reason="wrong_account",
        expected_placeholders={"email": TEST_USER_EMAIL},
        expected_access_token="mock-access-token",
        expected_setup_calls=0,
    ),
)
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    api: MagicMock = Depends(mock_api),
    *,
    new_email: str,
    expected_abort_reason: str,
    expected_placeholders: dict[str, str] | None,
    expected_access_token: str,
    expected_setup_calls: int,
) -> None:
    """Test the reconfiguration flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "&access_type=offline&prompt=consent"
    )
    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    api.get_user = AsyncMock(return_value={"user": {"emailAddress": new_email}})
    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.google_drive.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(expected_setup_calls)

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal(expected_abort_reason)
    expect(result.get("description_placeholders")).to_equal(expected_placeholders)

    expect(config_entry.unique_id).to_equal(TEST_USER_EMAIL)
    expect("token" in config_entry.data).to_be(True)
    expect(config_entry.data["token"].get("access_token")).to_equal(
        expected_access_token
    )
    expect(config_entry.data["token"].get("refresh_token")).to_equal(
        "mock-refresh-token"
    )


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    api: MagicMock = Depends(mock_api),
) -> None:
    """Test already configured account."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["url"]).to_equal(
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "&access_type=offline&prompt=consent"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    api.get_user = AsyncMock(
        return_value={"user": {"emailAddress": TEST_USER_EMAIL}}
    )
    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
