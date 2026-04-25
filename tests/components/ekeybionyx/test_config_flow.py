"""Test the ekey bionyx config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.ekeybionyx.const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    SCOPE,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    CLIENT_ID,
    add_webhook,
    already_set_up,
    dummy_systems,
    no_available_webhooks,
    no_own_system,
    no_response,
    setup_credentials,
    system,
    token_hex,
    webhook_deletion,
    webhook_id,
    webhooks,
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
    _network: None = Depends(mock_network),
    _request: None = Depends(current_request_with_host),
    _add_webhook: None = Depends(add_webhook),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    client_mock: AiohttpClientMocker = Depends(aioclient_mock),
    _credentials: None = Depends(setup_credentials),
    _webhook_id: None = Depends(webhook_id),
    _system: None = Depends(system),
    _token_hex: None = Depends(token_hex),
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
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        f"&scope={SCOPE}"
    )

    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    client_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )
    flow = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(flow.get("step_id")).to_equal("choose_system")

    flow2 = await hass.config_entries.flow.async_configure(
        flow["flow_id"], {"system": "946DA01F-9ABD-4D9D-80C7-02AF85C822A8"}
    )
    expect(flow2.get("step_id")).to_equal("webhooks")

    flow3 = await hass.config_entries.flow.async_configure(
        flow2["flow_id"],
        {
            "url": "localhost:8123",
        },
    )

    expect(flow3.get("errors")).to_equal(
        {"base": "no_webhooks_provided", "url": "invalid_url"}
    )

    flow4 = await hass.config_entries.flow.async_configure(
        flow3["flow_id"],
        {
            "webhook1": "Test ",
            "webhook2": " Invalid",
            "webhook3": "1Invalid",
            "webhook4": "Also@Invalid",
            "webhook5": "Invalid-Name",
            "url": "localhost:8123",
        },
    )

    expect(flow4.get("errors")).to_equal(
        {
            "url": "invalid_url",
            "webhook1": "invalid_name",
            "webhook2": "invalid_name",
            "webhook3": "invalid_name",
            "webhook4": "invalid_name",
            "webhook5": "invalid_name",
        }
    )

    with patch(
        "homeassistant.components.ekeybionyx.async_setup_entry", return_value=True
    ) as mock_setup:
        flow5 = await hass.config_entries.flow.async_configure(
            flow2["flow_id"],
            {
                "webhook1": "Test",
                "url": "http://localhost:8123",
            },
        )
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(hass.config_entries.async_entries(DOMAIN)[0].data).to_equal(
        {
            "webhooks": [
                {
                    "webhook_id": "1234567890",
                    "name": "Test",
                    "auth": "f2156edca7fc6871e13845314a6fc68622e5ad7c58f17663a487ed28cac247f7",
                    "ekey_id": "946DA01F-9ABD-4D9D-80C7-02AF85C822A8",
                }
            ]
        }
    )

    expect(flow5.get("type")).to_be(FlowResultType.CREATE_ENTRY)

    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def no_own_system_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    client_mock: AiohttpClientMocker = Depends(aioclient_mock),
    _credentials: None = Depends(setup_credentials),
    _no_own: None = Depends(no_own_system),
) -> None:
    """Check no own System flow."""
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
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        f"&scope={SCOPE}"
    )

    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    client_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )
    flow = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(0)

    expect(flow.get("type")).to_be(FlowResultType.ABORT)
    expect(flow.get("reason")).to_equal("no_own_systems")


@test
async def no_available_webhooks_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    client_mock: AiohttpClientMocker = Depends(aioclient_mock),
    _credentials: None = Depends(setup_credentials),
    _no_available: None = Depends(no_available_webhooks),
) -> None:
    """Check no available webhooks flow."""
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
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        f"&scope={SCOPE}"
    )

    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    client_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )
    flow = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(0)

    expect(flow.get("type")).to_be(FlowResultType.ABORT)
    expect(flow.get("reason")).to_equal("no_available_webhooks")


@test
async def cleanup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    client_mock: AiohttpClientMocker = Depends(aioclient_mock),
    _credentials: None = Depends(setup_credentials),
    _set_up: None = Depends(already_set_up),
    _webhooks: None = Depends(webhooks),
    _deletion: None = Depends(webhook_deletion),
) -> None:
    """Check cleanup flow."""
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
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        f"&scope={SCOPE}"
    )

    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    client_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    flow = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(flow.get("step_id")).to_equal("delete_webhooks")

    flow2 = await hass.config_entries.flow.async_configure(flow["flow_id"], {})
    expect(flow2.get("type")).to_be(FlowResultType.SHOW_PROGRESS)

    client_mock.clear_requests()

    client_mock.get(
        "https://api.bionyx.io/3rd-party/api/systems",
        json=dummy_systems(1, 1, 0),
    )

    await hass.async_block_till_done()

    expect(
        hass.config_entries.flow.async_get(flow2["flow_id"]).get("step_id")
    ).to_equal("webhooks")


@test
async def error_on_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    client_mock: AiohttpClientMocker = Depends(aioclient_mock),
    _credentials: None = Depends(setup_credentials),
    _no_response: None = Depends(no_response),
) -> None:
    """Check error on setup flow."""
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
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        f"&scope={SCOPE}"
    )

    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    client_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )
    flow = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(0)

    expect(flow.get("type")).to_be(FlowResultType.ABORT)
    expect(flow.get("reason")).to_equal("cannot_connect")
