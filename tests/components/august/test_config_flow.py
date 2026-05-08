"""Test the August config flow."""

from unittest.mock import ANY

from tryke import Depends, expect, fixture, test

from homeassistant.components.august.application_credentials import (
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from homeassistant.components.august.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    CLIENT_ID,
    USER_ID,
    client_credentials,
    disable_ratelimit_checks,
    jwt,
    mock_discovery,
    mock_setup_entry,
    skip_cloud,
)

from tests.hass_fixtures import (
    ClientSessionGenerator,
    aioclient_mock,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _creds: None = Depends(client_credentials),
    _request: None = Depends(current_request_with_host),
    _ratelimit: None = Depends(disable_ratelimit_checks),
    _discovery: None = Depends(mock_discovery),
    _cloud: None = Depends(skip_cloud),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
async def full_flow(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    _setup: None = Depends(mock_setup_entry),
    jwt_token: str = Depends(jwt),
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
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient.clear_requests()
    aioclient.post(
        OAUTH2_TOKEN,
        json={
            "access_token": jwt_token,
            "scope": "any",
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "user_id": "mock-user-id",
            "expires_at": 1697753347,
        },
    )

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.unique_id).to_equal(USER_ID)

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["result"].unique_id).to_equal(USER_ID)
    expect(entry.data).to_equal(
        {
            "auth_implementation": "august",
            "token": {
                "access_token": jwt_token,
                "expires_at": ANY,
                "expires_in": ANY,
                "refresh_token": "mock-refresh-token",
                "scope": "any",
                "user_id": "mock-user-id",
            },
        }
    )


@test.skip("full_flow_already_exists needs more setup")
async def full_flow_already_exists(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test full flow when entry already exists."""


@test.skip("reauth flow not yet ported")
async def reauth(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reauth flow."""


@test.skip("reauth_wrong_account flow not yet ported")
async def reauth_wrong_account(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reauth wrong account flow."""


@test.skip("legacy_migration tests not yet ported")
async def legacy_migration_with_email_match(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test legacy migration with email match."""


@test.skip("legacy_migration tests not yet ported")
async def legacy_migration_wrong_email(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test legacy migration with wrong email."""


@test.skip("legacy_migration tests not yet ported")
async def legacy_migration_no_email_in_jwt(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test legacy migration no email in jwt."""
