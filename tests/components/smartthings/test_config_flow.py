"""Tests for the SmartThings config flow module."""

from http import HTTPStatus
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.smartthings import OLD_DATA
from homeassistant.components.smartthings.const import (
    CONF_LOCATION_ID,
    CONF_SUBSCRIPTION_ID,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_old_config_entry,
    mock_setup_entry,
    mock_smartthings,
    setup_credentials,
    use_cloud,
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


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _creds: None = Depends(setup_credentials),
) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@fixture
def _trigger_with_cloud(
    _network: None = Depends(mock_network),
    _creds: None = Depends(setup_credentials),
    _cloud: None = Depends(use_cloud),
    _request: None = Depends(current_request_with_host),
) -> None:
    """Anchor fixture for OAuth flows that require the cloud component."""


@fixture
def _trigger_no_cloud(
    _network: None = Depends(mock_network),
    _creds: None = Depends(setup_credentials),
    _request: None = Depends(current_request_with_host),
) -> None:
    """Anchor fixture for OAuth flows where cloud is intentionally absent."""


@test
async def missing_credentials_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Without OAuth credentials configured, the flow aborts."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    # Without 'cloud' component or OAuth credentials, smartthings aborts.
    expect(
        result["reason"] in ("cloud_not_enabled", "missing_credentials")
    ).to_be(True)


