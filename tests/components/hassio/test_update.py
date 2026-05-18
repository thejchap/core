"""The tests for the hassio update entities."""

from collections.abc import Generator
from dataclasses import replace
from datetime import datetime, timedelta
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

from aiohasupervisor import (
    SupervisorBadRequestError,
    SupervisorError,
    SupervisorNotFoundError,
)
from aiohasupervisor.models import (
    AddonState,
    HomeAssistantUpdateOptions,
    InstalledAddonComplete,
    Job,
    JobsInfo,
    OSUpdate,
    StoreAddonUpdate,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.backup import BackupManagerError, ManagerBackup

# pylint: disable-next=hass-component-root-import
from homeassistant.components.backup.manager import AgentBackupStatus
from homeassistant.components.hassio import DOMAIN
from homeassistant.components.hassio.const import (
    DATA_CONFIG_STORE,
    REQUEST_REFRESH_DELAY,
)
from homeassistant.const import __version__ as HAVERSION
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import (
    addon_changelog,
    addon_info,
    addon_installed,
    addon_stats,
    addon_store_info,
    addons_list,
    homeassistant_info,
    homeassistant_stats,
    host_info,
    ingress_panels,
    jobs_info,
    network_info,
    os_info,
    resolution_info,
    store_info,
    supervisor_client,
    supervisor_info,
    supervisor_root_info,
    supervisor_stats,
    update_addon,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async

MOCK_ENVIRON = {"SUPERVISOR": "127.0.0.1", "SUPERVISOR_TOKEN": "abcdefgh"}


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@fixture
def fixture_supervisor_environ() -> Generator[None]:
    """Mock os environ for supervisor."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        yield


@fixture
def mock_all(
    addon_installed: AsyncMock = Depends(addon_installed),
    _store_info: AsyncMock = Depends(store_info),
    _addon_stats: AsyncMock = Depends(addon_stats),
    _addon_changelog: AsyncMock = Depends(addon_changelog),
    _resolution_info: AsyncMock = Depends(resolution_info),
    _jobs_info: AsyncMock = Depends(jobs_info),
    _host_info: AsyncMock = Depends(host_info),
    _supervisor_root_info: AsyncMock = Depends(supervisor_root_info),
    homeassistant_info: AsyncMock = Depends(homeassistant_info),
    supervisor_info: AsyncMock = Depends(supervisor_info),
    _addons_list: AsyncMock = Depends(addons_list),
    _network_info: AsyncMock = Depends(network_info),
    os_info: AsyncMock = Depends(os_info),
    _homeassistant_stats: AsyncMock = Depends(homeassistant_stats),
    _supervisor_stats: AsyncMock = Depends(supervisor_stats),
    _ingress_panels: AsyncMock = Depends(ingress_panels),
) -> None:
    """Mock all setup requests."""
    homeassistant_info.return_value = replace(
        homeassistant_info.return_value,
        version="1.0.0dev221",
        version_latest="1.0.0dev222",
        update_available=True,
    )
    os_info.return_value = replace(
        os_info.return_value,
        version="1.0.0dev2221",
        version_latest="1.0.0dev2222",
        update_available=True,
    )
    supervisor_info.return_value = replace(
        supervisor_info.return_value,
        version_latest="1.0.1dev222",
        update_available=True,
    )

    def mock_addon_info(slug: str):
        addon = Mock(
            spec=InstalledAddonComplete,
            to_dict=addon_installed.return_value.to_dict,
            **addon_installed.return_value.to_dict(),
        )
        if slug == "test":
            addon.name = "test"
            addon.slug = "test"
            addon.version = "2.0.0"
            addon.version_latest = "2.0.1"
            addon.update_available = True
            addon.state = AddonState.STARTED
            addon.url = "https://github.com/home-assistant/addons/test"
            addon.auto_update = True
        else:
            addon.name = "test2"
            addon.slug = "test2"
            addon.version = "3.1.0"
            addon.version_latest = "3.1.0"
            addon.update_available = False
            addon.state = AddonState.STOPPED
            addon.url = "https://github.com"
            addon.auto_update = False

        return addon

    addon_installed.side_effect = mock_addon_info


@fixture
def hass_supervisor_ws_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fx),
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


async def _setup_hassio(hass: HomeAssistant) -> None:
    """Set up the hassio integration."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        assert result
    await hass.async_block_till_done()


async def setup_backup_integration(hass: HomeAssistant) -> None:
    """Set up the backup integration."""
    assert await async_setup_component(hass, "backup", {})
    await hass.async_block_till_done()


@test.cases(
    test.case(
        "operating_system",
        entity_id="update.home_assistant_operating_system_update",
        expected_state="on",
        auto_update=False,
    ),
    test.case(
        "supervisor",
        entity_id="update.home_assistant_supervisor_update",
        expected_state="on",
        auto_update=True,
    ),
    test.case(
        "core",
        entity_id="update.home_assistant_core_update",
        expected_state="on",
        auto_update=False,
    ),
    test.case(
        "test",
        entity_id="update.test_update",
        expected_state="on",
        auto_update=True,
    ),
    test.case(
        "test2",
        entity_id="update.test2_update",
        expected_state="off",
        auto_update=False,
    ),
)
async def update_entities(
    entity_id: str,
    expected_state: str,
    auto_update: bool,
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    addon_installed: AsyncMock = Depends(addon_installed),
) -> None:
    """Test update entities."""
    addon_installed.return_value.auto_update = auto_update
    await _setup_hassio(hass)

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(expected_state)
    expect(state.attributes["auto_update"]).to_be(auto_update)


@test
async def update_addon_test(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test updating addon update entity."""
    await _setup_hassio(hass)

    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
    ) as mock_create_backup:
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.test_update"},
            blocking=True,
        )
    mock_create_backup.assert_not_called()
    update_addon.assert_called_once_with("test", StoreAddonUpdate(backup=False))


@test
async def update_addon_progress(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test progress reporting for addon update."""
    await _setup_hassio(hass)

    client = await hass_supervisor_ws_client()
    message_id = 0
    job_uuid = uuid4().hex

    def make_job_message(progress: float, done: bool | None):
        nonlocal message_id
        message_id += 1
        return {
            "id": message_id,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "uuid": job_uuid,
                    "created": "2025-09-29T00:00:00.000000+00:00",
                    "name": "addon_manager_update",
                    "reference": "test",
                    "progress": progress,
                    "done": done,
                    "stage": None,
                    "extra": {"total": 1234567890} if progress > 0 else None,
                    "errors": [],
                },
            },
        }

    await client.send_json(make_job_message(progress=0, done=None))
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(
        hass.states.get("update.test_update").attributes.get("in_progress")
    ).to_be(False)
    expect(
        hass.states.get("update.test_update").attributes.get("update_percentage")
    ).to_be(None)

    await client.send_json(make_job_message(progress=5, done=False))
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(
        hass.states.get("update.test_update").attributes.get("in_progress")
    ).to_be(True)
    expect(
        hass.states.get("update.test_update").attributes.get("update_percentage")
    ).to_equal(5)

    await client.send_json(make_job_message(progress=50, done=False))
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(
        hass.states.get("update.test_update").attributes.get("in_progress")
    ).to_be(True)
    expect(
        hass.states.get("update.test_update").attributes.get("update_percentage")
    ).to_equal(50)

    await client.send_json(make_job_message(progress=100, done=True))
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(
        hass.states.get("update.test_update").attributes.get("in_progress")
    ).to_be(False)
    expect(
        hass.states.get("update.test_update").attributes.get("update_percentage")
    ).to_be(None)


@test
async def addon_update_progress_startup(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    jobs_info: AsyncMock = Depends(jobs_info),
) -> None:
    """Test addon update in progress during home assistant startup."""
    jobs_info.return_value = JobsInfo(
        ignore_conditions=[],
        jobs=[
            Job(
                name="addon_manager_update",
                reference="test",
                uuid=uuid4().hex,
                progress=50,
                stage=None,
                done=False,
                errors=[],
                created=datetime.now(),
                child_jobs=[],
                extra={"total": 1234567890},
            )
        ],
    )

    await _setup_hassio(hass)

    expect(
        hass.states.get("update.test_update").attributes.get("in_progress")
    ).to_be(True)
    expect(
        hass.states.get("update.test_update").attributes.get("update_percentage")
    ).to_equal(50)


@test.cases(
    test.case(
        "no_commands_default_mount",
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
        "config_update",
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
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test updating addon update entity."""
    await _setup_hassio(hass)
    await setup_backup_integration(hass)

    client = await hass_ws_client(hass)
    for command in commands:
        await client.send_json_auto_id(command)
        result = await client.receive_json()
        expect(result["success"]).to_be_truthy()

    supervisor_client.mounts.info.return_value.default_backup_mount = default_mount
    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
    ) as mock_create_backup:
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.test_update", "backup": True},
            blocking=True,
        )
    mock_create_backup.assert_called_once_with(**expected_kwargs)
    update_addon.assert_called_once_with("test", StoreAddonUpdate(backup=False))


@test.cases(
    test.case("empty", backups={}, removed_backups=[]),
    test.case(
        "many",
        backups={
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
        },
        removed_backups=["backup-5"],
    ),
)
async def update_addon_with_backup_removes_old_backups(
    backups: dict[str, ManagerBackup],
    removed_backups: list[str],
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test updating addon update entity."""
    await _setup_hassio(hass)
    await setup_backup_integration(hass)

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
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.test_update", "backup": True},
            blocking=True,
        )
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
        expect(call.args[1] in removed_backups).to_be_truthy()
    update_addon.assert_called_once_with("test", StoreAddonUpdate(backup=False))


@test
async def update_os(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test updating OS update entity."""
    await _setup_hassio(hass)

    supervisor_client.os.update.return_value = None
    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
    ) as mock_create_backup:
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.home_assistant_operating_system_update"},
            blocking=True,
        )
    mock_create_backup.assert_not_called()
    supervisor_client.os.update.assert_called_once_with(OSUpdate(version=None))


@test.cases(
    test.case(
        "no_commands_default_mount",
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
        "config_update",
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
async def update_os_with_backup(
    commands: list[dict[str, Any]],
    default_mount: str | None,
    expected_kwargs: dict[str, Any],
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test updating OS update entity."""
    await _setup_hassio(hass)
    await setup_backup_integration(hass)

    client = await hass_ws_client(hass)
    for command in commands:
        await client.send_json_auto_id(command)
        result = await client.receive_json()
        expect(result["success"]).to_be_truthy()

    supervisor_client.os.update.return_value = None
    supervisor_client.mounts.info.return_value.default_backup_mount = default_mount
    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
    ) as mock_create_backup:
        await hass.services.async_call(
            "update",
            "install",
            {
                "entity_id": "update.home_assistant_operating_system_update",
                "backup": True,
            },
            blocking=True,
        )
    mock_create_backup.assert_called_once_with(**expected_kwargs)
    supervisor_client.os.update.assert_called_once_with(OSUpdate(version=None))


@test
async def update_core(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test updating core update entity."""
    await _setup_hassio(hass)

    supervisor_client.homeassistant.update.return_value = None
    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
    ) as mock_create_backup:
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.home_assistant_core_update"},
            blocking=True,
        )
    mock_create_backup.assert_not_called()
    supervisor_client.homeassistant.update.assert_called_once_with(
        HomeAssistantUpdateOptions(version=None, backup=False)
    )


@test
async def update_core_progress(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test progress reporting for core update."""
    await _setup_hassio(hass)

    client = await hass_supervisor_ws_client()
    message_id = 0
    job_uuid = uuid4().hex

    def make_job_message(
        progress: float, done: bool | None, errors: list[dict[str, str]] | None = None
    ):
        nonlocal message_id
        message_id += 1
        return {
            "id": message_id,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "uuid": job_uuid,
                    "created": "2025-09-29T00:00:00.000000+00:00",
                    "name": "home_assistant_core_update",
                    "reference": None,
                    "progress": progress,
                    "done": done,
                    "stage": None,
                    "extra": {"total": 1234567890} if progress > 0 else None,
                    "errors": errors or [],
                },
            },
        }

    await client.send_json(make_job_message(progress=0, done=None))
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "in_progress"
        )
    ).to_be(False)
    expect(
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "update_percentage"
        )
    ).to_be(None)

    await client.send_json(make_job_message(progress=5, done=False))
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "in_progress"
        )
    ).to_be(True)
    expect(
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "update_percentage"
        )
    ).to_equal(5)

    await client.send_json(make_job_message(progress=50, done=False))
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "in_progress"
        )
    ).to_be(True)
    expect(
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "update_percentage"
        )
    ).to_equal(50)

    await client.send_json(
        make_job_message(
            progress=70,
            done=True,
            errors=[
                {"type": "HomeAssistantUpdateError", "message": "bad", "stage": None}
            ],
        )
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "in_progress"
        )
    ).to_be(False)
    expect(
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "update_percentage"
        )
    ).to_be(None)


