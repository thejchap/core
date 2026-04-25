"""Test the Honeywell Lyric config flow."""

from http import HTTPStatus
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.lyric.const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import CLIENT_ID, mock_impl

from tests.common import MockConfigEntry
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
    _request: None = Depends(current_request_with_host),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def abort_if_no_configuration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check flow abort when no configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("missing_credentials")


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _impl: None = Depends(mock_impl),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
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

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&appSelect=1"
    )

    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)
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

    with (
        patch("homeassistant.components.lyric.api.ConfigEntryLyricClient"),
        patch(
            "homeassistant.components.lyric.async_setup_entry", return_value=True
        ) as mock_setup,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["data"]["auth_implementation"]).to_equal("cred")

    result["data"]["token"].pop("expires_at")
    expect(result["data"]["token"]).to_equal(
        {
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        }
    )

    expect(DOMAIN in hass.config.components).to_be(True)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def reauthentication_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _impl: None = Depends(mock_impl),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test reauthentication flow."""
    old_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        version=1,
        data={"id": "timmo", "auth_implementation": DOMAIN},
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    result = await hass.config_entries.flow.async_configure(flows[0]["flow_id"], {})

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    http_client = await client()
    await http_client.get(f"/auth/external/callback?code=abcd&state={state}")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with (
        patch("homeassistant.components.lyric.api.ConfigEntryLyricClient"),
        patch(
            "homeassistant.components.lyric.async_setup_entry", return_value=True
        ) as mock_setup,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(len(mock_setup.mock_calls)).to_equal(1)
