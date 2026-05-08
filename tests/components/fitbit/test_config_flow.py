"""Test the fitbit config flow."""

from http import HTTPStatus
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.fitbit.const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    CLIENT_ID,
    DISPLAY_NAME,
    FAKE_AUTH_IMPL,
    PROFILE_USER_ID,
    SERVER_ACCESS_TOKEN,
    config_entry,
    profile,
    setup_credentials,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    aioclient_mock,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

REDIRECT_URL = "https://example.com/auth/external/callback"


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _creds: None = Depends(setup_credentials),
    _request: None = Depends(current_request_with_host),
    _profile: None = Depends(profile),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
async def full_flow(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URL,
        },
    )
    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&state={state}"
        "&scope=activity+heartrate+nutrition+profile+settings+sleep+weight&prompt=consent"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient.post(
        OAUTH2_TOKEN,
        json=SERVER_ACCESS_TOKEN,
    )

    with patch(
        "homeassistant.components.fitbit.async_setup_entry", return_value=True
    ) as mock_setup:
        await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(mock_setup.mock_calls)).to_equal(1)
    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)
    config_entry_obj = entries[0]
    expect(config_entry_obj.title).to_equal(DISPLAY_NAME)
    expect(config_entry_obj.unique_id).to_equal(PROFILE_USER_ID)

    data = dict(config_entry_obj.data)
    expect("token" in data).to_be(True)
    del data["token"]["expires_at"]
    expect(dict(config_entry_obj.data)).to_equal(
        {
            "auth_implementation": FAKE_AUTH_IMPL,
            "token": SERVER_ACCESS_TOKEN,
        }
    )


@test.cases(
    test.case(
        "unauthorized",
        status_code=HTTPStatus.UNAUTHORIZED,
        error_reason="invalid_auth",
    ),
    test.case(
        "server_error",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        error_reason="cannot_connect",
    ),
)
async def token_error(
    *,
    status_code: HTTPStatus,
    error_reason: str,
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Check token errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URL,
        },
    )
    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient.post(
        OAUTH2_TOKEN,
        status=status_code,
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal(error_reason)


@test.skip("multi-parametrize api_failure with profile_id needs more work")
async def api_failure(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a failure to fetch the profile during the setup flow."""


@test.skip("config_entry_already_exists needs integration_setup fixture")
async def config_entry_already_exists(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that an account may only be configured once."""


@test.skip("reauth_flow needs more setup")
async def reauth_flow(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test OAuth reauthentication flow will update existing config entry."""


@test.skip("reauth_wrong_user_id needs profile_id parametrize")
async def reauth_wrong_user_id(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test OAuth reauthentication where the wrong user is selected."""


@test.skip("partial_profile_data has profile_data parametrize")
async def partial_profile_data(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Check full flow with partial profile data."""
