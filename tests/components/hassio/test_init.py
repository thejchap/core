"""The tests for the hassio component."""

from dataclasses import replace
from datetime import timedelta
import os
from pathlib import PurePath
from typing import Any
from unittest.mock import ANY, AsyncMock, Mock, call, patch
from uuid import uuid4

from aiohasupervisor import SupervisorError
from aiohasupervisor.models import (
    AddonsStats,
    AddonStage,
    AddonState,
    CIFSMountResponse,
    FullBackupOptions,
    HomeAssistantOptions,
    InstalledAddon,
    InstalledAddonComplete,
    MountsInfo,
    MountState,
    MountType,
    MountUsage,
    NewBackup,
    PartialBackupOptions,
    PartialRestoreOptions,
    SupervisorOptions,
)
from voluptuous import Invalid

from homeassistant.auth.const import GROUP_ID_ADMIN
from homeassistant.components import frontend, hassio
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.hassio import (
    ADDONS_COORDINATOR,
    DOMAIN,
    get_addons_info,
    get_addons_list,
    get_addons_stats,
    get_core_info,
    get_core_stats,
    get_host_info,
    get_info,
    get_network_info,
    get_os_info,
    get_store,
    get_supervisor_info,
    get_supervisor_stats,
    hostname_from_addon_slug,
)
from homeassistant.components.hassio.config import STORAGE_KEY
from homeassistant.components.hassio.const import (
    HASSIO_MAIN_UPDATE_INTERVAL,
    REQUEST_REFRESH_DELAY,
)
from homeassistant.components.homeassistant import (
    DOMAIN as HOMEASSISTANT_DOMAIN,
    SERVICE_UPDATE_ENTITY,
)
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr, issue_registry as ir
from homeassistant.helpers.hassio import is_hassio
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import load_yaml_dict

from tryke import Depends, expect, fixture, test

from ._fixtures import (
    addon_changelog,
    addon_info,
    addon_installed,
    addon_stats,
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
    supervisor_is_connected,
    supervisor_root_info,
    supervisor_stats,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    caplog as caplog_fx,
    device_registry as device_registry_fx,
    freezer as freezer_fx,
    hass as hass_fixture,
    hass_storage as hass_storage_fx,
    issue_registry as issue_registry_fx,
    mock_network,
)
from tests.hass_tryke_helpers import (
    entity_registry_enabled_by_default as entity_registry_enabled_by_default_fx,
    expect_raises_async,
)

MOCK_ENVIRON = {"SUPERVISOR": "127.0.0.1", "SUPERVISOR_TOKEN": "abcdefgh"}


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_all(
    store_info: AsyncMock = Depends(store_info),
    addon_info: AsyncMock = Depends(addon_info),
    addon_stats: AsyncMock = Depends(addon_stats),
    addon_changelog: AsyncMock = Depends(addon_changelog),
    resolution_info: AsyncMock = Depends(resolution_info),
    jobs_info: AsyncMock = Depends(jobs_info),
    host_info: AsyncMock = Depends(host_info),
    supervisor_root_info: AsyncMock = Depends(supervisor_root_info),
    homeassistant_info: AsyncMock = Depends(homeassistant_info),
    supervisor_info: AsyncMock = Depends(supervisor_info),
    addons_list: AsyncMock = Depends(addons_list),
    network_info: AsyncMock = Depends(network_info),
    os_info: AsyncMock = Depends(os_info),
    homeassistant_stats: AsyncMock = Depends(homeassistant_stats),
    supervisor_stats: AsyncMock = Depends(supervisor_stats),
    addon_installed: AsyncMock = Depends(addon_installed),
    ingress_panels: AsyncMock = Depends(ingress_panels),
) -> None:
    """Mock all setup requests."""
    addons_list.return_value[0] = replace(
        addons_list.return_value[0],
        version="1.0.0",
        version_latest="1.0.0",
        update_available=False,
        state=AddonState.STOPPED,
    )
    addons_list.return_value[1] = replace(
        addons_list.return_value[1],
        version="1.0.0",
        version_latest="1.0.0",
    )
    addon_installed.return_value.state = AddonState.STOPPED

    async def mock_addon_stats(addon: str) -> AddonsStats:
        """Mock addon stats for test and test2."""
        if addon in {"test2", "test3"}:
            return AddonsStats(
                cpu_percent=0.8,
                memory_usage=51941376,
                memory_limit=3977146368,
                memory_percent=1.31,
                network_rx=31338284,
                network_tx=15692900,
                blk_read=740077568,
                blk_write=6004736,
            )
        return AddonsStats(
            cpu_percent=0.99,
            memory_usage=182611968,
            memory_limit=3977146368,
            memory_percent=4.59,
            network_rx=362570232,
            network_tx=82374138,
            blk_read=46010945536,
            blk_write=15051526144,
        )

    addon_stats.side_effect = mock_addon_stats

    def mock_addon_info_fn(slug: str):
        addon = Mock(
            spec=InstalledAddonComplete,
            to_dict=addon_installed.return_value.to_dict,
            **addon_installed.return_value.to_dict(),
        )
        if slug == "test":
            addon.name = "test"
            addon.slug = "test"
            addon.url = "https://github.com/home-assistant/addons/test"
            addon.auto_update = True
        else:
            addon.name = "test2"
            addon.slug = "test2"
            addon.url = "https://github.com"
            addon.auto_update = False

        return addon

    addon_info.side_effect = mock_addon_info_fn