@test
async def core_update_progress_startup(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    jobs_info: AsyncMock = Depends(jobs_info),
) -> None:
    """Test core update in progress during home assistant startup."""
    jobs_info.return_value = JobsInfo(
        ignore_conditions=[],
        jobs=[
            Job(
                name="home_assistant_core_update",
                reference=None,
                uuid=uuid4().hex,
                progress=50,
                stage=None,
                done=False,
                errors=[],
                created=datetime.now(),
                child_jobs=[],
                extra={"total": 1234567890},
            )
        ],
    )

    await _setup_hassio(hass)

    expect(
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "in_progress"
        )
    ).to_be(True)
    expect(
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "update_percentage"
        )
    ).to_equal(50)


@test.cases(
    test.case(
        "no_commands_default_mount",
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
        "config_update",
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
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test updating core update entity."""
    await _setup_hassio(hass)
    await setup_backup_integration(hass)

    client = await hass_ws_client(hass)
    for command in commands:
        await client.send_json_auto_id(command)
        result = await client.receive_json()
        expect(result["success"]).to_be_truthy()

    supervisor_client.homeassistant.update.return_value = None
    supervisor_client.mounts.info.return_value.default_backup_mount = default_mount
    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
    ) as mock_create_backup:
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.home_assistant_core_update", "backup": True},
            blocking=True,
        )
    mock_create_backup.assert_called_once_with(**expected_kwargs)
    supervisor_client.homeassistant.update.assert_called_once_with(
        HomeAssistantUpdateOptions(version=None, backup=False)
    )


@test
async def update_core_sets_progress_immediately(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    _supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test core update sets in_progress immediately when install starts."""
    await _setup_hassio(hass)

    state = hass.states.get("update.home_assistant_core_update")
    expect(state.attributes.get("in_progress")).to_be(False)

    async def check_progress(
        hass: HomeAssistant, version: str | None, backup: bool
    ) -> None:
        assert (
            hass.states.get("update.home_assistant_core_update").attributes.get(
                "in_progress"
            )
            is True
        )

    with patch(
        "homeassistant.components.hassio.update.update_core",
        side_effect=check_progress,
    ) as mock_update:
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.home_assistant_core_update", "backup": True},
            blocking=True,
        )

    mock_update.assert_called_once()


@test
async def update_core_resets_progress_on_error(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    _supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test core update resets in_progress to False when update fails."""
    await _setup_hassio(hass)

    state = hass.states.get("update.home_assistant_core_update")
    expect(state.attributes.get("in_progress")).to_be(False)

    with patch(
        "homeassistant.components.hassio.update.update_core",
        side_effect=HomeAssistantError,
    ):
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                "update",
                "install",
                {"entity_id": "update.home_assistant_core_update", "backup": True},
                blocking=True,
            )

    state = hass.states.get("update.home_assistant_core_update")
    expect(state.attributes.get("in_progress")).to_be(False)


@test
async def update_addon_sets_progress_immediately(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    _supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test addon update sets in_progress immediately when install starts."""
    await _setup_hassio(hass)

    state = hass.states.get("update.test_update")
    expect(state.attributes.get("in_progress")).to_be(False)

    async def check_progress(
        hass: HomeAssistant,
        addon: str,
        backup: bool,
        addon_name: str | None,
        installed_version: str | None,
    ) -> None:
        assert (
            hass.states.get("update.test_update").attributes.get("in_progress") is True
        )

    with patch(
        "homeassistant.components.hassio.update.update_addon",
        side_effect=check_progress,
    ) as mock_update:
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.test_update", "backup": True},
            blocking=True,
        )

    mock_update.assert_called_once()


@test
async def update_addon_resets_progress_on_error(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
    _supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test addon update resets in_progress and update_percentage on failure."""
    await _setup_hassio(hass)

    state = hass.states.get("update.test_update")
    expect(state.attributes.get("in_progress")).to_be(False)
    expect(state.attributes.get("update_percentage")).to_be(None)

    ws = await hass_supervisor_ws_client()
    job_uuid = uuid4().hex

    async def fake_update_addon_error(
        _hass: HomeAssistant,
        _addon: str,
        _backup: bool,
        _addon_name: str | None,
        _installed_version: str | None,
    ) -> None:
        """Report some progress, then fail - as a mid-pull network error would."""
        await ws.send_json(
            {
                "id": 1,
                "type": "supervisor/event",
                "data": {
                    "event": "job",
                    "data": {
                        "uuid": job_uuid,
                        "created": "2025-09-29T00:00:00.000000+00:00",
                        "name": "addon_manager_update",
                        "reference": "test",
                        "progress": 42,
                        "done": False,
                        "stage": None,
                        "extra": {"total": 1234567890},
                        "errors": [],
                    },
                },
            }
        )
        msg = await ws.receive_json()
        assert msg["success"]
        await hass.async_block_till_done()
        raise HomeAssistantError

    with patch(
        "homeassistant.components.hassio.update.update_addon",
        side_effect=fake_update_addon_error,
    ):
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                "update",
                "install",
                {"entity_id": "update.test_update", "backup": True},
                blocking=True,
            )

    state = hass.states.get("update.test_update")
    expect(state.attributes.get("in_progress")).to_be(False)
    expect(state.attributes.get("update_percentage")).to_be(None)


def _bump_addon_to(
    addons_list: AsyncMock,
    addon_installed: AsyncMock,
    version: str,
    version_latest: str,
) -> None:
    """Rewrite the addon fixtures to report a post-update version."""
    current = addons_list.return_value
    addons_list.return_value = [
        replace(
            current[0],
            version=version,
            version_latest=version_latest,
            update_available=version != version_latest,
        ),
        *current[1:],
    ]

    def _updated_info(slug: str):
        addon = Mock(
            spec=InstalledAddonComplete,
            to_dict=addon_installed.return_value.to_dict,
            **addon_installed.return_value.to_dict(),
        )
        addon.name = "test"
        addon.slug = "test"
        addon.version = version
        addon.version_latest = version_latest
        addon.update_available = version != version_latest
        addon.state = AddonState.STARTED
        addon.url = "https://github.com/home-assistant/addons/test"
        addon.auto_update = True
        return addon

    addon_installed.side_effect = _updated_info


@test
async def update_addon_stays_in_progress_until_refresh(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
    update_addon: AsyncMock = Depends(update_addon),
    addon_installed: AsyncMock = Depends(addon_installed),
    addons_list: AsyncMock = Depends(addons_list),
) -> None:
    """Test addon update entity stays in progress until coordinator refresh."""
    await _setup_hassio(hass)

    entity_id = "update.test_update"
    expect(hass.states.get(entity_id).state).to_equal("on")

    ws = await hass_supervisor_ws_client()
    job_uuid = uuid4().hex
    in_progress_after_done: list[bool | None] = []

    async def fake_update_addon(slug: str, _options: StoreAddonUpdate) -> None:
        """Mimic Supervisor: fire done=True on WS, then return HTTP response."""
        await ws.send_json(
            {
                "id": 1,
                "type": "supervisor/event",
                "data": {
                    "event": "job",
                    "data": {
                        "uuid": job_uuid,
                        "created": "2025-09-29T00:00:00.000000+00:00",
                        "name": "addon_manager_update",
                        "reference": "test",
                        "progress": 100,
                        "done": True,
                        "stage": None,
                        "extra": {"total": 1234567890},
                        "errors": [],
                    },
                },
            }
        )
        msg = await ws.receive_json()
        assert msg["success"]
        await hass.async_block_till_done()
        in_progress_after_done.append(
            hass.states.get(entity_id).attributes.get("in_progress")
        )
        _bump_addon_to(addons_list, addon_installed, "2.0.1", "2.0.1")

    update_addon.side_effect = fake_update_addon

    await hass.services.async_call(
        "update", "install", {"entity_id": entity_id}, blocking=True
    )

    expect(in_progress_after_done).to_equal([True])

    state = hass.states.get(entity_id)
    expect(state.attributes.get("in_progress")).to_be(False)
    expect(state.state).to_equal("off")


@test
async def update_addon_completes_on_any_version_change(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    update_addon: AsyncMock = Depends(update_addon),
    addon_installed: AsyncMock = Depends(addon_installed),
    addons_list: AsyncMock = Depends(addons_list),
) -> None:
    """Test completion when installed version changes from the pre-install one."""
    await _setup_hassio(hass)

    entity_id = "update.test_update"

    async def fake_update_addon(slug: str, _options: StoreAddonUpdate) -> None:
        _bump_addon_to(addons_list, addon_installed, "2.0.1", "2.0.2")

    update_addon.side_effect = fake_update_addon

    await hass.services.async_call(
        "update", "install", {"entity_id": entity_id}, blocking=True
    )

    state = hass.states.get(entity_id)
    expect(state.attributes.get("in_progress")).to_be(False)
    expect(state.state).to_equal("on")


@test
async def update_supervisor(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test updating supervisor update entity."""
    await _setup_hassio(hass)

    supervisor_client.supervisor.update.return_value = None
    await hass.services.async_call(
        "update",
        "install",
        {"entity_id": "update.home_assistant_supervisor_update"},
        blocking=True,
    )
    supervisor_client.supervisor.update.assert_called_once()


@test
async def update_supervisor_progress(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
    supervisor_info: AsyncMock = Depends(supervisor_info),
) -> None:
    """Test progress reporting for a Supervisor update."""
    await _setup_hassio(hass)

    client = await hass_supervisor_ws_client()
    message_id = 0
    job_uuid = uuid4().hex
    entity_id = "update.home_assistant_supervisor_update"

    def make_job_message(progress: float, done: bool | None) -> dict[str, Any]:
        nonlocal message_id
        message_id += 1
        return {
            "id": message_id,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "uuid": job_uuid,
                    "created": "2025-09-29T00:00:00.000000+00:00",
                    "name": "supervisor_update",
                    "reference": None,
                    "progress": progress,
                    "done": done,
                    "stage": None,
                    "extra": {"total": 1234567890} if progress > 0 else None,
                    "errors": [],
                },
            },
        }

    await client.send_json(make_job_message(progress=0, done=None))
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()
    expect(hass.states.get(entity_id).attributes.get("in_progress")).to_be(False)
    expect(hass.states.get(entity_id).attributes.get("update_percentage")).to_be(None)

    await client.send_json(make_job_message(progress=5, done=False))
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()
    expect(hass.states.get(entity_id).attributes.get("in_progress")).to_be(True)
    expect(hass.states.get(entity_id).attributes.get("update_percentage")).to_equal(5)

    await client.send_json(make_job_message(progress=50, done=False))
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()
    expect(hass.states.get(entity_id).attributes.get("update_percentage")).to_equal(50)

    await client.send_json(make_job_message(progress=100, done=True))
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()
    expect(hass.states.get(entity_id).attributes.get("in_progress")).to_be(True)
    expect(hass.states.get(entity_id).attributes.get("update_percentage")).to_be(None)

    supervisor_info.return_value = replace(
        supervisor_info.return_value,
        version="1.0.1dev222",
        update_available=False,
    )
    await client.send_json(
        {
            "id": message_id + 1,
            "type": "supervisor/event",
            "data": {
                "event": "supervisor_update",
                "update_key": "supervisor",
                "data": {"startup": "complete"},
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()

    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=REQUEST_REFRESH_DELAY + 1)
    )
    await hass.async_block_till_done()

    expect(hass.states.get(entity_id).attributes.get("in_progress")).to_be(False)


@test
async def update_supervisor_stays_in_progress_until_restart(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    supervisor_info: AsyncMock = Depends(supervisor_info),
) -> None:
    """Test in_progress stays True after install returns, until Supervisor restart."""
    await _setup_hassio(hass)

    entity_id = "update.home_assistant_supervisor_update"
    expect(hass.states.get(entity_id).attributes.get("in_progress")).to_be(False)

    supervisor_client.supervisor.update.return_value = None
    await hass.services.async_call(
        "update", "install", {"entity_id": entity_id}, blocking=True
    )

    expect(hass.states.get(entity_id).attributes.get("in_progress")).to_be(True)

    supervisor_info.return_value = replace(
        supervisor_info.return_value,
        version="1.0.1dev222",
        update_available=False,
    )

    client = await hass_supervisor_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "supervisor_update",
                "update_key": "supervisor",
                "data": {"startup": "complete"},
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()

    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=REQUEST_REFRESH_DELAY + 1)
    )
    await hass.async_block_till_done()

    expect(hass.states.get(entity_id).attributes.get("in_progress")).to_be(False)


