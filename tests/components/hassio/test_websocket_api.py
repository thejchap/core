"""Test websocket API."""

from collections.abc import AsyncGenerator, Generator
from dataclasses import replace
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from aiohasupervisor import SupervisorError
from aiohasupervisor.models import HomeAssistantUpdateOptions, StoreAddonUpdate
from syrupy.assertion import SnapshotAssertion
from tryke import Depends, expect, fixture, test

from homeassistant.components.backup import BackupManagerError, ManagerBackup

# pylint: disable-next=hass-component-root-import
from homeassistant.components.backup.manager import AgentBackupStatus
from homeassistant.components.hassio import DOMAIN
from homeassistant.components.hassio.const import (
    ATTR_DATA,
    ATTR_ENDPOINT,
    ATTR_METHOD,
    ATTR_PARAMS,
    ATTR_WS_EVENT,
    DATA_CONFIG_STORE,
    EVENT_SUPERVISOR_EVENT,
    WS_ID,
    WS_TYPE,
    WS_TYPE_API,
    WS_TYPE_SUBSCRIBE,
)
from homeassistant.const import __version__ as HAVERSION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.setup import async_setup_component

from ._fixtures import (
    addon_info as addon_info_fixture,
    addons_list as addons_list_fixture,
    homeassistant_info as homeassistant_info_fixture,
    host_info as host_info_fixture,
    ingress_panels as ingress_panels_fixture,
    network_info as network_info_fixture,
    os_info as os_info_fixture,
    resolution_info as resolution_info_fixture,
    store_info as store_info_fixture,
    supervisor_client as supervisor_client_fixture,
    supervisor_info as supervisor_info_fixture,
    supervisor_is_connected as supervisor_is_connected_fixture,
    supervisor_root_info as supervisor_root_info_fixture,
)

from tests.common import MockConfigEntry, MockUser, async_mock_signal
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network as mock_network_fixture,
)
from tests.hass_tryke_helpers import snapshot as snapshot_fixture
from tests.test_util.aiohttp import AiohttpClientMocker

MOCK_ENVIRON = {"SUPERVISOR": "127.0.0.1", "SUPERVISOR_TOKEN": "abcdefgh"}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network_fixture),
    _aiomock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> int:
    """Ensure aioclient_mock patch is active before HA sessions are created."""
    return 0


@fixture
def update_addon(
    supervisor_client: AsyncMock = Depends(supervisor_client_fixture),
) -> AsyncMock:
    """Mock update add-on."""
    return supervisor_client.store.update_addon


@fixture
def mock_all(
    _trigger: int = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    supervisor_is_connected: AsyncMock = Depends(supervisor_is_connected_fixture),
    resolution_info: AsyncMock = Depends(resolution_info_fixture),
    addon_info: AsyncMock = Depends(addon_info_fixture),
    host_info: AsyncMock = Depends(host_info_fixture),
    supervisor_root_info: AsyncMock = Depends(supervisor_root_info_fixture),
    homeassistant_info: AsyncMock = Depends(homeassistant_info_fixture),
    supervisor_info: AsyncMock = Depends(supervisor_info_fixture),
    addons_list: AsyncMock = Depends(addons_list_fixture),
    network_info: AsyncMock = Depends(network_info_fixture),
    os_info: AsyncMock = Depends(os_info_fixture),
    store_info: AsyncMock = Depends(store_info_fixture),
    ingress_panels: AsyncMock = Depends(ingress_panels_fixture),
) -> None:
    """Mock all setup requests."""
    supervisor_root_info.return_value = replace(
        supervisor_root_info.return_value, hassos=None
    )
    addons_list.return_value.pop(1)
    addon_info.return_value.version = "2.0.0"
    addon_info.return_value.version_latest = "2.0.1"
    addon_info.return_value.update_available = True

    # The websocket API still relies on HassIO.send_command for all Supervisor API calls
    # So must keep some aioclient mocks normally covered by aiohasupervisor in component
    aioclient_mock.get(
        "http://127.0.0.1/supervisor/info",
        json={
            "result": "ok",
            "data": {
                "version": "1.0.0",
                "version_latest": "1.0.0",
                "auto_update": True,
                "addons": [
                    {
                        "name": "test",
                        "state": "started",
                        "slug": "test",
                        "installed": True,
                        "update_available": True,
                        "icon": False,
                        "version": "2.0.0",
                        "version_latest": "2.0.1",
                        "repository": "core",
                        "url": "https://github.com/home-assistant/addons/test",
                    },
                ],
            },
        },
    )