@test
async def setup_api_ping(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test setup with API ping."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(hass, "hassio", {})
        await hass.async_block_till_done()

    expect(result).to_be_truthy()
    expect(len(supervisor_client.mock_calls)).to_equal(25)
    expect(get_core_info(hass)["version_latest"]).to_equal("1.0.0")
    expect(is_hassio(hass)).to_be_truthy()


@test
async def setup_app_panel(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test app panel is registered."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(hass, "hassio", {})
        await hass.async_block_till_done()
        expect(result).to_be_truthy()

    panels = hass.data[frontend.DATA_PANELS]

    expect(panels.get("app").to_response()).to_equal(
        {
            "component_name": "app",
            "icon": None,
            "title": None,
            "default_visible": True,
            "config": None,
            "url_path": "app",
            "require_admin": False,
            "show_in_sidebar": True,
            "config_panel_domain": None,
        }
    )


@test
async def setup_api_push_api_data(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test setup with API push."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass, "hassio", {"http": {"server_port": 9999}, "hassio": {}}
        )
        await hass.async_block_till_done()

    expect(result).to_be_truthy()
    expect(len(supervisor_client.mock_calls)).to_equal(25)
    supervisor_client.homeassistant.set_options.assert_called_once_with(
        HomeAssistantOptions(ssl=False, port=9999, refresh_token=ANY)
    )


@test
async def setup_api_push_api_data_error(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    caplog=Depends(caplog_fx),
) -> None:
    """Test setup with error while pushing core config data to API."""
    supervisor_client.homeassistant.set_options.side_effect = SupervisorError("boom")
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(hass, "hassio", {"http": {}, "hassio": {}})
        await hass.async_block_till_done()

    expect(result).to_be_truthy()
    expect(len(supervisor_client.mock_calls)).to_equal(25)
    expect("Failed to update Home Assistant options in Supervisor: boom" in caplog.text).to_be_truthy()


@test
async def setup_api_push_api_data_server_host(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test setup with API push with active server host."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        await hass.async_block_till_done()

    expect(result).to_be_truthy()
    expect(len(supervisor_client.mock_calls)).to_equal(25)
    supervisor_client.homeassistant.set_options.assert_called_once_with(
        HomeAssistantOptions(ssl=False, port=9999, refresh_token=ANY, watchdog=False)
    )


@test
async def setup_api_push_api_data_default(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test setup with API push default data."""
    with (
        patch.dict(os.environ, MOCK_ENVIRON),
        patch("homeassistant.components.hassio.config.STORE_DELAY_SAVE", 0),
    ):
        result = await async_setup_component(hass, "hassio", {"http": {}, "hassio": {}})
        await hass.async_block_till_done()

    expect(result).to_be_truthy()
    expect(len(supervisor_client.mock_calls)).to_equal(25)
    supervisor_client.homeassistant.set_options.assert_called_once_with(
        HomeAssistantOptions(ssl=False, port=8123, refresh_token=ANY)
    )
    refresh_token = (
        supervisor_client.homeassistant.set_options.mock_calls[0].args[0].refresh_token
    )
    hassio_user = await hass.auth.async_get_user(
        hass_storage[STORAGE_KEY]["data"]["hassio_user"]
    )
    expect(hassio_user is not None).to_be_truthy()
    expect(hassio_user.system_generated).to_be_truthy()
    expect(len(hassio_user.groups)).to_equal(1)
    expect(hassio_user.groups[0].id).to_equal(GROUP_ID_ADMIN)
    expect(hassio_user.name).to_equal("Supervisor")
    found = False
    for token in hassio_user.refresh_tokens.values():
        if token.token == refresh_token:
            found = True
            break
    expect(found).to_be_truthy()


@test
async def setup_adds_admin_group_to_user(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test setup with API push default data."""
    user = await hass.auth.async_create_system_user("Hass.io")
    expect(user.is_admin).to_be_falsy()
    await hass.auth.async_create_refresh_token(user)

    hass_storage[STORAGE_KEY] = {
        "data": {"hassio_user": user.id},
        "key": STORAGE_KEY,
        "version": 1,
    }

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(hass, "hassio", {"http": {}, "hassio": {}})
        expect(result).to_be_truthy()

    expect(user.is_admin).to_be_truthy()


@test
async def setup_migrate_user_name(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test setup with migrating the user name."""
    user = await hass.auth.async_create_system_user("Hass.io")
    await hass.auth.async_create_refresh_token(user)

    hass_storage[STORAGE_KEY] = {
        "data": {"hassio_user": user.id},
        "key": STORAGE_KEY,
        "version": 1,
    }

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(hass, "hassio", {"http": {}, "hassio": {}})
        expect(result).to_be_truthy()

    expect(user.name).to_equal("Supervisor")


@test
async def setup_api_existing_hassio_user(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test setup with API push default data."""
    user = await hass.auth.async_create_system_user("Hass.io test")
    token = await hass.auth.async_create_refresh_token(user)
    hass_storage[STORAGE_KEY] = {"version": 1, "data": {"hassio_user": user.id}}
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(hass, "hassio", {"http": {}, "hassio": {}})
        await hass.async_block_till_done()

    expect(result).to_be_truthy()
    expect(len(supervisor_client.mock_calls)).to_equal(25)
    supervisor_client.homeassistant.set_options.assert_called_once_with(
        HomeAssistantOptions(ssl=False, port=8123, refresh_token=token.token)
    )


@test
async def setup_core_push_config(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test setup with API push default data."""
    hass.config.time_zone = "testzone"

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(hass, "hassio", {"hassio": {}})
        await hass.async_block_till_done()

    expect(result).to_be_truthy()
    expect(len(supervisor_client.mock_calls)).to_equal(25)
    supervisor_client.supervisor.set_options.assert_called_once_with(
        SupervisorOptions(timezone="testzone")
    )

    with patch("homeassistant.util.dt.set_default_time_zone"):
        await hass.config.async_update(time_zone="America/New_York", country="US")
    await hass.async_block_till_done()
    supervisor_client.supervisor.set_options.assert_called_with(
        SupervisorOptions(timezone="America/New_York", country="US")
    )


@test
async def setup_core_push_config_error(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    caplog=Depends(caplog_fx),
) -> None:
    """Test setup with error while pushing supervisor config data to API."""
    hass.config.time_zone = "testzone"
    supervisor_client.supervisor.set_options.side_effect = SupervisorError("boom")

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(hass, "hassio", {"hassio": {}})
        await hass.async_block_till_done()

    expect(result).to_be_truthy()
    expect(len(supervisor_client.mock_calls)).to_equal(25)
    expect("Failed to update Supervisor options: boom" in caplog.text).to_be_truthy()


@test
async def setup_hassio_no_additional_data(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test setup with API push default data."""
    with (
        patch.dict(os.environ, MOCK_ENVIRON),
        patch.dict(os.environ, {"SUPERVISOR_TOKEN": "123456"}),
    ):
        result = await async_setup_component(hass, "hassio", {"hassio": {}})
        await hass.async_block_till_done()

    expect(result).to_be_truthy()
    expect(len(supervisor_client.mock_calls)).to_equal(25)


@test
async def fail_setup_without_environ_var(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Fail setup if no environ variable set."""
    with patch.dict(os.environ, {}, clear=True):
        result = await async_setup_component(hass, "hassio", {})
        expect(result).to_be_falsy()


@test
async def warn_when_cannot_connect(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog=Depends(caplog_fx),
    supervisor_is_connected: AsyncMock = Depends(supervisor_is_connected),
) -> None:
    """Fail warn when we cannot connect."""
    supervisor_is_connected.side_effect = SupervisorError
    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(hass, "hassio", {})
        expect(result).to_be_truthy()

    expect(is_hassio(hass)).to_be_truthy()
    expect("Not connected with the supervisor / system too busy!" in caplog.text).to_be_truthy()


@test
async def service_register(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check if service will be setup."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()
    # New app services
    expect(hass.services.has_service("hassio", "app_start")).to_be_truthy()
    expect(hass.services.has_service("hassio", "app_stop")).to_be_truthy()
    expect(hass.services.has_service("hassio", "app_restart")).to_be_truthy()
    expect(hass.services.has_service("hassio", "app_stdin")).to_be_truthy()
    # Legacy addon services (deprecated)
    expect(hass.services.has_service("hassio", "addon_start")).to_be_truthy()
    expect(hass.services.has_service("hassio", "addon_stop")).to_be_truthy()
    expect(hass.services.has_service("hassio", "addon_restart")).to_be_truthy()
    expect(hass.services.has_service("hassio", "addon_stdin")).to_be_truthy()
    # Other services
    expect(hass.services.has_service("hassio", "host_shutdown")).to_be_truthy()
    expect(hass.services.has_service("hassio", "host_reboot")).to_be_truthy()
    expect(hass.services.has_service("hassio", "backup_full")).to_be_truthy()
    expect(hass.services.has_service("hassio", "backup_partial")).to_be_truthy()
    expect(hass.services.has_service("hassio", "restore_full")).to_be_truthy()
    expect(hass.services.has_service("hassio", "restore_partial")).to_be_truthy()
    expect(hass.services.has_service("hassio", "mount_reload")).to_be_truthy()


@test.cases(
    test.case("app", app_or_addon="app"),
    test.case("addon", app_or_addon="addon"),
)
async def service_calls(
    app_or_addon: str,
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    supervisor_is_connected: AsyncMock = Depends(supervisor_is_connected),
    freezer=Depends(freezer_fx),
) -> None:
    """Call service and check the API calls behind that."""
    freezer.move_to("2021-11-13 11:48:00")
    supervisor_is_connected.side_effect = SupervisorError
    with patch.dict(os.environ, MOCK_ENVIRON):
        expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()
        await hass.async_block_till_done()

    supervisor_client.reset_mock()

    await hass.services.async_call(
        "hassio", f"{app_or_addon}_start", {app_or_addon: "test"}
    )
    await hass.services.async_call(
        "hassio", f"{app_or_addon}_stop", {app_or_addon: "test"}
    )
    await hass.services.async_call(
        "hassio", f"{app_or_addon}_restart", {app_or_addon: "test"}
    )
    await hass.services.async_call(
        "hassio", f"{app_or_addon}_stdin", {app_or_addon: "test", "input": "test"}
    )
    await hass.services.async_call(
        "hassio",
        f"{app_or_addon}_stdin",
        {app_or_addon: "test", "input": {"hello": "world"}},
    )
    await hass.async_block_till_done()

    supervisor_client.addons.start_addon.assert_called_once_with("test")
    supervisor_client.addons.stop_addon.assert_called_once_with("test")
    supervisor_client.addons.restart_addon.assert_called_once_with("test")
    expect(
        call("test", b'"test"') in supervisor_client.addons.write_addon_stdin.mock_calls
    ).to_be_truthy()
    expect(
        call("test", b'{"hello": "world"}')
        in supervisor_client.addons.write_addon_stdin.mock_calls
    ).to_be_truthy()

    await hass.services.async_call("hassio", "host_shutdown", {})
    await hass.services.async_call("hassio", "host_reboot", {})
    await hass.async_block_till_done()

    supervisor_client.host.shutdown.assert_called_once_with()
    supervisor_client.host.reboot.assert_called_once_with()

    supervisor_client.backups.full_backup.return_value = NewBackup(
        job_id=uuid4(), slug="full"
    )
    supervisor_client.backups.partial_backup.return_value = NewBackup(
        job_id=uuid4(), slug="partial"
    )

    full_backup = await hass.services.async_call(
        "hassio", "backup_full", {}, blocking=True, return_response=True
    )
    supervisor_client.backups.full_backup.assert_called_once_with(
        FullBackupOptions(name="2021-11-13 03:48:00")
    )
    expect(full_backup).to_equal({"backup": "full"})

    partial_backup = await hass.services.async_call(
        "hassio",
        "backup_partial",
        {
            "homeassistant": True,
            f"{app_or_addon}s": ["test"],
            "folders": ["ssl"],
            "password": "123456",
        },
        blocking=True,
        return_response=True,
    )
    supervisor_client.backups.partial_backup.assert_called_once_with(
        PartialBackupOptions(
            name="2021-11-13 03:48:00",
            homeassistant=True,
            addons={"test"},
            folders={"ssl"},
            password="123456",
        )
    )
    expect(partial_backup).to_equal({"backup": "partial"})

    await hass.services.async_call("hassio", "restore_full", {"slug": "test"})
    await hass.services.async_call(
        "hassio",
        "restore_partial",
        {
            "slug": "test",
            "homeassistant": False,
            f"{app_or_addon}s": ["test"],
            "folders": ["ssl"],
            "password": "123456",
        },
    )
    await hass.async_block_till_done()

    supervisor_client.backups.full_restore.assert_called_once_with("test", None)
    supervisor_client.backups.partial_restore.assert_called_once_with(
        "test",
        PartialRestoreOptions(
            homeassistant=False, addons={"test"}, folders={"ssl"}, password="123456"
        ),
    )

    await hass.services.async_call(
        "hassio",
        "backup_full",
        {
            "name": "backup_name",
            "location": "backup_share",
            "homeassistant_exclude_database": True,
        },
    )
    await hass.async_block_till_done()
    supervisor_client.backups.full_backup.assert_called_with(
        FullBackupOptions(
            name="backup_name",
            location="backup_share",
            homeassistant_exclude_database=True,
        )
    )

    await hass.services.async_call(
        "hassio",
        "backup_full",
        {
            "location": "/backup",
        },
    )
    await hass.async_block_till_done()
    supervisor_client.backups.full_backup.assert_called_with(
        FullBackupOptions(name="2021-11-13 03:48:00", location=None)
    )

    # check backup with different timezone
    await hass.config.async_update(time_zone="Europe/London")
    await hass.async_block_till_done()

    await hass.services.async_call(
        "hassio",
        "backup_full",
        {
            "location": "/backup",
        },
    )
    await hass.async_block_till_done()
    supervisor_client.backups.full_backup.assert_called_with(
        FullBackupOptions(name="2021-11-13 11:48:00", location=None)
    )


@test.cases(
    test.case("app", app_or_addon="app"),
    test.case("addon", app_or_addon="addon"),
)
async def invalid_service_calls(
    app_or_addon: str,
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_is_connected: AsyncMock = Depends(supervisor_is_connected),
) -> None:
    """Call service with invalid input and check that it raises."""
    supervisor_is_connected.side_effect = SupervisorError
    with patch.dict(os.environ, MOCK_ENVIRON):
        expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()
        await hass.async_block_till_done()

    async with expect_raises_async(Invalid):
        await hass.services.async_call(
            "hassio", f"{app_or_addon}_start", {app_or_addon: "does_not_exist"}
        )
    async with expect_raises_async(Invalid):
        await hass.services.async_call(
            "hassio",
            f"{app_or_addon}_stdin",
            {app_or_addon: "does_not_exist", "input": "test"},
        )


@test.cases(
    test.case(
        "backup_partial",
        service="backup_partial",
        service_data={"apps": ["test"], "addons": ["test"]},
    ),
    test.case(
        "restore_partial",
        service="restore_partial",
        service_data={"apps": ["test"], "addons": ["test"], "slug": "test"},
    ),
)
async def service_calls_apps_addons_exclusive(
    service: str,
    service_data: dict[str, Any],
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_is_connected: AsyncMock = Depends(supervisor_is_connected),
    _addon_installed: AsyncMock = Depends(addon_installed),
) -> None:
    """Test that apps and addons parameters are mutually exclusive."""
    supervisor_is_connected.side_effect = SupervisorError
    with patch.dict(os.environ, MOCK_ENVIRON):
        expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()
        await hass.async_block_till_done()

    async with expect_raises_async(
        Invalid, match="two or more values in the same group of exclusion"
    ):
        await hass.services.async_call("hassio", service, service_data)


@test.cases(
    test.case("app", app_or_addon="app"),
    test.case("addon", app_or_addon="addon"),
)
async def addon_service_call_with_complex_slug(
    app_or_addon: str,
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_is_connected: AsyncMock = Depends(supervisor_is_connected),
    addons_list: AsyncMock = Depends(addons_list),
) -> None:
    """Addon slugs can have ., - and _, confirm that passes validation."""
    addons_list.return_value = [
        InstalledAddon(
            detached=False,
            advanced=False,
            available=True,
            build=False,
            description="",
            homeassistant=None,
            icon=False,
            logo=False,
            name="test.a_1-2",
            repository="core",
            slug="test.a_1-2",
            stage=AddonStage.STABLE,
            update_available=False,
            url="https://github.com",
            version_latest="1.0.0",
            version="1.0.0",
            state=AddonState.STOPPED,
        )
    ]
    supervisor_is_connected.side_effect = SupervisorError
    with patch.dict(os.environ, MOCK_ENVIRON):
        expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()
        await hass.async_block_till_done()

    await hass.services.async_call(
        "hassio", f"{app_or_addon}_start", {app_or_addon: "test.a_1-2"}
    )


@test
async def service_calls_core(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Call core service and check the API calls behind that."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
        expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

        await hass.services.async_call("homeassistant", "stop")
        await hass.async_block_till_done()

        supervisor_client.homeassistant.stop.assert_called_once_with()

        await hass.services.async_call("homeassistant", "check_config")
        await hass.async_block_till_done()

        with patch(
            "homeassistant.config.async_check_ha_config_file", return_value=None
        ) as mock_check_config:
            await hass.services.async_call("homeassistant", "restart")
            await hass.async_block_till_done()
            expect(mock_check_config.called).to_be_truthy()

    supervisor_client.homeassistant.restart.assert_called_once_with()


@test.cases(
    test.case("apps", app_or_addon="apps"),
    test.case("addons", app_or_addon="addons"),
)
async def invalid_service_calls_app_duplicates(
    app_or_addon: str,
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    _supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test invalid backup/restore service calls due to duplicates in apps list."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    async with expect_raises_async(Invalid, match="contains duplicate items"):
        await hass.services.async_call(
            "hassio", "backup_partial", {app_or_addon: ["test", "test"]}
        )

    async with expect_raises_async(Invalid, match="contains duplicate items"):
        await hass.services.async_call(
            "hassio", "restore_partial", {app_or_addon: ["test", "test"]}
        )


@test
async def invalid_service_calls_folder_duplicates(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    _supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test invalid backup/restore service calls due to duplicates in folder list."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        expect(await async_setup_component(hass, "hassio", {})).to_be_truthy()

    async with expect_raises_async(Invalid, match="contains duplicate items"):
        await hass.services.async_call(
            "hassio", "backup_partial", {"folders": ["ssl", "ssl"]}
        )

    async with expect_raises_async(Invalid, match="contains duplicate items"):
        await hass.services.async_call(
            "hassio", "restore_partial", {"folders": ["ssl", "ssl"]}
        )


@test
async def entry_load_and_unload(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    _addon_installed: AsyncMock = Depends(addon_installed),
) -> None:
    """Test loading and unloading config entry."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    expect(SENSOR_DOMAIN in hass.config.components).to_be_truthy()
    expect(BINARY_SENSOR_DOMAIN in hass.config.components).to_be_truthy()
    expect(ADDONS_COORDINATOR in hass.data).to_be_truthy()

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    expect(ADDONS_COORDINATOR not in hass.data).to_be_truthy()


@test
async def migration_off_hassio(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that when a user moves instance off Hass.io, config entry gets cleaned up."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_falsy()
    await hass.async_block_till_done()
    expect(hass.config_entries.async_entries(DOMAIN)).to_equal([])


@test
async def device_registry_calls(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    addons_list: AsyncMock = Depends(addons_list),
    os_info: AsyncMock = Depends(os_info),
    _addon_installed: AsyncMock = Depends(addon_installed),
    _supervisor_info: AsyncMock = Depends(supervisor_info),
) -> None:
    """Test device registry entries for hassio."""
    addons_list.return_value[0] = replace(
        addons_list.return_value[0],
        version="1.0.0",
        version_latest="1.0.0",
        update_available=False,
    )
    addons_list.return_value[1] = replace(
        addons_list.return_value[1],
        version="1.0.0",
        version_latest="1.0.0",
        state=AddonState.STARTED,
    )
    os_info.return_value = replace(
        os_info.return_value,
        board="odroid-n2",
        boot="A",
        version="5.12",
        version_latest="5.12",
    )

    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done(wait_background_tasks=True)
        expect(len(device_registry.devices)).to_equal(6)

    addons_list.return_value.pop(0)

    async_fire_time_changed(hass, dt_util.now() + timedelta(hours=1))
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(len(device_registry.devices)).to_equal(5)

    async_fire_time_changed(hass, dt_util.now() + timedelta(hours=2))
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(len(device_registry.devices)).to_equal(5)

    addons_list.return_value.append(
        InstalledAddon(
            detached=False,
            advanced=False,
            available=True,
            build=False,
            description="",
            homeassistant=None,
            icon=False,
            logo=False,
            name="test3",
            repository="core",
            slug="test3",
            stage=AddonStage.STABLE,
            update_available=False,
            url="https://github.com",
            version_latest="1.0.0",
            version="1.0.0",
            state=AddonState.STOPPED,
        )
    )

    async_fire_time_changed(hass, dt_util.now() + timedelta(hours=3))
    await hass.async_block_till_done()
    expect(len(device_registry.devices)).to_equal(5)


@test
async def coordinator_updates(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog=Depends(caplog_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    _addon_installed: AsyncMock = Depends(addon_installed),
) -> None:
    """Test coordinator updates."""
    await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

        supervisor_client.reload_updates.assert_not_called()

    async_fire_time_changed(hass, dt_util.now() + timedelta(minutes=20))
    await hass.async_block_till_done(wait_background_tasks=True)

    supervisor_client.reload_updates.assert_not_called()

    await hass.services.async_call(
        HOMEASSISTANT_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {
            "entity_id": [
                "update.home_assistant_core_update",
                "update.home_assistant_supervisor_update",
            ]
        },
        blocking=True,
    )

    supervisor_client.reload_updates.assert_not_called()
    async_fire_time_changed(
        hass, dt_util.now() + timedelta(seconds=REQUEST_REFRESH_DELAY)
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    supervisor_client.reload_updates.assert_called_once()

    supervisor_client.reload_updates.reset_mock()
    supervisor_client.reload_updates.side_effect = SupervisorError("Unknown")
    await hass.services.async_call(
        HOMEASSISTANT_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {
            "entity_id": [
                "update.home_assistant_core_update",
                "update.home_assistant_supervisor_update",
            ]
        },
        blocking=True,
    )
    async_fire_time_changed(
        hass, dt_util.now() + timedelta(seconds=REQUEST_REFRESH_DELAY)
    )
    await hass.async_block_till_done()
    supervisor_client.reload_updates.assert_called_once()
    expect("Error on Supervisor API: Unknown" in caplog.text).to_be_truthy()


@test
async def coordinator_updates_stats_entities_enabled(
    _mock_all: None = Depends(mock_all),
    _enabled: None = Depends(entity_registry_enabled_by_default_fx),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog=Depends(caplog_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    _addon_installed: AsyncMock = Depends(addon_installed),
) -> None:
    """Test coordinator updates with stats entities enabled."""
    await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()
        supervisor_client.reload_updates.assert_not_called()

        async_fire_time_changed(
            hass, dt_util.now() + timedelta(seconds=REQUEST_REFRESH_DELAY)
        )
        await hass.async_block_till_done()

        supervisor_client.reload_updates.assert_not_called()

    async_fire_time_changed(hass, dt_util.now() + timedelta(minutes=20))
    await hass.async_block_till_done()
    supervisor_client.reload_updates.assert_not_called()

    await hass.services.async_call(
        HOMEASSISTANT_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {
            "entity_id": [
                "update.home_assistant_core_update",
                "update.home_assistant_supervisor_update",
            ]
        },
        blocking=True,
    )
    supervisor_client.reload_updates.assert_not_called()

    async_fire_time_changed(
        hass, dt_util.now() + timedelta(seconds=REQUEST_REFRESH_DELAY)
    )
    await hass.async_block_till_done()

    supervisor_client.reload_updates.reset_mock()
    supervisor_client.reload_updates.side_effect = SupervisorError("Unknown")
    await hass.services.async_call(
        HOMEASSISTANT_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {
            "entity_id": [
                "update.home_assistant_core_update",
                "update.home_assistant_supervisor_update",
            ]
        },
        blocking=True,
    )
    async_fire_time_changed(
        hass, dt_util.now() + timedelta(seconds=REQUEST_REFRESH_DELAY)
    )
    await hass.async_block_till_done()
    supervisor_client.reload_updates.assert_called_once()
    expect("Error on Supervisor API: Unknown" in caplog.text).to_be_truthy()


@test.cases(
    test.case("green", board="green", integration="homeassistant_green"),
    test.case("odroid_c2", board="odroid-c2", integration="hardkernel"),
    test.case("odroid_c4", board="odroid-c4", integration="hardkernel"),
    test.case("odroid_n2", board="odroid-n2", integration="hardkernel"),
    test.case("odroid_xu4", board="odroid-xu4", integration="hardkernel"),
    test.case("rpi2", board="rpi2", integration="raspberry_pi"),
    test.case("rpi3", board="rpi3", integration="raspberry_pi"),
    test.case("rpi3_64", board="rpi3-64", integration="raspberry_pi"),
    test.case("rpi4", board="rpi4", integration="raspberry_pi"),
    test.case("rpi4_64", board="rpi4-64", integration="raspberry_pi"),
    test.case("yellow", board="yellow", integration="homeassistant_yellow"),
)
async def setup_hardware_integration(
    board: str,
    integration: str,
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    os_info: AsyncMock = Depends(os_info),
) -> None:
    """Test setup initiates hardware integration."""
    os_info.return_value = replace(os_info.return_value, board=board)

    with (
        patch.dict(os.environ, MOCK_ENVIRON),
        patch(
            f"homeassistant.components.{integration}.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.homeassistant_yellow.config_flow.probe_silabs_firmware_info",
            return_value=None,
        ),
    ):
        result = await async_setup_component(hass, "hassio", {"hassio": {}})
        await hass.async_block_till_done(wait_background_tasks=True)

    expect(result).to_be_truthy()
    expect(len(supervisor_client.mock_calls)).to_equal(25)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
def hostname_from_addon_slug_test() -> None:
    """Test hostname_from_addon_slug."""
    expect(hostname_from_addon_slug("mqtt")).to_equal("mqtt")
    expect(hostname_from_addon_slug("core_silabs_multiprotocol")).to_equal(
        "core-silabs-multiprotocol"
    )


@test.cases(
    test.case("rpi3", board="rpi3", issue_id="deprecated_os_aarch64"),
    test.case("rpi4", board="rpi4", issue_id="deprecated_os_aarch64"),
    test.case("tinker", board="tinker", issue_id="deprecated_os_armv7"),
    test.case("odroid_xu4", board="odroid-xu4", issue_id="deprecated_os_armv7"),
    test.case("rpi2", board="rpi2", issue_id="deprecated_os_armv7"),
)
async def deprecated_installation_issue_os_armv7(
    board: str,
    issue_id: str,
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
    freezer=Depends(freezer_fx),
) -> None:
    """Test deprecated installation issue."""
    with (
        patch.dict(os.environ, MOCK_ENVIRON),
        patch(
            "homeassistant.components.hassio._is_32_bit",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hassio.get_os_info", return_value={"board": board}
        ),
        patch(
            "homeassistant.components.hassio.get_info",
            return_value={"hassos": True, "arch": "armv7"},
        ),
        patch("homeassistant.components.hardware.async_setup", return_value=True),
    ):
        expect(await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})).to_be_truthy()
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()
        freezer.tick(REQUEST_REFRESH_DELAY)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        await hass.services.async_call(
            HOMEASSISTANT_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {
                "entity_id": [
                    "update.home_assistant_core_update",
                    "update.home_assistant_supervisor_update",
                ]
            },
            blocking=True,
        )
        freezer.tick(HASSIO_MAIN_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    expect(len(issue_registry.issues)).to_equal(1)
    issue = issue_registry.async_get_issue("homeassistant", issue_id)
    expect(issue.domain).to_equal("homeassistant")
    expect(issue.severity).to_equal(ir.IssueSeverity.WARNING)
    expect(issue.translation_placeholders).to_equal(
        {"installation_guide": "https://www.home-assistant.io/installation/"}
    )


@test.cases(
    test.case("i386", arch="i386"),
    test.case("armhf", arch="armhf"),
    test.case("armv7", arch="armv7"),
)
async def deprecated_installation_issue_32bit_os(
    arch: str,
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
    freezer=Depends(freezer_fx),
) -> None:
    """Test deprecated architecture issue."""
    with (
        patch.dict(os.environ, MOCK_ENVIRON),
        patch(
            "homeassistant.components.hassio._is_32_bit",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hassio.get_os_info",
            return_value={"board": "rpi3-64"},
        ),
        patch(
            "homeassistant.components.hassio.get_info",
            return_value={"hassos": True, "arch": arch},
        ),
        patch("homeassistant.components.hardware.async_setup", return_value=True),
    ):
        expect(await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})).to_be_truthy()
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()
        freezer.tick(REQUEST_REFRESH_DELAY)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        await hass.services.async_call(
            HOMEASSISTANT_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {
                "entity_id": [
                    "update.home_assistant_core_update",
                    "update.home_assistant_supervisor_update",
                ]
            },
            blocking=True,
        )
        freezer.tick(HASSIO_MAIN_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    expect(len(issue_registry.issues)).to_equal(1)
    issue = issue_registry.async_get_issue("homeassistant", "deprecated_architecture")
    expect(issue.domain).to_equal("homeassistant")
    expect(issue.severity).to_equal(ir.IssueSeverity.WARNING)
    expect(issue.translation_placeholders).to_equal(
        {"installation_type": "OS", "arch": arch}
    )


@test.cases(
    test.case("i386", arch="i386"),
    test.case("armhf", arch="armhf"),
    test.case("armv7", arch="armv7"),
)
async def deprecated_installation_issue_32bit_supervised(
    arch: str,
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
    freezer=Depends(freezer_fx),
) -> None:
    """Test deprecated architecture issue."""
    with (
        patch.dict(os.environ, MOCK_ENVIRON),
        patch(
            "homeassistant.components.hassio._is_32_bit",
            return_value=True,
        ),
        patch(
            "homeassistant.components.hassio.get_os_info",
            return_value={"board": "rpi3-64"},
        ),
        patch(
            "homeassistant.components.hassio.get_info",
            return_value={"hassos": None, "arch": arch},
        ),
        patch("homeassistant.components.hardware.async_setup", return_value=True),
    ):
        expect(await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})).to_be_truthy()
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()
        freezer.tick(REQUEST_REFRESH_DELAY)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        await hass.services.async_call(
            HOMEASSISTANT_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {
                "entity_id": [
                    "update.home_assistant_core_update",
                    "update.home_assistant_supervisor_update",
                ]
            },
            blocking=True,
        )
        freezer.tick(HASSIO_MAIN_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    expect(len(issue_registry.issues)).to_equal(1)
    issue = issue_registry.async_get_issue(
        "homeassistant", "deprecated_method_architecture"
    )
    expect(issue.domain).to_equal("homeassistant")
    expect(issue.severity).to_equal(ir.IssueSeverity.WARNING)
    expect(issue.translation_placeholders).to_equal(
        {"installation_type": "Supervised", "arch": arch}
    )


@test.cases(
    test.case("amd64", arch="amd64"),
    test.case("aarch64", arch="aarch64"),
)
async def deprecated_installation_issue_64bit_supervised(
    arch: str,
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
    freezer=Depends(freezer_fx),
) -> None:
    """Test deprecated architecture issue."""
    with (
        patch.dict(os.environ, MOCK_ENVIRON),
        patch(
            "homeassistant.components.hassio._is_32_bit",
            return_value=False,
        ),
        patch(
            "homeassistant.components.hassio.get_os_info",
            return_value={"board": "generic-x86-64"},
        ),
        patch(
            "homeassistant.components.hassio.get_info",
            return_value={"hassos": None, "arch": arch},
        ),
        patch("homeassistant.components.hardware.async_setup", return_value=True),
    ):
        expect(await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})).to_be_truthy()
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()
        freezer.tick(REQUEST_REFRESH_DELAY)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        await hass.services.async_call(
            HOMEASSISTANT_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {
                "entity_id": [
                    "update.home_assistant_core_update",
                    "update.home_assistant_supervisor_update",
                ]
            },
            blocking=True,
        )
        freezer.tick(HASSIO_MAIN_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    expect(len(issue_registry.issues)).to_equal(1)
    issue = issue_registry.async_get_issue("homeassistant", "deprecated_method")
    expect(issue.domain).to_equal("homeassistant")
    expect(issue.severity).to_equal(ir.IssueSeverity.WARNING)
    expect(issue.translation_placeholders).to_equal(
        {"installation_type": "Supervised", "arch": arch}
    )


@test.cases(
    test.case("rpi5", board="rpi5", issue_id="deprecated_os_aarch64"),
)
async def deprecated_installation_issue_supported_board(
    board: str,
    issue_id: str,
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fx),
    freezer=Depends(freezer_fx),
) -> None:
    """Test no deprecated installation issue for a supported board."""
    with (
        patch.dict(os.environ, MOCK_ENVIRON),
        patch(
            "homeassistant.components.hassio._is_32_bit",
            return_value=False,
        ),
        patch(
            "homeassistant.components.hassio.get_os_info", return_value={"board": board}
        ),
        patch(
            "homeassistant.components.hassio.get_info",
            return_value={"hassos": True, "arch": "aarch64"},
        ),
    ):
        expect(await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})).to_be_truthy()
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()
        freezer.tick(REQUEST_REFRESH_DELAY)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        await hass.services.async_call(
            HOMEASSISTANT_DOMAIN,
            SERVICE_UPDATE_ENTITY,
            {
                "entity_id": [
                    "update.home_assistant_core_update",
                    "update.home_assistant_supervisor_update",
                ]
            },
            blocking=True,
        )
        freezer.tick(HASSIO_MAIN_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    expect(len(issue_registry.issues)).to_equal(0)


async def _mount_reload_test_setup(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    supervisor_client: AsyncMock,
) -> dr.DeviceEntry:
    """Set up mount reload test and return the device entry."""
    supervisor_client.mounts.info = AsyncMock(
        return_value=MountsInfo(
            default_backup_mount=None,
            mounts=[
                CIFSMountResponse(
                    share="files",
                    server="1.2.3.4",
                    name="NAS",
                    type=MountType.CIFS,
                    usage=MountUsage.SHARE,
                    read_only=False,
                    state=MountState.ACTIVE,
                    user_path=PurePath("/share/nas"),
                )
            ],
        )
    )

    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, "mount_NAS")})
    assert device is not None
    return device


@test
async def mount_reload_action(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test reload_mount service call."""
    device = await _mount_reload_test_setup(hass, device_registry, supervisor_client)
    await hass.services.async_call(
        "hassio", "mount_reload", {"device_id": device.id}, blocking=True
    )
    supervisor_client.mounts.reload_mount.assert_awaited_once_with("NAS")


@test
async def mount_reload_action_failure(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test reload_mount service call failure."""
    device = await _mount_reload_test_setup(hass, device_registry, supervisor_client)
    supervisor_client.mounts.reload_mount = AsyncMock(
        side_effect=SupervisorError("test failure")
    )
    async with expect_raises_async(HomeAssistantError, match="mount_reload_error"):
        await hass.services.async_call(
            "hassio", "mount_reload", {"device_id": device.id}, blocking=True
        )


@test
async def mount_reload_unknown_device_id(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test reload_mount with unknown device ID."""
    await _mount_reload_test_setup(hass, device_registry, supervisor_client)
    async with expect_raises_async(ServiceValidationError, match="mount_reload_unknown_device_id"):
        await hass.services.async_call(
            "hassio", "mount_reload", {"device_id": "1234"}, blocking=True
        )


@test
async def mount_reload_no_name(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test reload_mount with an unnamed device."""
    device = await _mount_reload_test_setup(hass, device_registry, supervisor_client)
    device_registry.async_update_device(device.id, name=None)
    async with expect_raises_async(ServiceValidationError, match="mount_reload_invalid_device"):
        await hass.services.async_call(
            "hassio", "mount_reload", {"device_id": device.id}, blocking=True
        )


@test
async def mount_reload_invalid_model(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test reload_mount with an invalid model."""
    device = await _mount_reload_test_setup(hass, device_registry, supervisor_client)
    device_registry.async_update_device(device.id, model=None)
    async with expect_raises_async(ServiceValidationError, match="mount_reload_invalid_device"):
        await hass.services.async_call(
            "hassio", "mount_reload", {"device_id": device.id}, blocking=True
        )


@test
async def mount_reload_not_supervisor_device(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test reload_mount with a device not belonging to the supervisor."""
    device = await _mount_reload_test_setup(hass, device_registry, supervisor_client)
    config_entry = MockConfigEntry()
    config_entry.add_to_hass(hass)
    device2 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("test", "test")},
        name=device.name,
        model=device.model,
    )
    async with expect_raises_async(ServiceValidationError, match="mount_reload_invalid_device"):
        await hass.services.async_call(
            "hassio", "mount_reload", {"device_id": device2.id}, blocking=True
        )


@test
async def mount_reload_selector_matches_device_name(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Test that the model name in the selector of mount reload is valid."""
    device = await _mount_reload_test_setup(hass, device_registry, supervisor_client)
    services = load_yaml_dict(f"{hassio.__path__[0]}/services.yaml")
    expect(
        services["mount_reload"]["fields"]["device_id"]["selector"]["device"]["filter"][
            "model"
        ]
    ).to_equal(device.model)


@test
async def get_supervisor_info_test(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_supervisor_info returns a dict with backwards-compat keys."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    result = get_supervisor_info(hass)
    expect(isinstance(result, dict)).to_be_truthy()
    expect("repositories" in result).to_be_truthy()
    expect(isinstance(result["repositories"], list)).to_be_truthy()
    expect("addons" in result).to_be_truthy()
    expect(isinstance(result["addons"], list)).to_be_truthy()
    expect(all(isinstance(addon, dict) for addon in result["addons"])).to_be_truthy()


@test
async def get_info_test(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_info returns serialized dict with expected values."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    result = get_info(hass)
    expect(isinstance(result, dict)).to_be_truthy()
    expect(result["supervisor"]).to_equal("222")
    expect(result["homeassistant"]).to_equal("0.110.0")
    expect(result["hassos"]).to_equal("1.2.3")


@test
async def get_host_info_test(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_host_info returns serialized dict with expected values."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    result = get_host_info(hass)
    expect(isinstance(result, dict)).to_be_truthy()
    expect(result["chassis"]).to_equal("vm")
    expect(result["disk_total"]).to_equal(100.0)
    expect(result["kernel"]).to_equal("4.19.0-6-amd64")


@test
async def get_store_test(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_store returns serialized dict with expected values."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    result = get_store(hass)
    expect(isinstance(result, dict)).to_be_truthy()
    expect("addons" in result).to_be_truthy()
    expect("repositories" in result).to_be_truthy()
    expect(isinstance(result["addons"], list)).to_be_truthy()
    expect(isinstance(result["repositories"], list)).to_be_truthy()


@test
async def get_network_info_test(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_network_info returns serialized dict with expected values."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    result = get_network_info(hass)
    expect(isinstance(result, dict)).to_be_truthy()
    expect(result["host_internet"]).to_be_truthy()
    expect(result["supervisor_internet"]).to_be_truthy()
    expect(isinstance(result["interfaces"], list)).to_be_truthy()


@test
async def get_addons_info_test(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_addons_info returns serialized dicts, not model objects."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    result = get_addons_info(hass)
    expect(isinstance(result, dict)).to_be_truthy()
    expect("test" in result).to_be_truthy()
    expect(isinstance(result["test"], dict)).to_be_truthy()
    expect(result["test"]["slug"]).to_equal("test")
    expect(result["test"]["version"]).to_equal("1.0.0")
    expect(result["test"]["hassio_api"]).to_be_falsy()
    expect(result["test"]["supervisor_api"]).to_be_falsy()
    expect(result["test"]["hassio_role"]).to_equal("default")
    expect(result["test"]["supervisor_role"]).to_equal("default")


@test
async def get_addons_list_test(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_addons_list returns a list of serialized dicts."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    result = get_addons_list(hass)
    expect(isinstance(result, list)).to_be_truthy()
    expect(all(isinstance(addon, dict) for addon in result)).to_be_truthy()
    slugs = {addon["slug"] for addon in result}
    expect("test" in slugs).to_be_truthy()
    expect("test2" in slugs).to_be_truthy()


@test
async def get_addons_stats_test(
    _mock_all: None = Depends(mock_all),
    _enabled: None = Depends(entity_registry_enabled_by_default_fx),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_addons_stats returns serialized dicts, not model objects."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    result = get_addons_stats(hass)
    expect(isinstance(result, dict)).to_be_truthy()
    for stats in result.values():
        expect(isinstance(stats, dict)).to_be_truthy()


@test
async def get_core_stats_test(
    _mock_all: None = Depends(mock_all),
    _enabled: None = Depends(entity_registry_enabled_by_default_fx),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_core_stats returns serialized dict with expected values."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    async_fire_time_changed(
        hass, dt_util.now() + timedelta(seconds=REQUEST_REFRESH_DELAY)
    )
    await hass.async_block_till_done()

    result = get_core_stats(hass)
    expect(isinstance(result, dict)).to_be_truthy()
    expect(result["cpu_percent"]).to_equal(0.99)
    expect(result["memory_percent"]).to_equal(4.59)


@test
async def get_supervisor_stats_test(
    _mock_all: None = Depends(mock_all),
    _enabled: None = Depends(entity_registry_enabled_by_default_fx),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_supervisor_stats returns serialized dict with expected values."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    async_fire_time_changed(
        hass, dt_util.now() + timedelta(seconds=REQUEST_REFRESH_DELAY)
    )
    await hass.async_block_till_done()

    result = get_supervisor_stats(hass)
    expect(isinstance(result, dict)).to_be_truthy()
    expect(result["cpu_percent"]).to_equal(0.99)
    expect(result["memory_percent"]).to_equal(4.59)


@test
async def get_os_info_test(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_os_info returns serialized dict with expected values."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    result = get_os_info(hass)
    expect(isinstance(result, dict)).to_be_truthy()
    expect(result["version"]).to_equal("1.0.0")
    expect(result["version_latest"]).to_equal("1.0.0")
    expect(result["update_available"]).to_be_falsy()


@test
async def get_core_info_test(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test get_core_info returns serialized dict with expected values."""
    with patch.dict(os.environ, MOCK_ENVIRON):
        config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    result = get_core_info(hass)
    expect(isinstance(result, dict)).to_be_truthy()
    expect(result["version"]).to_equal("1.0.0")
    expect(result["version_latest"]).to_equal("1.0.0")
    expect(result["image"]).to_equal("homeassistant")