@test
async def update_supervisor_completes_on_any_version_change(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    supervisor_info: AsyncMock = Depends(supervisor_info),
) -> None:
    """Test completion is detected when installed version changes from the pre-install one."""
    await _setup_hassio(hass)

    entity_id = "update.home_assistant_supervisor_update"

    supervisor_client.supervisor.update.return_value = None
    await hass.services.async_call(
        "update", "install", {"entity_id": entity_id}, blocking=True
    )
    expect(hass.states.get(entity_id).attributes.get("in_progress")).to_be(True)

    supervisor_info.return_value = replace(
        supervisor_info.return_value,
        version="1.0.1dev222",
        version_latest="1.0.2dev223",
        update_available=True,
    )

    client = await hass_supervisor_ws_client()
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "supervisor_update",
                "update_key": "supervisor",
                "data": {"startup": "complete"},
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()

    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=REQUEST_REFRESH_DELAY + 1)
    )
    await hass.async_block_till_done()

    expect(hass.states.get(entity_id).attributes.get("in_progress")).to_be(False)


@test
async def update_addon_with_error(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test updating addon update entity with error."""
    await _setup_hassio(hass)

    update_addon.side_effect = SupervisorError
    async with expect_raises_async(HomeAssistantError, match=r"^Error updating test:"):
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.test_update"},
            blocking=True,
        )


@test.cases(
    test.case(
        "create_backup",
        create_backup_error=BackupManagerError,
        delete_filtered_backups_error=None,
        message=r"^Error creating backup: ",
    ),
    test.case(
        "delete_backup",
        create_backup_error=None,
        delete_filtered_backups_error=BackupManagerError,
        message=r"^Error deleting old backups: ",
    ),
)
async def update_addon_with_backup_and_error(
    create_backup_error: type[Exception] | None,
    delete_filtered_backups_error: type[Exception] | None,
    message: str,
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test updating addon update entity with error."""
    await _setup_hassio(hass)
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
        async with expect_raises_async(HomeAssistantError, match=message):
            await hass.services.async_call(
                "update",
                "install",
                {"entity_id": "update.test_update", "backup": True},
                blocking=True,
            )


@test
async def update_os_with_error(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test updating OS update entity with error."""
    await _setup_hassio(hass)

    supervisor_client.os.update.side_effect = SupervisorError
    async with expect_raises_async(
        HomeAssistantError, match=r"^Error updating Home Assistant Operating System:"
    ):
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.home_assistant_operating_system_update"},
            blocking=True,
        )


@test
async def update_os_with_backup_and_error(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test updating OS update entity with error."""
    await _setup_hassio(hass)
    await setup_backup_integration(hass)

    supervisor_client.os.update.return_value = None
    supervisor_client.mounts.info.return_value.default_backup_mount = None
    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
        side_effect=BackupManagerError,
    ):
        async with expect_raises_async(
            HomeAssistantError, match=r"^Error creating backup:"
        ):
            await hass.services.async_call(
                "update",
                "install",
                {
                    "entity_id": "update.home_assistant_operating_system_update",
                    "backup": True,
                },
                blocking=True,
            )


@test
async def update_supervisor_with_error(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test updating supervisor update entity with error."""
    await _setup_hassio(hass)

    supervisor_client.supervisor.update.side_effect = SupervisorError
    async with expect_raises_async(
        HomeAssistantError, match=r"^Error updating Home Assistant Supervisor:"
    ):
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.home_assistant_supervisor_update"},
            blocking=True,
        )


@test
async def update_core_with_error(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test updating core update entity with error."""
    await _setup_hassio(hass)

    supervisor_client.homeassistant.update.side_effect = SupervisorError
    async with expect_raises_async(
        HomeAssistantError, match=r"^Error updating Home Assistant Core:"
    ):
        await hass.services.async_call(
            "update",
            "install",
            {"entity_id": "update.home_assistant_core_update"},
            blocking=True,
        )


@test
async def update_core_with_backup_and_error(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test updating core update entity with error."""
    await _setup_hassio(hass)
    await setup_backup_integration(hass)

    supervisor_client.homeassistant.update.return_value = None
    supervisor_client.mounts.info.return_value.default_backup_mount = None
    with patch(
        "homeassistant.components.backup.manager.BackupManager.async_create_backup",
        side_effect=BackupManagerError,
    ):
        async with expect_raises_async(
            HomeAssistantError, match=r"^Error creating backup:"
        ):
            await hass.services.async_call(
                "update",
                "install",
                {"entity_id": "update.home_assistant_core_update", "backup": True},
                blocking=True,
            )


@test
async def release_notes_between_versions(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    addon_changelog: AsyncMock = Depends(addon_changelog),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test release notes between versions."""
    addon_changelog.return_value = "# 2.0.1\nNew updates\n# 2.0.0\nOld updates"

    await _setup_hassio(hass)

    client = await hass_ws_client(hass)
    await hass.async_block_till_done()

    await client.send_json(
        {
            "id": 1,
            "type": "update/release_notes",
            "entity_id": "update.test_update",
        }
    )
    result = await client.receive_json()
    expect("Old updates" not in result["result"]).to_be_truthy()
    expect("New updates" in result["result"]).to_be_truthy()


@test
async def release_notes_full(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    addon_changelog: AsyncMock = Depends(addon_changelog),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test release notes no match."""
    full_changelog = "# 2.0.0\nNew updates\n# 2.0.0\nOld updates"
    addon_changelog.return_value = full_changelog

    await _setup_hassio(hass)

    client = await hass_ws_client(hass)
    await hass.async_block_till_done()

    await client.send_json(
        {
            "id": 1,
            "type": "update/release_notes",
            "entity_id": "update.test_update",
        }
    )
    result = await client.receive_json()
    expect("Old updates" in result["result"]).to_be_truthy()
    expect("New updates" in result["result"]).to_be_truthy()

    await client.send_json(
        {
            "id": 2,
            "type": "update/release_notes",
            "entity_id": "update.test2_update",
        }
    )
    result = await client.receive_json()
    expect(result["result"]).to_equal(full_changelog)


@test
async def not_release_notes(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    addon_changelog: AsyncMock = Depends(addon_changelog),
    hass_ws_client=Depends(hass_ws_client_fx),
) -> None:
    """Test handling where there are no release notes."""
    addon_changelog.side_effect = SupervisorNotFoundError()

    await _setup_hassio(hass)

    client = await hass_ws_client(hass)
    await hass.async_block_till_done()

    await client.send_json(
        {
            "id": 1,
            "type": "update/release_notes",
            "entity_id": "update.test_update",
        }
    )
    result = await client.receive_json()
    expect(result["result"]).to_be(None)


@test
async def no_os_entity(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_root_info: AsyncMock = Depends(supervisor_root_info),
) -> None:
    """Test handling where there is no os entity."""
    supervisor_root_info.return_value = replace(
        supervisor_root_info.return_value, hassos=None
    )
    result = await async_setup_component(
        hass,
        "hassio",
        {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
    )
    expect(result).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get("update.home_assistant_operating_system_update")).to_be(None)


@test
async def setting_up_core_update_when_addon_fails(
    _env: None = Depends(fixture_supervisor_environ),
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    addon_installed: AsyncMock = Depends(addon_installed),
    addon_stats: AsyncMock = Depends(addon_stats),
    addon_changelog: AsyncMock = Depends(addon_changelog),
) -> None:
    """Test setting up core update when single addon fails."""
    addon_installed.side_effect = SupervisorBadRequestError("Addon Test does not exist")
    addon_stats.side_effect = SupervisorBadRequestError("add-on is not running")
    addon_changelog.side_effect = SupervisorBadRequestError("add-on is not running")
    result = await async_setup_component(
        hass,
        "hassio",
        {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
    )
    await hass.async_block_till_done()
    expect(result).to_be_truthy()

    async_fire_time_changed(
        hass, dt_util.now() + timedelta(seconds=REQUEST_REFRESH_DELAY)
    )
    await hass.async_block_till_done()

    state = hass.states.get("update.home_assistant_core_update")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("on")