@fixture
def hassio_env(
    supervisor_is_connected: AsyncMock = Depends(supervisor_is_connected_fixture),
    supervisor_root_info: AsyncMock = Depends(supervisor_root_info_fixture),
) -> Generator[None]:
    """Inject hassio env vars."""
    supervisor_root_info.side_effect = SupervisorError()
    with (
        patch.dict(os.environ, {"SUPERVISOR": "127.0.0.1"}),
        patch.dict(os.environ, {"SUPERVISOR_TOKEN": "123456"}),
    ):
        yield


@fixture
def hass_supervisor_ws_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
):
    """Return a websocket client authenticated as the Supervisor user."""

    async def create_client():
        hassio_user_id = hass.data[DATA_CONFIG_STORE].data.hassio_user
        hassio_user = await hass.auth.async_get_user(hassio_user_id)
        assert hassio_user
        assert hassio_user.refresh_tokens
        refresh_token = next(iter(hassio_user.refresh_tokens.values()))
        access_token = hass.auth.async_create_access_token(refresh_token)
        return await hass_ws_client(hass, access_token=access_token)

    return create_client


async def setup_backup_integration(hass: HomeAssistant) -> None:
    """Set up the backup integration."""
    assert await async_setup_component(hass, "backup", {})
    await hass.async_block_till_done()