@test
async def full_flow(
    _trigger: None = Depends(_trigger_with_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    _smartthings: AsyncMock = Depends(mock_smartthings),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Check a full flow."""
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

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result["url"]).to_equal(
        "https://api.smartthings.com/oauth/authorize"
        "?response_type=code&client_id=CLIENT_ID"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        "&scope=r:devices:*+w:devices:*+x:devices:*+r:hubs:*+"
        "r:locations:*+w:locations:*+x:locations:*+r:scenes:*+"
        "x:scenes:*+r:rules:*+w:rules:*+sse+r:installedapps+"
        "w:installedapps"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient.clear_requests()
    aioclient.post(
        "https://auth-global.api.smartthings.com/oauth/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* w:rules:* sse",
            "access_tier": 0,
            "installed_app_id": "5aaaa925-2be1-4e40-b257-e4ef59083324",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    result["data"]["token"].pop("expires_at")
    expect(result["data"][CONF_TOKEN]).to_equal(
        {
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* w:rules:* sse",
            "access_tier": 0,
            "installed_app_id": "5aaaa925-2be1-4e40-b257-e4ef59083324",
        }
    )
    expect(result["result"].unique_id).to_equal("397678e5-9995-4a39-9d9f-ae6ba310236c")


@test
async def not_enough_scopes(
    _trigger: None = Depends(_trigger_with_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    _smartthings: AsyncMock = Depends(mock_smartthings),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we abort if we don't have enough scopes."""
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

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)

    aioclient.clear_requests()
    aioclient.post(
        "https://auth-global.api.smartthings.com/oauth/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* w:rules:* "
            "r:installedapps w:installedapps",
            "access_tier": 0,
            "installed_app_id": "5aaaa925-2be1-4e40-b257-e4ef59083324",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("missing_scopes")


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_with_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    _smartthings: AsyncMock = Depends(mock_smartthings),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate entry is not able to set up."""
    config_entry.add_to_hass(hass)
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

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)

    aioclient.clear_requests()
    aioclient.post(
        "https://auth-global.api.smartthings.com/oauth/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* w:rules:* sse",
            "access_tier": 0,
            "installed_app_id": "5aaaa925-2be1-4e40-b257-e4ef59083324",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def no_cloud(
    _trigger: None = Depends(_trigger_no_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    _client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    _aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    _smartthings: AsyncMock = Depends(mock_smartthings),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Check we abort when cloud is not enabled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cloud_not_enabled")


@test
async def reauthentication(
    _trigger: None = Depends(_trigger_with_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    _smartthings: AsyncMock = Depends(mock_smartthings),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test SmartThings reauthentication."""
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
    client = await client_factory()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

    aioclient.post(
        "https://auth-global.api.smartthings.com/oauth/token",
        json={
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* sse w:rules:*",
            "access_tier": 0,
            "installed_app_id": "5aaaa925-2be1-4e40-b257-e4ef59083324",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    config_entry.data["token"].pop("expires_at")
    expect(config_entry.data[CONF_TOKEN]).to_equal(
        {
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* sse w:rules:*",
            "access_tier": 0,
            "installed_app_id": "5aaaa925-2be1-4e40-b257-e4ef59083324",
        }
    )


@test
async def reauthentication_wrong_scopes(
    _trigger: None = Depends(_trigger_with_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    _smartthings: AsyncMock = Depends(mock_smartthings),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test SmartThings reauthentication with wrong scopes."""
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
    client = await client_factory()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

    aioclient.post(
        "https://auth-global.api.smartthings.com/oauth/token",
        json={
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* w:rules:* "
            "r:installedapps w:installedapps",
            "access_tier": 0,
            "installed_app_id": "5aaaa925-2be1-4e40-b257-e4ef59083324",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("missing_scopes")


@test
async def reauth_account_mismatch(
    _trigger: None = Depends(_trigger_with_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    smartthings: AsyncMock = Depends(mock_smartthings),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test SmartThings reauthentication with different account."""
    config_entry.add_to_hass(hass)

    smartthings.get_locations.return_value[
        0
    ].location_id = "123123123-2be1-4e40-b257-e4ef59083324"

    result = await config_entry.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await client_factory()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

    aioclient.post(
        "https://auth-global.api.smartthings.com/oauth/token",
        json={
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* w:rules:* sse",
            "access_tier": 0,
            "installed_app_id": "123123123-2be1-4e40-b257-e4ef59083324",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_account_mismatch")


@test
async def reauthentication_no_cloud(
    _trigger: None = Depends(_trigger_no_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    _client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    _aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    _smartthings: AsyncMock = Depends(mock_smartthings),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test SmartThings reauthentication without cloud."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cloud_not_enabled")


@test
async def migration(
    _trigger: None = Depends(_trigger_with_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    smartthings: AsyncMock = Depends(mock_smartthings),
    config_entry: MockConfigEntry = Depends(mock_old_config_entry),
) -> None:
    """Test SmartThings migration from old to new config entry."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    result = hass.config_entries.flow.async_progress()[0]

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await client_factory()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

    aioclient.post(
        "https://auth-global.api.smartthings.com/oauth/token",
        json={
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* w:rules:* sse",
            "access_tier": 0,
            "installed_app_id": "123123123-2be1-4e40-b257-e4ef59083324",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(hass.config_entries.flow.async_progress())).to_equal(0)
    config_entry.data[CONF_TOKEN].pop("expires_at")
    expect(config_entry.data).to_equal(
        {
            "auth_implementation": DOMAIN,
            "old_data": {CONF_LOCATION_ID: "397678e5-9995-4a39-9d9f-ae6ba310236c"},
            CONF_TOKEN: {
                "refresh_token": "new-refresh-token",
                "access_token": "new-access-token",
                "token_type": "Bearer",
                "expires_in": 82806,
                "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
                "r:locations:* w:locations:* x:locations:* "
                "r:scenes:* x:scenes:* r:rules:* w:rules:* sse",
                "access_tier": 0,
                "installed_app_id": "123123123-2be1-4e40-b257-e4ef59083324",
            },
            CONF_LOCATION_ID: "397678e5-9995-4a39-9d9f-ae6ba310236c",
            CONF_SUBSCRIPTION_ID: "f5768ce8-c9e5-4507-9020-912c0c60e0ab",
        }
    )
    expect(config_entry.unique_id).to_equal("397678e5-9995-4a39-9d9f-ae6ba310236c")
    expect(config_entry.version).to_equal(3)
    expect(config_entry.minor_version).to_equal(3)
    smartthings.get_installed_app.assert_called_once_with(
        "mock-access-token",
        "123aa123-2be1-4e40-b257-e4ef59083324",
    )
    smartthings.delete_installed_app.assert_called_once_with(
        "mock-access-token",
        "123aa123-2be1-4e40-b257-e4ef59083324",
    )
    smartthings.delete_smart_app.assert_called_once_with(
        "mock-access-token",
        "c6cde2b0-203e-44cf-a510-3b3ed4706996",
    )


@test
async def migration_wrong_location(
    _trigger: None = Depends(_trigger_with_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    smartthings: AsyncMock = Depends(mock_smartthings),
    config_entry: MockConfigEntry = Depends(mock_old_config_entry),
) -> None:
    """Test SmartThings reauthentication with wrong location."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    smartthings.get_locations.return_value[
        0
    ].location_id = "123123123-2be1-4e40-b257-e4ef59083324"

    result = hass.config_entries.flow.async_progress()[0]

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await client_factory()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

    aioclient.post(
        "https://auth-global.api.smartthings.com/oauth/token",
        json={
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* w:rules:* sse",
            "access_tier": 0,
            "installed_app_id": "123123123-2be1-4e40-b257-e4ef59083324",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_location_mismatch")
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(config_entry.data).to_equal(
        {OLD_DATA: {CONF_LOCATION_ID: "397678e5-9995-4a39-9d9f-ae6ba310236c"}}
    )
    expect(config_entry.unique_id).to_equal(
        "appid123-2be1-4e40-b257-e4ef59083324_397678e5-9995-4a39-9d9f-ae6ba310236c"
    )
    expect(config_entry.version).to_equal(3)
    expect(config_entry.minor_version).to_equal(3)
    smartthings.get_installed_app.assert_called_once_with(
        "mock-access-token",
        "123aa123-2be1-4e40-b257-e4ef59083324",
    )
    smartthings.delete_installed_app.assert_called_once_with(
        "mock-access-token",
        "123aa123-2be1-4e40-b257-e4ef59083324",
    )
    smartthings.delete_smart_app.assert_called_once_with(
        "mock-access-token",
        "c6cde2b0-203e-44cf-a510-3b3ed4706996",
    )


@test
async def migration_no_cloud(
    _trigger: None = Depends(_trigger_no_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    _client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    _aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    _smartthings: AsyncMock = Depends(mock_smartthings),
    config_entry: MockConfigEntry = Depends(mock_old_config_entry),
) -> None:
    """Test SmartThings migration without cloud."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    result = hass.config_entries.flow.async_progress()[0]

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cloud_not_enabled")


@test
async def dhcp_flow(
    _trigger: None = Depends(_trigger_with_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    _smartthings: AsyncMock = Depends(mock_smartthings),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Check a full flow initiated by DHCP discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.0.2", hostname="Samsung-Washer", macaddress="88571dc3ed7d"
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("oauth_discovery")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result["url"]).to_equal(
        "https://api.smartthings.com/oauth/authorize"
        "?response_type=code&client_id=CLIENT_ID"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        "&scope=r:devices:*+w:devices:*+x:devices:*+r:hubs:*+"
        "r:locations:*+w:locations:*+x:locations:*+r:scenes:*+"
        "x:scenes:*+r:rules:*+w:rules:*+sse+r:installedapps+"
        "w:installedapps"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient.clear_requests()
    aioclient.post(
        "https://auth-global.api.smartthings.com/oauth/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* w:rules:* sse",
            "access_tier": 0,
            "installed_app_id": "5aaaa925-2be1-4e40-b257-e4ef59083324",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_entry_dhcp(
    _trigger: None = Depends(_trigger_with_cloud),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate entry is not able to set up."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.0.2", hostname="Samsung-Washer", macaddress="88571dc3ed7d"
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
