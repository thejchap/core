"""Test the Google Assistant SDK config flow."""

from collections.abc import Coroutine
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.google_assistant_sdk.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    CLIENT_ID,
    config_entry as config_entry_fixture,
    setup_credentials,
    setup_integration,
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
TITLE = "Google Assistant SDK"


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
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _credentials: None = Depends(setup_credentials),
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
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/assistant-sdk-prototype"
        "&access_type=offline&prompt=consent"
    )

    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

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
        "homeassistant.components.google_assistant_sdk.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(TITLE)
    expect("result" in result).to_be(True)
    expect(result.get("result").unique_id).to_be(None)
    expect("token" in result.get("result").data).to_be(True)
    expect(result.get("result").data["token"].get("access_token")).to_equal(
        "mock-access-token"
    )
    expect(result.get("result").data["token"].get("refresh_token")).to_equal(
        "mock-refresh-token"
    )


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _credentials: None = Depends(setup_credentials),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test the reauthentication case updates the existing config entry."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
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
        f"&state={state}&scope=https://www.googleapis.com/auth/assistant-sdk-prototype"
        "&access_type=offline&prompt=consent"
    )
    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

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
        "homeassistant.components.google_assistant_sdk.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")

    expect(config_entry.unique_id).to_be(None)
    expect("token" in config_entry.data).to_be(True)
    expect(config_entry.data["token"].get("access_token")).to_equal(
        "updated-access-token"
    )
    expect(config_entry.data["token"].get("refresh_token")).to_equal(
        "mock-refresh-token"
    )


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _credentials: None = Depends(setup_credentials),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test the reconfiguration flow updates the existing config entry."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)

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
        f"&state={state}&scope=https://www.googleapis.com/auth/assistant-sdk-prototype"
        "&access_type=offline&prompt=consent"
    )
    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(config_entry.unique_id).to_be(None)
    expect("token" in config_entry.data).to_be(True)
    expect(config_entry.data["token"].get("access_token")).to_equal(
        "updated-access-token"
    )
    expect(config_entry.data["token"].get("refresh_token")).to_equal(
        "mock-refresh-token"
    )


@test
async def single_instance_allowed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _credentials: None = Depends(setup_credentials),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test case where config flow allows a single test."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("single_instance_allowed")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_int: Coroutine[Any, Any, None] = Depends(setup_integration),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test options flow."""
    await setup_int()
    expect(bool(config_entry.options)).to_be(False)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    data_schema = result["data_schema"].schema
    expect(set(data_schema)).to_equal({"language_code"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"language_code": "es-ES"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({"language_code": "es-ES"})

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    data_schema = result["data_schema"].schema
    expect(set(data_schema)).to_equal({"language_code"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"language_code": "es-ES"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({"language_code": "es-ES"})

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    data_schema = result["data_schema"].schema
    expect(set(data_schema)).to_equal({"language_code"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"language_code": "en-US"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({"language_code": "en-US"})
