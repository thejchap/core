"""Test the OneDrive config flow."""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

from onedrive_personal_sdk.exceptions import OneDriveException
from onedrive_personal_sdk.models.items import AppRoot, ItemUpdate
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.onedrive.const import (
    CONF_DELETE_PERMANENTLY,
    CONF_FOLDER_ID,
    CONF_FOLDER_NAME,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from . import setup_integration
from ._fixtures import (
    mock_approot,
    mock_backup_file,
    mock_config_entry,
    mock_drive,
    mock_folder,
    mock_instance_id,
    mock_metadata_file,
    mock_onedrive_client,
    mock_onedrive_client_init,
    mock_setup_entry,
    setup_credentials,
)
from .const import CLIENT_ID

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
    _credentials: None = Depends(setup_credentials),
    _request: None = Depends(current_request_with_host),
    _instance_id: None = Depends(mock_instance_id),
) -> None:
    """Apply autouse-equivalent fixtures."""


async def _do_get_token(
    hass: HomeAssistant,
    result: ConfigFlowResult,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    scope = "Files.ReadWrite.AppFolder+offline_access+openid"

    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={scope}"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
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


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    setup_mock: AsyncMock = Depends(mock_setup_entry),
    onedrive_init: MagicMock = Depends(mock_onedrive_client_init),
    _client: MagicMock = Depends(mock_onedrive_client),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await _do_get_token(hass, result, client_factory, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    token_callback = onedrive_init.call_args[0][0]
    expect(await token_callback()).to_equal("mock-access-token")

    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "myFolder"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(setup_mock.mock_calls)).to_equal(1)
    expect(result["title"]).to_equal("John Doe's OneDrive")
    expect(result["result"].unique_id).to_equal("mock_drive_id")
    expect(result["data"][CONF_TOKEN][CONF_ACCESS_TOKEN]).to_equal("mock-access-token")
    expect(result["data"][CONF_TOKEN]["refresh_token"]).to_equal("mock-refresh-token")
    expect(result["data"][CONF_FOLDER_NAME]).to_equal("myFolder")
    expect(result["data"][CONF_FOLDER_ID]).to_equal("my_folder_id")


@test
async def full_flow_with_owner_not_found(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    setup_mock: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_onedrive_client),
    approot: MagicMock = Depends(mock_approot),
) -> None:
    """Ensure we get a default title if the drive's owner can't be read."""
    approot.created_by.user = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await _do_get_token(hass, result, client_factory, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "myFolder"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(setup_mock.mock_calls)).to_equal(1)
    expect(result["title"]).to_equal("OneDrive")
    expect(result["result"].unique_id).to_equal("mock_drive_id")


@test
async def error_during_folder_creation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_onedrive_client),
) -> None:
    """Ensure we can create the backup folder."""
    client.create_folder.side_effect = OneDriveException()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await _do_get_token(hass, result, client_factory, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "myFolder"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "folder_creation_error"})

    client.create_folder.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "myFolder"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("unknown", exception=Exception, error="unknown"),
    test.case(
        "connection_error", exception=OneDriveException, error="connection_error"
    ),
)
async def flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    client: MagicMock = Depends(mock_onedrive_client),
    *,
    exception: type[Exception],
    error: str,
) -> None:
    """Test errors during flow."""
    client.get_approot.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await _do_get_token(hass, result, client_factory, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(error)


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_onedrive_client),
) -> None:
    """Test already configured account."""
    await setup_integration(hass, config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    await _do_get_token(hass, result, client_factory, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_onedrive_client),
) -> None:
    """Test that the reauth flow works."""
    await setup_integration(hass, config_entry)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await _do_get_token(hass, result, client_factory, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_TOKEN][CONF_ACCESS_TOKEN]).to_equal(
        "mock-access-token"
    )
    expect(config_entry.data[CONF_TOKEN]["refresh_token"]).to_equal("mock-refresh-token")
    expect(config_entry.data[CONF_FOLDER_ID]).to_equal("my_folder_id")


@test
async def reauth_flow_id_changed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_onedrive_client),
    approot: AppRoot = Depends(mock_approot),
) -> None:
    """Test that the reauth flow fails on a different drive id."""
    approot.parent_reference.drive_id = "other_drive_id"

    await setup_integration(hass, config_entry)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await _do_get_token(hass, result, client_factory, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_drive")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    client: MagicMock = Depends(mock_onedrive_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow."""
    await setup_integration(hass, config_entry)

    result = await config_entry.start_reconfigure_flow(hass)
    await _do_get_token(hass, result, client_factory, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure_folder")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "newFolder"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    client.update_drive_item.assert_called_once_with(
        config_entry.data[CONF_FOLDER_ID], ItemUpdate(name="newFolder")
    )
    expect(config_entry.data[CONF_FOLDER_NAME]).to_equal("newFolder")


@test
async def reconfigure_flow_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    client: MagicMock = Depends(mock_onedrive_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow errors."""
    config_entry.add_to_hass(hass)
    await hass.async_block_till_done()

    result = await config_entry.start_reconfigure_flow(hass)
    await _do_get_token(hass, result, client_factory, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure_folder")

    client.update_drive_item.side_effect = OneDriveException()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "newFolder"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure_folder")
    expect(result["errors"]).to_equal({"base": "folder_rename_error"})

    client.update_drive_item.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_FOLDER_NAME: "newFolder"}
    )

    expect(config_entry.data[CONF_FOLDER_NAME]).to_equal("newFolder")


@test
async def reconfigure_flow_id_changed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_onedrive_client),
    approot: AppRoot = Depends(mock_approot),
) -> None:
    """Test that the reconfigure flow fails on a different drive id."""
    approot.parent_reference.drive_id = "other_drive_id"

    config_entry.add_to_hass(hass)
    await hass.async_block_till_done()

    result = await config_entry.start_reconfigure_flow(hass)
    await _do_get_token(hass, result, client_factory, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_drive")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_onedrive_client),
) -> None:
    """Test options flow."""
    await setup_integration(hass, config_entry)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_DELETE_PERMANENTLY: True},
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["data"]).to_equal({CONF_DELETE_PERMANENTLY: True})
