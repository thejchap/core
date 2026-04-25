"""Test the Neato Botvac config flow."""

from unittest.mock import patch

from pybotvac.neato import Neato
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, setup
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.neato.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aioclient_mock,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import ClientSessionGenerator

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"

VENDOR = Neato()
OAUTH2_AUTHORIZE = VENDOR.auth_endpoint
OAUTH2_TOKEN = VENDOR.token_endpoint


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _request: None = Depends(current_request_with_host),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock_obj: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Check full flow."""
    expect(await setup.async_setup_component(hass, "neato", {})).to_be(True)
    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET)
    )

    result = await hass.config_entries.flow.async_init(
        "neato", context={"source": config_entries.SOURCE_USER}
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
        f"&client_secret={CLIENT_SECRET}"
        "&scope=public_profile+control_robots+maps"
    )

    aiohttp_client = await client()
    resp = await aiohttp_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock_obj.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.neato.async_setup_entry", return_value=True
    ) as mock_setup:
        await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def abort_if_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if Neato is already setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"auth_implementation": "neato", "token": {"some": "data"}},
    )
    entry.add_to_hass(hass)

    # Should fail
    result = await hass.config_entries.flow.async_init(
        "neato", context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock_obj: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test initialization of the reauth flow."""
    expect(await setup.async_setup_component(hass, "neato", {})).to_be(True)
    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET)
    )

    entry = MockConfigEntry(
        entry_id="my_entry",
        domain=DOMAIN,
        data={"username": "abcdef", "password": "123456", "vendor": "neato"},
    )
    entry.add_to_hass(hass)

    # Should show form
    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    # Confirm reauth flow
    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    aiohttp_client = await client()
    resp = await aiohttp_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock_obj.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    # Update entry
    with patch(
        "homeassistant.components.neato.async_setup_entry", return_value=True
    ) as mock_setup:
        result3 = await hass.config_entries.flow.async_configure(result2["flow_id"])
        await hass.async_block_till_done()

    new_entry = hass.config_entries.async_get_entry("my_entry")

    expect(result3["type"]).to_be(FlowResultType.ABORT)
    expect(result3["reason"]).to_equal("reauth_successful")
    expect(new_entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)
