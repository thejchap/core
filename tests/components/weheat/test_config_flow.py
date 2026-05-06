"""Test the Weheat config flow."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.weheat.const import (
    DOMAIN,
    ENTRY_TITLE,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from homeassistant.config_entries import SOURCE_USER, ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_SOURCE, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    mock_setup_entry,
    mock_user_id,
    mock_weheat_discover,
    setup_credentials,
)
from .const import (
    CLIENT_ID,
    CONF_AUTH_IMPLEMENTATION,
    CONF_REFRESH_TOKEN,
    MOCK_ACCESS_TOKEN,
    MOCK_REFRESH_TOKEN,
    USER_UUID_1,
    USER_UUID_2,
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


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _credentials: None = Depends(setup_credentials),
    _request: None = Depends(current_request_with_host),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


async def _handle_oauth(
    hass: HomeAssistant,
    hass_client_no_auth_fn: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    result: ConfigFlowResult,
) -> None:
    """Handle the Oauth2 part of the flow."""
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
        "&scope=openid+offline_access"
    )

    client = await hass_client_no_auth_fn()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": MOCK_REFRESH_TOKEN,
            "access_token": MOCK_ACCESS_TOKEN,
            "type": "Bearer",
            "expires_in": 60,
        },
    )


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Check full of adding a single heat pump."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    await _handle_oauth(hass, client, aioclient_mock, result)

    with patch(
        "homeassistant.components.weheat.config_flow.async_get_user_id_from_token",
        return_value=USER_UUID_1,
    ) as mock_weheat:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_weheat.mock_calls)).to_equal(1)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(USER_UUID_1)
    expect(result["result"].title).to_equal(ENTRY_TITLE)
    expect(result["data"][CONF_TOKEN][CONF_REFRESH_TOKEN]).to_equal(MOCK_REFRESH_TOKEN)
    expect(result["data"][CONF_TOKEN][CONF_ACCESS_TOKEN]).to_equal(MOCK_ACCESS_TOKEN)
    expect(result["data"][CONF_AUTH_IMPLEMENTATION]).to_equal(DOMAIN)


@test
async def duplicate_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Check that the config flow is aborted when an entry with the same ID exists."""
    first_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        unique_id=USER_UUID_1,
    )

    first_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    await _handle_oauth(hass, client, aioclient_mock, result)

    with patch(
        "homeassistant.components.weheat.config_flow.async_get_user_id_from_token",
        return_value=USER_UUID_1,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "correct_user", logged_in_user=USER_UUID_1, expected_reason="reauth_successful"
    ),
    test.case(
        "wrong_user", logged_in_user=USER_UUID_2, expected_reason="wrong_account"
    ),
)
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    user_id: AsyncMock = Depends(mock_user_id),
    _discover: AsyncMock = Depends(mock_weheat_discover),
    *,
    logged_in_user: str,
    expected_reason: str,
) -> None:
    """Check reauth flow both with and without the correct logged in user."""
    user_id.return_value = logged_in_user
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        unique_id=USER_UUID_1,
    )

    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"],
        user_input={},
    )

    await _handle_oauth(hass, client, aioclient_mock, result)

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal(expected_reason)
    expect(entry.unique_id).to_equal(USER_UUID_1)