@test
async def ws_subscription(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test websocket subscription."""
    expect(await async_setup_component(hass, "hassio", {})).to_be(True)
    client = await hass_supervisor_ws_client()
    await client.send_json({WS_ID: 5, WS_TYPE: WS_TYPE_SUBSCRIBE})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)

    calls = async_mock_signal(hass, EVENT_SUPERVISOR_EVENT)
    async_dispatcher_send(hass, EVENT_SUPERVISOR_EVENT, {"lorem": "ipsum"})

    response = await client.receive_json()
    expect(response["event"]["lorem"]).to_equal("ipsum")
    expect(len(calls)).to_equal(1)

    await client.send_json(
        {
            WS_ID: 6,
            WS_TYPE: "supervisor/event",
            ATTR_DATA: {ATTR_WS_EVENT: "test", "lorem": "ipsum"},
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(len(calls)).to_equal(2)

    response = await client.receive_json()
    expect(response["event"]["lorem"]).to_equal("ipsum")

    # Unsubscribe
    await client.send_json({WS_ID: 7, WS_TYPE: "unsubscribe_events", "subscription": 5})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)


@test
async def admin_non_supervisor_publish_supervisor_event_failure(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test non admin user cannot publish supervisor event."""
    hass_admin_user.groups = []
    expect(await async_setup_component(hass, "hassio", {})).to_be(True)
    client = await hass_ws_client(hass)

    await client.send_json(
        {
            WS_ID: 1,
            WS_TYPE: "supervisor/event",
            ATTR_DATA: {ATTR_WS_EVENT: "test", "lorem": "ipsum"},
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]["message"]).to_equal("Only allowed as Supervisor")


@test
async def websocket_supervisor_api(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test Supervisor websocket api."""
    expect(await async_setup_component(hass, "hassio", {})).to_be(True)
    websocket_client = await hass_ws_client(hass)
    aioclient_mock.post(
        "http://127.0.0.1/backups/new/partial",
        json={"result": "ok", "data": {"slug": "sn_slug"}},
    )

    await websocket_client.send_json(
        {
            WS_ID: 1,
            WS_TYPE: WS_TYPE_API,
            ATTR_ENDPOINT: "/backups/new/partial",
            ATTR_METHOD: "post",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["result"]["slug"]).to_equal("sn_slug")

    await websocket_client.send_json(
        {
            WS_ID: 2,
            WS_TYPE: WS_TYPE_API,
            ATTR_ENDPOINT: "/supervisor/info",
            ATTR_METHOD: "get",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["result"]["version_latest"]).to_equal("1.0.0")

    expect(aioclient_mock.mock_calls[-1][3]).to_equal(
        {
            "X-Hass-Source": "core.websocket_api",
            "Authorization": "Bearer 123456",
        }
    )


@test
async def websocket_supervisor_api_with_params(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test Supervisor websocket api with query params."""
    expect(await async_setup_component(hass, "hassio", {})).to_be(True)
    websocket_client = await hass_ws_client(hass)
    aioclient_mock.get(
        "http://127.0.0.1/backups/backup_id/info",
        json={"result": "ok", "data": {"slug": "backup_id"}},
    )

    await websocket_client.send_json(
        {
            WS_ID: 1,
            WS_TYPE: WS_TYPE_API,
            ATTR_ENDPOINT: "/backups/backup_id/info",
            ATTR_METHOD: "get",
            ATTR_PARAMS: {"extra_info": "true"},
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["result"]["slug"]).to_equal("backup_id")

    # Verify the params were passed to the request URL
    expect(dict(aioclient_mock.mock_calls[-1][1].query)).to_equal(
        {"extra_info": "true"}
    )


@test
async def websocket_supervisor_api_error(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test Supervisor websocket api error."""
    expect(await async_setup_component(hass, "hassio", {})).to_be(True)
    websocket_client = await hass_ws_client(hass)
    aioclient_mock.get(
        "http://127.0.0.1/ping",
        json={"result": "error", "message": "example error"},
        status=400,
    )

    await websocket_client.send_json(
        {
            WS_ID: 1,
            WS_TYPE: WS_TYPE_API,
            ATTR_ENDPOINT: "/ping",
            ATTR_METHOD: "get",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["error"]["code"]).to_equal("unknown_error")
    expect(msg["error"]["message"]).to_equal("example error")


@test
async def websocket_supervisor_api_error_without_msg(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test Supervisor websocket api error."""
    expect(await async_setup_component(hass, "hassio", {})).to_be(True)
    websocket_client = await hass_ws_client(hass)
    aioclient_mock.get(
        "http://127.0.0.1/ping",
        json={},
        status=400,
    )

    await websocket_client.send_json(
        {
            WS_ID: 1,
            WS_TYPE: WS_TYPE_API,
            ATTR_ENDPOINT: "/ping",
            ATTR_METHOD: "get",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["error"]["code"]).to_equal("unknown_error")
    expect(msg["error"]["message"]).to_equal("")


@test
async def websocket_non_admin_user(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test Supervisor websocket api error."""
    hass_admin_user.groups = []
    expect(await async_setup_component(hass, "hassio", {})).to_be(True)
    websocket_client = await hass_ws_client(hass)
    aioclient_mock.get(
        "http://127.0.0.1/addons/test_addon/info",
        json={
            "result": "ok",
            "data": {
                "name": "test",
                "state": "started",
                "slug": "test_addon",
                "version": "2.0.0",
                "ingress_url": "http://127.0.0.1/ingress/test_addon",
                "options": {"option1": "value1", "option2": "value2"},
            },
        },
    )
    aioclient_mock.get(
        "http://127.0.0.1/ingress/session",
        json={"result": "ok", "data": {}},
    )
    aioclient_mock.get(
        "http://127.0.0.1/ingress/validate_session",
        json={"result": "ok", "data": {}},
    )

    # Should return the fields frontend needs (name, version, state, slug and ingress_url)
    # but not options, as user is not admin and options can contain sensitive information
    await websocket_client.send_json(
        {
            WS_ID: 1,
            WS_TYPE: WS_TYPE_API,
            ATTR_ENDPOINT: "/addons/test_addon/info",
            ATTR_METHOD: "get",
        }
    )
    msg = await websocket_client.receive_json()
    expect(msg["result"]).to_equal(
        {
            "name": "test",
            "state": "started",
            "slug": "test_addon",
            "version": "2.0.0",
            "ingress_url": "http://127.0.0.1/ingress/test_addon",
        }
    )
    expect("options" in msg["result"]).to_be(False)

    await websocket_client.send_json(
        {
            WS_ID: 2,
            WS_TYPE: WS_TYPE_API,
            ATTR_ENDPOINT: "/ingress/session",
            ATTR_METHOD: "get",
        }
    )
    msg = await websocket_client.receive_json()
    expect(msg["result"]).to_equal({})

    await websocket_client.send_json(
        {
            WS_ID: 3,
            WS_TYPE: WS_TYPE_API,
            ATTR_ENDPOINT: "/ingress/validate_session",
            ATTR_METHOD: "get",
        }
    )
    msg = await websocket_client.receive_json()
    expect(msg["result"]).to_equal({})

    await websocket_client.send_json(
        {
            WS_ID: 4,
            WS_TYPE: WS_TYPE_API,
            ATTR_ENDPOINT: "/supervisor/info",
            ATTR_METHOD: "get",
        }
    )

    msg = await websocket_client.receive_json()
    expect(msg["error"]["message"]).to_equal("Unauthorized")


@test
async def update_addon_test(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test updating addon."""
    client = await hass_ws_client(hass)
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        expect(result).to_be(True)
    await hass.async_block_till_done()

    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
    ) as mock_create_backup:
        await client.send_json_auto_id(
            {"type": "hassio/update/addon", "addon": "test", "backup": False}
        )
        result = await client.receive_json()
        expect(result["success"]).to_be(True)
    mock_create_backup.assert_not_called()
    update_addon.assert_called_once_with("test", StoreAddonUpdate(backup=False))


@test.cases(
    test.case(
        "no_commands_no_mount",
        commands=[],
        default_mount=None,
        expected_kwargs={
            "agent_ids": ["hassio.local"],
            "extra_metadata": {"supervisor.addon_update": "test"},
            "include_addons": ["test"],
            "include_all_addons": False,
            "include_database": False,
            "include_folders": None,
            "include_homeassistant": False,
            "name": "test 2.0.0",
            "password": None,
        },
    ),
    test.case(
        "no_commands_my_nas",
        commands=[],
        default_mount="my_nas",
        expected_kwargs={
            "agent_ids": ["hassio.my_nas"],
            "extra_metadata": {"supervisor.addon_update": "test"},
            "include_addons": ["test"],
            "include_all_addons": False,
            "include_database": False,
            "include_folders": None,
            "include_homeassistant": False,
            "name": "test 2.0.0",
            "password": None,
        },
    ),
    test.case(
        "with_backup_config_update",
        commands=[
            {
                "type": "backup/config/update",
                "create_backup": {
                    "agent_ids": ["test-agent"],
                    "include_addons": ["my-addon"],
                    "include_all_addons": True,
                    "include_database": False,
                    "include_folders": ["share"],
                    "name": "cool_backup",
                    "password": "hunter2",
                },
            },
        ],
        default_mount=None,
        expected_kwargs={
            "agent_ids": ["hassio.local"],
            "extra_metadata": {"supervisor.addon_update": "test"},
            "include_addons": ["test"],
            "include_all_addons": False,
            "include_database": False,
            "include_folders": None,
            "include_homeassistant": False,
            "name": "test 2.0.0",
            "password": "hunter2",
        },
    ),
)
async def update_addon_with_backup(
    commands: list[dict[str, Any]],
    default_mount: str | None,
    expected_kwargs: dict[str, Any],
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client_fixture),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test updating addon with backup."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        expect(result).to_be(True)
    await setup_backup_integration(hass)

    client = await hass_ws_client(hass)
    for command in commands:
        await client.send_json_auto_id(command)
        result = await client.receive_json()
        expect(result["success"]).to_be(True)

    supervisor_client.mounts.info.return_value.default_backup_mount = default_mount
    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
    ) as mock_create_backup:
        await client.send_json_auto_id(
            {"type": "hassio/update/addon", "addon": "test", "backup": True}
        )
        result = await client.receive_json()
        expect(result["success"]).to_be(True)
    mock_create_backup.assert_called_once_with(**expected_kwargs)
    update_addon.assert_called_once_with("test", StoreAddonUpdate(backup=False))


def _backup_mocks_a() -> dict[str, Any]:
    """Build the standard set of MagicMock backups for retention tests."""
    return {
        "backup-1": MagicMock(
            agents={"hassio.local": MagicMock(spec=AgentBackupStatus)},
            date="2024-11-10T04:45:00+01:00",
            with_automatic_settings=True,
            spec=ManagerBackup,
        ),
        "backup-2": MagicMock(
            agents={"hassio.local": MagicMock(spec=AgentBackupStatus)},
            date="2024-11-11T04:45:00+01:00",
            with_automatic_settings=False,
            spec=ManagerBackup,
        ),
        "backup-3": MagicMock(
            agents={"hassio.local": MagicMock(spec=AgentBackupStatus)},
            date="2024-11-11T04:45:00+01:00",
            extra_metadata={"supervisor.addon_update": "other"},
            with_automatic_settings=True,
            spec=ManagerBackup,
        ),
        "backup-4": MagicMock(
            agents={"hassio.local": MagicMock(spec=AgentBackupStatus)},
            date="2024-11-11T04:45:00+01:00",
            extra_metadata={"supervisor.addon_update": "other"},
            with_automatic_settings=True,
            spec=ManagerBackup,
        ),
        "backup-5": MagicMock(
            agents={"hassio.local": MagicMock(spec=AgentBackupStatus)},
            date="2024-11-11T04:45:00+01:00",
            extra_metadata={"supervisor.addon_update": "test"},
            with_automatic_settings=True,
            spec=ManagerBackup,
        ),
        "backup-6": MagicMock(
            agents={"hassio.local": MagicMock(spec=AgentBackupStatus)},
            date="2024-11-12T04:45:00+01:00",
            extra_metadata={"supervisor.addon_update": "test"},
            with_automatic_settings=True,
            spec=ManagerBackup,
        ),
    }


@test.cases(
    test.case("no_ws_no_backups", ws_commands=[], backups={}, removed_backups=[]),
    test.case(
        "no_ws_with_backups",
        ws_commands=[],
        backups=None,  # use _backup_mocks_a()
        removed_backups=["backup-5"],
    ),
    test.case(
        "retain_2_with_backups",
        ws_commands=[
            {"type": "hassio/update/config/update", "add_on_backup_retain_copies": 2}
        ],
        backups=None,  # use _backup_mocks_a()
        removed_backups=[],
    ),
)
async def update_addon_with_backup_removes_old_backups(
    ws_commands: list[dict[str, Any]],
    backups: dict[str, ManagerBackup] | None,
    removed_backups: list[str],
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client_fixture),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test updating addon update entity."""
    if backups is None:
        backups = _backup_mocks_a()
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        expect(result).to_be(True)
    await setup_backup_integration(hass)

    client = await hass_ws_client(hass)

    for command in ws_commands:
        await client.send_json_auto_id(command)
        result = await client.receive_json()
        expect(result["success"]).to_be(True)

    supervisor_client.mounts.info.return_value.default_backup_mount = None
    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_create_backup",
        ) as mock_create_backup,
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_delete_backup",
            autospec=True,
            return_value={},
        ) as async_delete_backup,
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_get_backups",
            return_value=(backups, {}),
        ),
    ):
        await client.send_json_auto_id(
            {"type": "hassio/update/addon", "addon": "test", "backup": True}
        )
        result = await client.receive_json()
        expect(result["success"]).to_be(True)
    mock_create_backup.assert_called_once_with(
        agent_ids=["hassio.local"],
        extra_metadata={"supervisor.addon_update": "test"},
        include_addons=["test"],
        include_all_addons=False,
        include_database=False,
        include_folders=None,
        include_homeassistant=False,
        name="test 2.0.0",
        password=None,
    )
    expect(len(async_delete_backup.mock_calls)).to_equal(len(removed_backups))
    for call in async_delete_backup.mock_calls:
        expect(call.args[1] in removed_backups).to_be(True)
    update_addon.assert_called_once_with("test", StoreAddonUpdate(backup=False))


@test
async def update_core(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client_fixture),
) -> None:
    """Test updating core."""
    client = await hass_ws_client(hass)
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        expect(result).to_be(True)
    await hass.async_block_till_done()

    supervisor_client.homeassistant.update.return_value = None
    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
    ) as mock_create_backup:
        await client.send_json_auto_id({"type": "hassio/update/core", "backup": False})
        result = await client.receive_json()
        expect(result["success"]).to_be(True)
    mock_create_backup.assert_not_called()
    supervisor_client.homeassistant.update.assert_called_once_with(
        HomeAssistantUpdateOptions(version=None, backup=False)
    )


@test.cases(
    test.case(
        "no_commands_no_mount",
        commands=[],
        default_mount=None,
        expected_kwargs={
            "agent_ids": ["hassio.local"],
            "include_addons": None,
            "include_all_addons": False,
            "include_database": True,
            "include_folders": None,
            "include_homeassistant": True,
            "name": f"Home Assistant Core {HAVERSION}",
            "password": None,
        },
    ),
    test.case(
        "no_commands_my_nas",
        commands=[],
        default_mount="my_nas",
        expected_kwargs={
            "agent_ids": ["hassio.my_nas"],
            "include_addons": None,
            "include_all_addons": False,
            "include_database": True,
            "include_folders": None,
            "include_homeassistant": True,
            "name": f"Home Assistant Core {HAVERSION}",
            "password": None,
        },
    ),
    test.case(
        "with_backup_config_update",
        commands=[
            {
                "type": "backup/config/update",
                "create_backup": {
                    "agent_ids": ["test-agent"],
                    "include_addons": ["my-addon"],
                    "include_all_addons": True,
                    "include_database": False,
                    "include_folders": ["share"],
                    "name": "cool_backup",
                    "password": "hunter2",
                },
            },
        ],
        default_mount=None,
        expected_kwargs={
            "agent_ids": ["test-agent"],
            "include_addons": ["my-addon"],
            "include_all_addons": True,
            "include_database": False,
            "include_folders": ["share"],
            "include_homeassistant": True,
            "name": "cool_backup",
            "password": "hunter2",
            "with_automatic_settings": True,
        },
    ),
)
async def update_core_with_backup(
    commands: list[dict[str, Any]],
    default_mount: str | None,
    expected_kwargs: dict[str, Any],
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client_fixture),
) -> None:
    """Test updating core with backup."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        expect(result).to_be(True)
    await setup_backup_integration(hass)

    client = await hass_ws_client(hass)
    for command in commands:
        await client.send_json_auto_id(command)
        result = await client.receive_json()
        expect(result["success"]).to_be(True)

    supervisor_client.homeassistant.update.return_value = None
    supervisor_client.mounts.info.return_value.default_backup_mount = default_mount
    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
    ) as mock_create_backup:
        await client.send_json_auto_id({"type": "hassio/update/core", "backup": True})
        result = await client.receive_json()
        expect(result["success"]).to_be(True)
    mock_create_backup.assert_called_once_with(**expected_kwargs)
    supervisor_client.homeassistant.update.assert_called_once_with(
        HomeAssistantUpdateOptions(version=None, backup=False)
    )


@test
async def update_addon_with_error(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test updating addon with error."""
    client = await hass_ws_client(hass)
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        expect(
            await async_setup_component(
                hass,
                "hassio",
                {
                    "http": {"server_port": 9999, "server_host": "127.0.0.1"},
                    "hassio": {},
                },
            )
        ).to_be(True)
    await hass.async_block_till_done()

    update_addon.side_effect = SupervisorError
    await client.send_json_auto_id(
        {"type": "hassio/update/addon", "addon": "test", "backup": False}
    )
    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]).to_equal(
        {"code": "home_assistant_error", "message": "Error updating test: "}
    )


@test.cases(
    test.case(
        "create_backup_error",
        create_backup_error=BackupManagerError,
        delete_filtered_backups_error=None,
        message="Error creating backup: ",
    ),
    test.case(
        "delete_filtered_backups_error",
        create_backup_error=None,
        delete_filtered_backups_error=BackupManagerError,
        message="Error deleting old backups: ",
    ),
)
async def update_addon_with_backup_and_error(
    create_backup_error: type[Exception] | None,
    delete_filtered_backups_error: type[Exception] | None,
    message: str,
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client_fixture),
) -> None:
    """Test updating addon with backup and error."""
    client = await hass_ws_client(hass)
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        expect(result).to_be(True)
    await setup_backup_integration(hass)

    supervisor_client.homeassistant.update.return_value = None
    supervisor_client.mounts.info.return_value.default_backup_mount = None
    with (
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_create_backup",
            side_effect=create_backup_error,
        ),
        patch(
            "homeassistant.components.backup.manager.BackupManager.async_delete_filtered_backups",
            side_effect=delete_filtered_backups_error,
        ),
    ):
        await client.send_json_auto_id(
            {"type": "hassio/update/addon", "addon": "test", "backup": True}
        )
        result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]).to_equal(
        {"code": "home_assistant_error", "message": message}
    )


@test
async def update_core_with_error(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client_fixture),
) -> None:
    """Test updating core with error."""
    client = await hass_ws_client(hass)
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        expect(
            await async_setup_component(
                hass,
                "hassio",
                {
                    "http": {"server_port": 9999, "server_host": "127.0.0.1"},
                    "hassio": {},
                },
            )
        ).to_be(True)
    await hass.async_block_till_done()

    supervisor_client.homeassistant.update.side_effect = SupervisorError
    await client.send_json_auto_id({"type": "hassio/update/core", "backup": False})
    result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]).to_equal(
        {
            "code": "home_assistant_error",
            "message": "Error updating Home Assistant Core: ",
        }
    )


@test
async def update_core_with_backup_and_error(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client_fixture),
) -> None:
    """Test updating core with backup and error."""
    client = await hass_ws_client(hass)
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        expect(result).to_be(True)
    await setup_backup_integration(hass)

    supervisor_client.homeassistant.update.return_value = None
    supervisor_client.mounts.info.return_value.default_backup_mount = None
    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
        side_effect=BackupManagerError,
    ):
        await client.send_json_auto_id({"type": "hassio/update/core", "backup": True})
        result = await client.receive_json()
    expect(result["success"]).to_be(False)
    expect(result["error"]).to_equal(
        {"code": "home_assistant_error", "message": "Error creating backup: "}
    )


@test
async def read_update_config(
    _mock_all: None = Depends(mock_all),
    _hassio_env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client_fixture),
    snapshot: SnapshotAssertion = Depends(snapshot_fixture),
) -> None:
    """Test read and update config."""
    expect(await async_setup_component(hass, "hassio", {})).to_be(True)
    websocket_client = await hass_ws_client(hass)

    await websocket_client.send_json_auto_id({"type": "hassio/update/config/info"})
    expect(await websocket_client.receive_json()).to_equal(snapshot)

    await websocket_client.send_json_auto_id(
        {
            "type": "hassio/update/config/update",
            "add_on_backup_before_update": True,
            "add_on_backup_retain_copies": 2,
            "core_backup_before_update": True,
        }
    )
    expect(await websocket_client.receive_json()).to_equal(snapshot)

    await websocket_client.send_json_auto_id({"type": "hassio/update/config/info"})
    expect(await websocket_client.receive_json()).to_equal(snapshot)
