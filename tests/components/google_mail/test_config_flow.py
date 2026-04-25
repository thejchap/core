"""Test the Google Mail config flow."""

from unittest.mock import patch

from httplib2 import Response
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.google_mail.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    CLIENT_ID,
    GOOGLE_AUTH_URI,
    GOOGLE_TOKEN_URI,
    SCOPES,
    TITLE,
    config_entry as config_entry_fx,
    mock_connection,
    setup_credentials,
)

from tests.common import MockConfigEntry, async_load_fixture
from tests.hass_fixtures import (
    ClientSessionGenerator,
    aioclient_mock as aioclient_mock_fixture,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _credentials: None = Depends(setup_credentials),
    _connection: AiohttpClientMocker = Depends(mock_connection),
    _request: None = Depends(current_request_with_host),
) -> None:
    """Apply autouse-equivalent fixtures."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "google_mail", context={"source": config_entries.SOURCE_USER}
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
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    with (
        patch(
            "homeassistant.components.google_mail.async_setup_entry", return_value=True
        ) as mock_setup,
        patch(
            "httplib2.Http.request",
            return_value=(
                Response({}),
                bytes(
                    await async_load_fixture(hass, "get_profile.json", DOMAIN),
                    encoding="UTF-8",
                ),
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(TITLE)
    expect("result" in result).to_be(True)
    expect(result.get("result").unique_id).to_equal(TITLE)
    expect("token" in result.get("result").data).to_be(True)
    expect(result.get("result").data["token"].get("access_token")).to_equal(
        "mock-access-token"
    )
    expect(result.get("result").data["token"].get("refresh_token")).to_equal(
        "mock-refresh-token"
    )


@test.cases(
    test.case(
        "reauth_successful",
        fixture_name="get_profile",
        abort_reason="reauth_successful",
        placeholders=None,
        call_count=1,
        access_token="updated-access-token",
    ),
    test.case(
        "wrong_account",
        fixture_name="get_profile_2",
        abort_reason="wrong_account",
        placeholders={"email": "example@gmail.com"},
        call_count=0,
        access_token="mock-access-token",
    ),
)
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    *,
    fixture_name: str,
    abort_reason: str,
    placeholders: dict[str, str] | None,
    call_count: int,
    access_token: str,
) -> None:
    """Test re-authentication updates the correct config entry."""
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
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )
    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with (
        patch(
            "homeassistant.components.google_mail.async_setup_entry", return_value=True
        ) as mock_setup,
        patch(
            "httplib2.Http.request",
            return_value=(
                Response({}),
                bytes(
                    await async_load_fixture(hass, f"{fixture_name}.json", DOMAIN),
                    encoding="UTF-8",
                ),
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(abort_reason)
    expect(result["description_placeholders"]).to_equal(placeholders)
    expect(len(mock_setup.mock_calls)).to_equal(call_count)

    expect(config_entry.unique_id).to_equal(TITLE)
    expect("token" in config_entry.data).to_be(True)
    # Verify access token is refreshed
    expect(config_entry.data["token"].get("access_token")).to_equal(access_token)
    expect(config_entry.data["token"].get("refresh_token")).to_equal("mock-refresh-token")


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
) -> None:
    """Test case where config flow discovers unique id was already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        "google_mail", context={"source": config_entries.SOURCE_USER}
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
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    with patch(
        "httplib2.Http.request",
        return_value=(
            Response({}),
            bytes(
                await async_load_fixture(hass, "get_profile.json", DOMAIN),
                encoding="UTF-8",
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
