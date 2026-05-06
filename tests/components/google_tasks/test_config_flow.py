"""Test the Google Tasks config flow."""

from unittest.mock import Mock, patch

from googleapiclient.errors import HttpError
from httplib2 import Response
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.google_tasks.const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import CLIENT_ID, setup_credentials, setup_userinfo

from tests.common import MockConfigEntry, async_load_fixture
from tests.hass_fixtures import (
    ClientSessionGenerator,
    aioclient_mock as aioclient_mock_fx,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _request: None = Depends(current_request_with_host),
    _credentials: None = Depends(setup_credentials),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _userinfo: Mock = Depends(setup_userinfo),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "google_tasks", context={"source": config_entries.SOURCE_USER}
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
        "&scope=https://www.googleapis.com/auth/tasks+"
        "https://www.googleapis.com/auth/userinfo.profile"
        "&access_type=offline&prompt=consent"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.google_tasks.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal("123")
    expect(result["result"].title).to_equal("Test Name")
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def api_not_enabled(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _userinfo: Mock = Depends(setup_userinfo),
) -> None:
    """Check flow aborts if api is not enabled."""
    result = await hass.config_entries.flow.async_init(
        "google_tasks", context={"source": config_entries.SOURCE_USER}
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
        "&scope=https://www.googleapis.com/auth/tasks+"
        "https://www.googleapis.com/auth/userinfo.profile"
        "&access_type=offline&prompt=consent"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.google_tasks.config_flow.build",
        side_effect=HttpError(
            Response({"status": "403"}),
            bytes(
                await async_load_fixture(hass, "api_not_enabled_response.json", DOMAIN),
                "utf-8",
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("access_not_configured")
    expect(result["description_placeholders"]["message"]).to_equal(
        "Google Tasks API has not been used in project 0 before or it is disabled. "
        "Enable it by visiting https://console.developers.google.com/apis/api/"
        "tasks.googleapis.com/overview?project=0 then retry. If you enabled this "
        "API recently, wait a few minutes for the action to propagate to our "
        "systems and retry."
    )


@test
async def general_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _userinfo: Mock = Depends(setup_userinfo),
) -> None:
    """Check flow aborts if exception happens."""
    result = await hass.config_entries.flow.async_init(
        "google_tasks", context={"source": config_entries.SOURCE_USER}
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
        "&scope=https://www.googleapis.com/auth/tasks+"
        "https://www.googleapis.com/auth/userinfo.profile"
        "&access_type=offline&prompt=consent"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.google_tasks.config_flow.build",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test.cases(
    test.case(
        "matching_unique",
        user_identifier="123",
        abort_reason="reauth_successful",
        resulting_access_token="updated-access-token",
        starting_unique_id="123",
    ),
    test.case(
        "no_unique_id",
        user_identifier="123",
        abort_reason="reauth_successful",
        resulting_access_token="updated-access-token",
        starting_unique_id=None,
    ),
    test.case(
        "wrong_account",
        user_identifier="345",
        abort_reason="wrong_account",
        resulting_access_token="mock-access",
        starting_unique_id="123",
    ),
)
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    *,
    user_identifier: str,
    abort_reason: str,
    resulting_access_token: str,
    starting_unique_id: str | None,
) -> None:
    """Test the re-authentication case updates the correct config entry."""
    with patch(
        "homeassistant.components.google_tasks.config_flow.build"
    ) as userinfo_mock:
        userinfo_mock.return_value.userinfo.return_value.get.return_value.execute.return_value = {
            "id": user_identifier,
            "name": "Test Name",
        }

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id=starting_unique_id,
            data={
                "token": {
                    "refresh_token": "mock-refresh-token",
                    "access_token": "mock-access",
                }
            },
        )
        config_entry.add_to_hass(hass)

        config_entry.async_start_reauth(hass)
        await hass.async_block_till_done()

        flows = hass.config_entries.flow.async_progress()
        expect(len(flows)).to_equal(1)
        result = flows[0]
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
            f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
            "&redirect_uri=https://example.com/auth/external/callback"
            f"&state={state}"
            "&scope=https://www.googleapis.com/auth/tasks+"
            "https://www.googleapis.com/auth/userinfo.profile"
            "&access_type=offline&prompt=consent"
        )
        client = await client_gen()
        resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
        expect(resp.status).to_equal(200)
        expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

        aioclient_mock.clear_requests()
        aioclient_mock.post(
            OAUTH2_TOKEN,
            json={
                "refresh_token": "mock-refresh-token",
                "access_token": "updated-access-token",
                "type": "Bearer",
                "expires_in": 60,
            },
        )

        with patch(
            "homeassistant.components.google_tasks.async_setup_entry",
            return_value=True,
        ):
            result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    expect(result["type"]).to_equal("abort")
    expect(result["reason"]).to_equal(abort_reason)

    expect(config_entry.unique_id).to_equal("123")
    expect("token" in config_entry.data).to_be(True)
    # Verify access token is refreshed.
    expect(config_entry.data["token"]["access_token"]).to_equal(resulting_access_token)
    expect(config_entry.data["token"]["refresh_token"]).to_equal("mock-refresh-token")
