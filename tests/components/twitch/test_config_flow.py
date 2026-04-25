"""Test config flow for Twitch."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test
from twitchAPI.object.api import TwitchUser

from homeassistant.components.twitch.const import (
    CONF_CHANNELS,
    DOMAIN,
    OAUTH2_AUTHORIZE,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from . import get_generator, setup_integration
from ._fixtures import (
    CLIENT_ID,
    TITLE,
    expires_at,
    mock_config_entry,
    mock_connection,
    mock_setup_entry,
    scopes,
    setup_credentials,
    twitch_mock,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _credentials: None = Depends(setup_credentials),
    _connection: object = Depends(mock_connection),
    _request: None = Depends(current_request_with_host),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


async def _do_get_token(
    hass: HomeAssistant,
    result: FlowResult,
    hass_client_no_auth: ClientSessionGenerator,
    scopes: list[str],
) -> None:
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
        f"&state={state}&scope={'+'.join(scopes)}"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _twitch: AsyncMock = Depends(twitch_mock),
    scopes: list[str] = Depends(scopes),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "twitch", context={"source": SOURCE_USER}
    )
    await _do_get_token(hass, result, client, scopes)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("channel123")
    expect("result" in result).to_be(True)
    expect("token" in result["result"].data).to_be(True)
    expect(result["result"].data["token"]["access_token"]).to_equal("mock-access-token")
    expect(result["result"].data["token"]["refresh_token"]).to_equal(
        "mock-refresh-token"
    )
    expect(result["result"].unique_id).to_equal("123")
    expect(result["options"]).to_equal(
        {CONF_CHANNELS: ["internetofthings", "homeassistant"]}
    )


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _twitch: AsyncMock = Depends(twitch_mock),
    scopes: list[str] = Depends(scopes),
) -> None:
    """Check flow aborts when account already configured."""
    await setup_integration(hass, config_entry)
    result = await hass.config_entries.flow.async_init(
        "twitch", context={"source": SOURCE_USER}
    )
    await _do_get_token(hass, result, client, scopes)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _twitch: AsyncMock = Depends(twitch_mock),
    scopes: list[str] = Depends(scopes),
) -> None:
    """Check reauth flow."""
    await setup_integration(hass, config_entry)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    await _do_get_token(hass, result, client, scopes)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_from_import(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _twitch: AsyncMock = Depends(twitch_mock),
    expires_at_value: int = Depends(expires_at),
    scopes: list[str] = Depends(scopes),
) -> None:
    """Check reauth flow from imported config."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title=TITLE,
        unique_id="123",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": expires_at_value,
                "scope": " ".join(scopes),
            },
            "imported": True,
        },
        options={"channels": ["internetofthings"]},
    )
    await setup_integration(hass, config_entry)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await _do_get_token(hass, result, client, scopes)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    entries = hass.config_entries.async_entries(DOMAIN)
    entry = entries[0]
    expect("imported" not in entry.data).to_be(True)
    expect(entry.options).to_equal(
        {CONF_CHANNELS: ["internetofthings", "homeassistant"]}
    )


@test
async def reauth_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    twitch: AsyncMock = Depends(twitch_mock),
    scopes: list[str] = Depends(scopes),
) -> None:
    """Check reauth flow aborts with wrong account."""
    await setup_integration(hass, config_entry)
    twitch.return_value.get_users = lambda *args, **kwargs: get_generator(
        hass, "get_users_2.json", TwitchUser
    )
    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    await _do_get_token(hass, result, client, scopes)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_account")
