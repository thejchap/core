"""Test the addon manager."""

import asyncio
from unittest.mock import AsyncMock, call
from uuid import uuid4

from aiohasupervisor import (
    AddonNotSupportedArchitectureError,
    AddonNotSupportedHomeAssistantVersionError,
    AddonNotSupportedMachineTypeError,
    SupervisorError,
)
from aiohasupervisor.models import AddonsOptions, Discovery, PartialBackupOptions
from tryke import Depends, expect, fixture, test

from homeassistant.components.hassio.addon_manager import (
    AddonError,
    AddonInfo,
    AddonManager,
    AddonState,
)
from homeassistant.core import HomeAssistant

from ._fixtures import (
    addon_info,
    addon_installed,
    addon_manager,
    addon_not_installed,
    addon_store_info,
    create_backup,
    get_addon_discovery_info,
    install_addon,
    restart_addon,
    set_addon_options,
    set_addon_options_no_side_effect,
    start_addon,
    stop_addon,
    supervisor_client,
    uninstall_addon,
    update_addon,
)

from tests.hass_fixtures import (
    caplog as caplog_fx,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt into Tryke's HookExecutor path for async fixtures."""
    return 0


@test
async def not_installed_raises_exception(
    addon_manager: AddonManager = Depends(addon_manager),
    _not_installed: AsyncMock = Depends(addon_not_installed),
) -> None:
    """Test addon not installed raises exception."""
    addon_config = {"test_key": "test"}

    async with expect_raises_async(AddonError, match=r"Test app is not installed"):
        await addon_manager.async_configure_addon(addon_config)

    async with expect_raises_async(AddonError, match=r"Test app is not installed"):
        await addon_manager.async_update_addon()


@test.cases(
    test.case(
        "arch",
        exception=AddonNotSupportedArchitectureError(
            "Add-on test not supported on this platform, supported architectures: test"
        ),
    ),
    test.case(
        "ha_version",
        exception=AddonNotSupportedHomeAssistantVersionError(
            "Add-on test not supported on this system, requires Home Assistant version 2026.1.0 or greater"
        ),
    ),
    test.case(
        "machine_type",
        exception=AddonNotSupportedMachineTypeError(
            "Add-on test not supported on this machine, supported machine types: test"
        ),
    ),
)
async def not_available_raises_exception(
    exception: SupervisorError,
    addon_manager: AddonManager = Depends(addon_manager),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    addon_info: AsyncMock = Depends(addon_info),
) -> None:
    """Test addon not available raises exception."""
    supervisor_client.store.addon_availability.side_effect = exception
    supervisor_client.store.install_addon.side_effect = exception
    addon_info.return_value.update_available = True

    async with expect_raises_async(
        AddonError, match=rf"Test app is not available: {exception!s}"
    ):
        await addon_manager.async_install_addon()

    async with expect_raises_async(
        AddonError, match=rf"Test app is not available: {exception!s}"
    ):
        await addon_manager.async_update_addon()


@test
async def get_addon_discovery_info_test(
    addon_manager: AddonManager = Depends(addon_manager),
    get_addon_discovery_info: AsyncMock = Depends(get_addon_discovery_info),
) -> None:
    """Test get addon discovery info."""
    get_addon_discovery_info.return_value = [
        Discovery(
            addon="test_addon", service="", uuid=uuid4(), config={"test_key": "test"}
        )
    ]

    expect(await addon_manager.async_get_addon_discovery_info()).to_equal(
        {"test_key": "test"}
    )
    expect(get_addon_discovery_info.call_count).to_equal(1)


@test
async def missing_addon_discovery_info(
    addon_manager: AddonManager = Depends(addon_manager),
    get_addon_discovery_info: AsyncMock = Depends(get_addon_discovery_info),
) -> None:
    """Test missing addon discovery info."""
    async with expect_raises_async(AddonError):
        await addon_manager.async_get_addon_discovery_info()

    expect(get_addon_discovery_info.call_count).to_equal(1)


@test
async def get_addon_discovery_info_error(
    addon_manager: AddonManager = Depends(addon_manager),
    get_addon_discovery_info: AsyncMock = Depends(get_addon_discovery_info),
) -> None:
    """Test get addon discovery info raises error."""
    get_addon_discovery_info.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to get the Test app discovery info: Boom"
    ):
        await addon_manager.async_get_addon_discovery_info()

    expect(get_addon_discovery_info.call_count).to_equal(1)


@test
async def get_addon_info_not_installed(
    addon_manager: AddonManager = Depends(addon_manager),
    addon_not_installed: AsyncMock = Depends(addon_not_installed),
) -> None:
    """Test get addon info when addon is not installed."""
    expect(await addon_manager.async_get_addon_info()).to_equal(
        AddonInfo(
            available=True,
            hostname=None,
            options={},
            state=AddonState.NOT_INSTALLED,
            update_available=False,
            version=None,
        )
    )


@test.cases(
    test.case("started", addon_info_state="started", addon_state=AddonState.RUNNING),
    test.case(
        "stopped", addon_info_state="stopped", addon_state=AddonState.NOT_RUNNING
    ),
)
async def get_addon_info_test(
    addon_info_state: str,
    addon_state: AddonState,
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
) -> None:
    """Test get addon info when addon is installed."""
    addon_installed.return_value.state = addon_info_state
    expect(await addon_manager.async_get_addon_info()).to_equal(
        AddonInfo(
            available=True,
            hostname="core-test-addon",
            options={},
            state=addon_state,
            update_available=False,
            version="1.0.0",
        )
    )


@test.cases(
    test.case(
        "addon_info_error",
        addon_info_error=SupervisorError("Boom"),
        addon_info_calls=1,
        addon_store_info_error=None,
        addon_store_info_calls=1,
    ),
    test.case(
        "addon_store_info_error",
        addon_info_error=None,
        addon_info_calls=0,
        addon_store_info_error=SupervisorError("Boom"),
        addon_store_info_calls=1,
    ),
)
async def get_addon_info_error(
    addon_info_error: Exception | None,
    addon_info_calls: int,
    addon_store_info_error: Exception | None,
    addon_store_info_calls: int,
    addon_manager: AddonManager = Depends(addon_manager),
    addon_info: AsyncMock = Depends(addon_info),
    addon_store_info: AsyncMock = Depends(addon_store_info),
    _addon_installed: AsyncMock = Depends(addon_installed),
) -> None:
    """Test get addon info raises error."""
    addon_info.side_effect = addon_info_error
    addon_store_info.side_effect = addon_store_info_error

    async with expect_raises_async(
        AddonError, match=r"Failed to get the Test app info: Boom"
    ):
        await addon_manager.async_get_addon_info()

    expect(addon_info.call_count).to_equal(addon_info_calls)
    expect(addon_store_info.call_count).to_equal(addon_store_info_calls)


@test
async def set_addon_options_test(
    hass: HomeAssistant = Depends(hass_fixture),
    addon_manager: AddonManager = Depends(addon_manager),
    set_addon_options: AsyncMock = Depends(set_addon_options),
) -> None:
    """Test set addon options."""
    await addon_manager.async_set_addon_options({"test_key": "test"})

    expect(set_addon_options.call_count).to_equal(1)
    expect(set_addon_options.call_args).to_equal(
        call("test_addon", AddonsOptions(config={"test_key": "test"}))
    )


@test
async def set_addon_options_error(
    hass: HomeAssistant = Depends(hass_fixture),
    addon_manager: AddonManager = Depends(addon_manager),
    set_addon_options: AsyncMock = Depends(set_addon_options),
) -> None:
    """Test set addon options raises error."""
    set_addon_options.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to set the Test app options: Boom"
    ):
        await addon_manager.async_set_addon_options({"test_key": "test"})

    expect(set_addon_options.call_count).to_equal(1)
    expect(set_addon_options.call_args).to_equal(
        call("test_addon", AddonsOptions(config={"test_key": "test"}))
    )


@test
async def install_addon_test(
    addon_manager: AddonManager = Depends(addon_manager),
    install_addon: AsyncMock = Depends(install_addon),
    addon_store_info: AsyncMock = Depends(addon_store_info),
    addon_info: AsyncMock = Depends(addon_info),
) -> None:
    """Test install addon."""
    addon_store_info.return_value.available = True
    addon_info.return_value.available = True

    await addon_manager.async_install_addon()

    expect(install_addon.call_count).to_equal(1)


@test
async def install_addon_error(
    addon_manager: AddonManager = Depends(addon_manager),
    install_addon: AsyncMock = Depends(install_addon),
    addon_store_info: AsyncMock = Depends(addon_store_info),
    addon_info: AsyncMock = Depends(addon_info),
) -> None:
    """Test install addon raises error."""
    addon_store_info.return_value.available = True
    addon_info.return_value.available = True
    install_addon.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to install the Test app: Boom"
    ):
        await addon_manager.async_install_addon()

    expect(install_addon.call_count).to_equal(1)


@test
async def schedule_install_addon(
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
    install_addon: AsyncMock = Depends(install_addon),
) -> None:
    """Test schedule install addon."""
    install_task = addon_manager.async_schedule_install_addon()

    expect(addon_manager.task_in_progress()).to_be(True)

    expect(await addon_manager.async_get_addon_info()).to_equal(
        AddonInfo(
            available=True,
            hostname="core-test-addon",
            options={},
            state=AddonState.INSTALLING,
            update_available=False,
            version="1.0.0",
        )
    )

    install_task_two = addon_manager.async_schedule_install_addon()

    await asyncio.gather(install_task, install_task_two)

    expect(addon_manager.task_in_progress()).to_be(False)
    expect(install_addon.call_count).to_equal(1)

    install_addon.reset_mock()

    await addon_manager.async_schedule_install_addon()

    expect(install_addon.call_count).to_equal(1)


@test
async def schedule_install_addon_error(
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
    install_addon: AsyncMock = Depends(install_addon),
) -> None:
    """Test schedule install addon raises error."""
    install_addon.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to install the Test app: Boom"
    ):
        await addon_manager.async_schedule_install_addon()

    expect(install_addon.call_count).to_equal(1)


@test
async def schedule_install_addon_logs_error(
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
    install_addon: AsyncMock = Depends(install_addon),
    caplog=Depends(caplog_fx),
) -> None:
    """Test schedule install addon logs error."""
    install_addon.side_effect = SupervisorError("Boom")

    await addon_manager.async_schedule_install_addon(catch_error=True)

    expect("Failed to install the Test app: Boom" in caplog.text).to_be(True)
    expect(install_addon.call_count).to_equal(1)


@test
async def uninstall_addon_test(
    addon_manager: AddonManager = Depends(addon_manager),
    uninstall_addon: AsyncMock = Depends(uninstall_addon),
) -> None:
    """Test uninstall addon."""
    await addon_manager.async_uninstall_addon()

    expect(uninstall_addon.call_count).to_equal(1)


@test
async def uninstall_addon_error(
    addon_manager: AddonManager = Depends(addon_manager),
    uninstall_addon: AsyncMock = Depends(uninstall_addon),
) -> None:
    """Test uninstall addon raises error."""
    uninstall_addon.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to uninstall the Test app: Boom"
    ):
        await addon_manager.async_uninstall_addon()

    expect(uninstall_addon.call_count).to_equal(1)


@test
async def start_addon_test(
    addon_manager: AddonManager = Depends(addon_manager),
    start_addon: AsyncMock = Depends(start_addon),
) -> None:
    """Test start addon."""
    await addon_manager.async_start_addon()

    expect(start_addon.call_count).to_equal(1)


@test
async def start_addon_error(
    addon_manager: AddonManager = Depends(addon_manager),
    start_addon: AsyncMock = Depends(start_addon),
) -> None:
    """Test start addon raises error."""
    start_addon.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to start the Test app: Boom"
    ):
        await addon_manager.async_start_addon()

    expect(start_addon.call_count).to_equal(1)


@test
async def schedule_start_addon(
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
    start_addon: AsyncMock = Depends(start_addon),
) -> None:
    """Test schedule start addon."""
    start_task = addon_manager.async_schedule_start_addon()

    expect(addon_manager.task_in_progress()).to_be(True)

    start_task_two = addon_manager.async_schedule_start_addon()

    await asyncio.gather(start_task, start_task_two)

    expect(addon_manager.task_in_progress()).to_be(False)
    expect(start_addon.call_count).to_equal(1)

    start_addon.reset_mock()

    await addon_manager.async_schedule_start_addon()

    expect(start_addon.call_count).to_equal(1)


@test
async def schedule_start_addon_error(
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
    start_addon: AsyncMock = Depends(start_addon),
) -> None:
    """Test schedule start addon raises error."""
    start_addon.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to start the Test app: Boom"
    ):
        await addon_manager.async_schedule_start_addon()

    expect(start_addon.call_count).to_equal(1)


@test
async def schedule_start_addon_logs_error(
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
    start_addon: AsyncMock = Depends(start_addon),
    caplog=Depends(caplog_fx),
) -> None:
    """Test schedule start addon logs error."""
    start_addon.side_effect = SupervisorError("Boom")

    await addon_manager.async_schedule_start_addon(catch_error=True)

    expect("Failed to start the Test app: Boom" in caplog.text).to_be(True)
    expect(start_addon.call_count).to_equal(1)


@test
async def restart_addon_test(
    addon_manager: AddonManager = Depends(addon_manager),
    restart_addon: AsyncMock = Depends(restart_addon),
) -> None:
    """Test restart addon."""
    await addon_manager.async_restart_addon()

    expect(restart_addon.call_count).to_equal(1)


@test
async def restart_addon_error(
    addon_manager: AddonManager = Depends(addon_manager),
    restart_addon: AsyncMock = Depends(restart_addon),
) -> None:
    """Test restart addon raises error."""
    restart_addon.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to restart the Test app: Boom"
    ):
        await addon_manager.async_restart_addon()

    expect(restart_addon.call_count).to_equal(1)


@test
async def schedule_restart_addon(
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
    restart_addon: AsyncMock = Depends(restart_addon),
) -> None:
    """Test schedule restart addon."""
    restart_task = addon_manager.async_schedule_restart_addon()

    expect(addon_manager.task_in_progress()).to_be(True)

    restart_task_two = addon_manager.async_schedule_restart_addon()

    await asyncio.gather(restart_task, restart_task_two)

    expect(addon_manager.task_in_progress()).to_be(False)
    expect(restart_addon.call_count).to_equal(1)

    restart_addon.reset_mock()

    await addon_manager.async_schedule_restart_addon()

    expect(restart_addon.call_count).to_equal(1)


@test
async def schedule_restart_addon_error(
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
    restart_addon: AsyncMock = Depends(restart_addon),
) -> None:
    """Test schedule restart addon raises error."""
    restart_addon.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to restart the Test app: Boom"
    ):
        await addon_manager.async_schedule_restart_addon()

    expect(restart_addon.call_count).to_equal(1)


@test
async def schedule_restart_addon_logs_error(
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
    restart_addon: AsyncMock = Depends(restart_addon),
    caplog=Depends(caplog_fx),
) -> None:
    """Test schedule restart addon logs error."""
    restart_addon.side_effect = SupervisorError("Boom")

    await addon_manager.async_schedule_restart_addon(catch_error=True)

    expect("Failed to restart the Test app: Boom" in caplog.text).to_be(True)
    expect(restart_addon.call_count).to_equal(1)


@test
async def stop_addon_test(
    addon_manager: AddonManager = Depends(addon_manager),
    stop_addon: AsyncMock = Depends(stop_addon),
) -> None:
    """Test stop addon."""
    await addon_manager.async_stop_addon()

    expect(stop_addon.call_count).to_equal(1)


@test
async def stop_addon_error(
    addon_manager: AddonManager = Depends(addon_manager),
    stop_addon: AsyncMock = Depends(stop_addon),
) -> None:
    """Test stop addon raises error."""
    stop_addon.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to stop the Test app: Boom"
    ):
        await addon_manager.async_stop_addon()

    expect(stop_addon.call_count).to_equal(1)


@test
async def update_addon_test(
    hass: HomeAssistant = Depends(hass_fixture),
    addon_manager: AddonManager = Depends(addon_manager),
    _installed: AsyncMock = Depends(addon_installed),
    addon_info: AsyncMock = Depends(addon_info),
    create_backup: AsyncMock = Depends(create_backup),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test update addon."""
    addon_info.return_value.update_available = True

    await addon_manager.async_update_addon()

    expect(addon_info.call_count).to_equal(1)
    expect(create_backup.call_count).to_equal(1)
    expect(create_backup.call_args).to_equal(
        call(PartialBackupOptions(name="addon_test_addon_1.0.0", addons={"test_addon"}))
    )
    expect(update_addon.call_count).to_equal(1)


@test
async def update_addon_no_update(
    addon_manager: AddonManager = Depends(addon_manager),
    _installed: AsyncMock = Depends(addon_installed),
    addon_info: AsyncMock = Depends(addon_info),
    create_backup: AsyncMock = Depends(create_backup),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test update addon without update available."""
    addon_info.return_value.update_available = False

    await addon_manager.async_update_addon()

    expect(addon_info.call_count).to_equal(1)
    expect(create_backup.call_count).to_equal(0)
    expect(update_addon.call_count).to_equal(0)


@test
async def update_addon_error(
    hass: HomeAssistant = Depends(hass_fixture),
    addon_manager: AddonManager = Depends(addon_manager),
    _installed: AsyncMock = Depends(addon_installed),
    addon_info: AsyncMock = Depends(addon_info),
    create_backup: AsyncMock = Depends(create_backup),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test update addon raises error."""
    addon_info.return_value.update_available = True
    update_addon.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to update the Test app: Boom"
    ):
        await addon_manager.async_update_addon()

    expect(addon_info.call_count).to_equal(1)
    expect(create_backup.call_count).to_equal(1)
    expect(create_backup.call_args).to_equal(
        call(PartialBackupOptions(name="addon_test_addon_1.0.0", addons={"test_addon"}))
    )
    expect(update_addon.call_count).to_equal(1)


@test
async def schedule_update_addon(
    hass: HomeAssistant = Depends(hass_fixture),
    addon_manager: AddonManager = Depends(addon_manager),
    _installed: AsyncMock = Depends(addon_installed),
    addon_info: AsyncMock = Depends(addon_info),
    create_backup: AsyncMock = Depends(create_backup),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test schedule update addon."""
    addon_info.return_value.update_available = True

    update_task = addon_manager.async_schedule_update_addon()

    expect(addon_manager.task_in_progress()).to_be(True)

    expect(await addon_manager.async_get_addon_info()).to_equal(
        AddonInfo(
            available=True,
            hostname="core-test-addon",
            options={},
            state=AddonState.UPDATING,
            update_available=True,
            version="1.0.0",
        )
    )

    update_task_two = addon_manager.async_schedule_update_addon()

    await asyncio.gather(update_task, update_task_two)

    expect(addon_manager.task_in_progress()).to_be(False)
    expect(addon_info.call_count).to_equal(2)
    expect(create_backup.call_count).to_equal(1)
    expect(create_backup.call_args).to_equal(
        call(PartialBackupOptions(name="addon_test_addon_1.0.0", addons={"test_addon"}))
    )
    expect(update_addon.call_count).to_equal(1)

    update_addon.reset_mock()

    await addon_manager.async_schedule_update_addon()

    expect(update_addon.call_count).to_equal(1)


@test.cases(
    test.case(
        "create_backup_error",
        create_backup_error=SupervisorError("Boom"),
        create_backup_calls=1,
        update_addon_error=None,
        update_addon_calls=0,
        error_message="Failed to create a backup of the Test app: Boom",
    ),
    test.case(
        "update_addon_error",
        create_backup_error=None,
        create_backup_calls=1,
        update_addon_error=SupervisorError("Boom"),
        update_addon_calls=1,
        error_message="Failed to update the Test app: Boom",
    ),
)
async def schedule_update_addon_error(
    create_backup_error: Exception | None,
    create_backup_calls: int,
    update_addon_error: Exception | None,
    update_addon_calls: int,
    error_message: str,
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
    create_backup: AsyncMock = Depends(create_backup),
    update_addon: AsyncMock = Depends(update_addon),
) -> None:
    """Test schedule update addon raises error."""
    addon_installed.return_value.update_available = True
    create_backup.side_effect = create_backup_error
    update_addon.side_effect = update_addon_error

    async with expect_raises_async(AddonError, match=rf"{error_message}"):
        await addon_manager.async_schedule_update_addon()

    expect(create_backup.call_count).to_equal(create_backup_calls)
    expect(update_addon.call_count).to_equal(update_addon_calls)


@test.cases(
    test.case(
        "create_backup_error",
        create_backup_error=SupervisorError("Boom"),
        create_backup_calls=1,
        update_addon_error=None,
        update_addon_calls=0,
        error_log="Failed to create a backup of the Test app: Boom",
    ),
    test.case(
        "update_addon_error",
        create_backup_error=None,
        create_backup_calls=1,
        update_addon_error=SupervisorError("Boom"),
        update_addon_calls=1,
        error_log="Failed to update the Test app: Boom",
    ),
)
async def schedule_update_addon_logs_error(
    create_backup_error: Exception | None,
    create_backup_calls: int,
    update_addon_error: Exception | None,
    update_addon_calls: int,
    error_log: str,
    addon_manager: AddonManager = Depends(addon_manager),
    addon_installed: AsyncMock = Depends(addon_installed),
    create_backup: AsyncMock = Depends(create_backup),
    update_addon: AsyncMock = Depends(update_addon),
    caplog=Depends(caplog_fx),
) -> None:
    """Test schedule update addon logs error."""
    addon_installed.return_value.update_available = True
    create_backup.side_effect = create_backup_error
    update_addon.side_effect = update_addon_error

    await addon_manager.async_schedule_update_addon(catch_error=True)

    expect(error_log in caplog.text).to_be(True)
    expect(create_backup.call_count).to_equal(create_backup_calls)
    expect(update_addon.call_count).to_equal(update_addon_calls)


@test
async def create_backup_test(
    hass: HomeAssistant = Depends(hass_fixture),
    addon_manager: AddonManager = Depends(addon_manager),
    addon_info: AsyncMock = Depends(addon_info),
    _installed: AsyncMock = Depends(addon_installed),
    create_backup: AsyncMock = Depends(create_backup),
) -> None:
    """Test creating a backup of the addon."""
    await addon_manager.async_create_backup()

    expect(addon_info.call_count).to_equal(1)
    expect(create_backup.call_count).to_equal(1)
    expect(create_backup.call_args).to_equal(
        call(PartialBackupOptions(name="addon_test_addon_1.0.0", addons={"test_addon"}))
    )


@test
async def create_backup_error(
    hass: HomeAssistant = Depends(hass_fixture),
    addon_manager: AddonManager = Depends(addon_manager),
    addon_info: AsyncMock = Depends(addon_info),
    _installed: AsyncMock = Depends(addon_installed),
    create_backup: AsyncMock = Depends(create_backup),
) -> None:
    """Test creating a backup of the addon raises error."""
    create_backup.side_effect = SupervisorError("Boom")

    async with expect_raises_async(
        AddonError, match=r"Failed to create a backup of the Test app: Boom"
    ):
        await addon_manager.async_create_backup()

    expect(addon_info.call_count).to_equal(1)
    expect(create_backup.call_count).to_equal(1)
    expect(create_backup.call_args).to_equal(
        call(PartialBackupOptions(name="addon_test_addon_1.0.0", addons={"test_addon"}))
    )


@test
async def schedule_install_setup_addon(
    addon_manager: AddonManager = Depends(addon_manager),
    _installed: AsyncMock = Depends(addon_installed),
    install_addon: AsyncMock = Depends(install_addon),
    set_addon_options: AsyncMock = Depends(set_addon_options_no_side_effect),
    start_addon: AsyncMock = Depends(start_addon),
) -> None:
    """Test schedule install setup addon."""
    install_task = addon_manager.async_schedule_install_setup_addon(
        {"test_key": "test"}
    )

    expect(addon_manager.task_in_progress()).to_be(True)

    install_task_two = addon_manager.async_schedule_install_setup_addon(
        {"test_key": "test"}
    )

    await asyncio.gather(install_task, install_task_two)

    expect(addon_manager.task_in_progress()).to_be(False)
    expect(install_addon.call_count).to_equal(1)
    expect(set_addon_options.call_count).to_equal(1)
    expect(start_addon.call_count).to_equal(1)

    install_addon.reset_mock()
    set_addon_options.reset_mock()
    start_addon.reset_mock()

    await addon_manager.async_schedule_install_setup_addon({"test_key": "test"})

    expect(install_addon.call_count).to_equal(1)
    expect(set_addon_options.call_count).to_equal(1)
    expect(start_addon.call_count).to_equal(1)


@test.cases(
    test.case(
        "install_error",
        install_addon_error=SupervisorError("Boom"),
        install_addon_calls=1,
        set_addon_options_error=None,
        set_addon_options_calls=0,
        start_addon_error=None,
        start_addon_calls=0,
        error_message="Failed to install the Test app: Boom",
    ),
    test.case(
        "set_options_error",
        install_addon_error=None,
        install_addon_calls=1,
        set_addon_options_error=SupervisorError("Boom"),
        set_addon_options_calls=1,
        start_addon_error=None,
        start_addon_calls=0,
        error_message="Failed to set the Test app options: Boom",
    ),
    test.case(
        "start_error",
        install_addon_error=None,
        install_addon_calls=1,
        set_addon_options_error=None,
        set_addon_options_calls=1,
        start_addon_error=SupervisorError("Boom"),
        start_addon_calls=1,
        error_message="Failed to start the Test app: Boom",
    ),
)
async def schedule_install_setup_addon_error(
    install_addon_error: Exception | None,
    install_addon_calls: int,
    set_addon_options_error: Exception | None,
    set_addon_options_calls: int,
    start_addon_error: Exception | None,
    start_addon_calls: int,
    error_message: str,
    addon_manager: AddonManager = Depends(addon_manager),
    _installed: AsyncMock = Depends(addon_installed),
    install_addon: AsyncMock = Depends(install_addon),
    set_addon_options: AsyncMock = Depends(set_addon_options),
    start_addon: AsyncMock = Depends(start_addon),
) -> None:
    """Test schedule install setup addon raises error."""
    install_addon.side_effect = install_addon_error
    set_addon_options.side_effect = set_addon_options_error
    start_addon.side_effect = start_addon_error

    async with expect_raises_async(AddonError, match=rf"{error_message}"):
        await addon_manager.async_schedule_install_setup_addon({"test_key": "test"})

    expect(install_addon.call_count).to_equal(install_addon_calls)
    expect(set_addon_options.call_count).to_equal(set_addon_options_calls)
    expect(start_addon.call_count).to_equal(start_addon_calls)


@test.cases(
    test.case(
        "install_error",
        install_addon_error=SupervisorError("Boom"),
        install_addon_calls=1,
        set_addon_options_error=None,
        set_addon_options_calls=0,
        start_addon_error=None,
        start_addon_calls=0,
        error_log="Failed to install the Test app: Boom",
    ),
    test.case(
        "set_options_error",
        install_addon_error=None,
        install_addon_calls=1,
        set_addon_options_error=SupervisorError("Boom"),
        set_addon_options_calls=1,
        start_addon_error=None,
        start_addon_calls=0,
        error_log="Failed to set the Test app options: Boom",
    ),
    test.case(
        "start_error",
        install_addon_error=None,
        install_addon_calls=1,
        set_addon_options_error=None,
        set_addon_options_calls=1,
        start_addon_error=SupervisorError("Boom"),
        start_addon_calls=1,
        error_log="Failed to start the Test app: Boom",
    ),
)
async def schedule_install_setup_addon_logs_error(
    install_addon_error: Exception | None,
    install_addon_calls: int,
    set_addon_options_error: Exception | None,
    set_addon_options_calls: int,
    start_addon_error: Exception | None,
    start_addon_calls: int,
    error_log: str,
    addon_manager: AddonManager = Depends(addon_manager),
    _installed: AsyncMock = Depends(addon_installed),
    install_addon: AsyncMock = Depends(install_addon),
    set_addon_options: AsyncMock = Depends(set_addon_options),
    start_addon: AsyncMock = Depends(start_addon),
    caplog=Depends(caplog_fx),
) -> None:
    """Test schedule install setup addon logs error."""
    install_addon.side_effect = install_addon_error
    set_addon_options.side_effect = set_addon_options_error
    start_addon.side_effect = start_addon_error

    await addon_manager.async_schedule_install_setup_addon(
        {"test_key": "test"}, catch_error=True
    )

    expect(error_log in caplog.text).to_be(True)
    expect(install_addon.call_count).to_equal(install_addon_calls)
    expect(set_addon_options.call_count).to_equal(set_addon_options_calls)
    expect(start_addon.call_count).to_equal(start_addon_calls)


@test
async def schedule_setup_addon(
    addon_manager: AddonManager = Depends(addon_manager),
    _installed: AsyncMock = Depends(addon_installed),
    set_addon_options: AsyncMock = Depends(set_addon_options_no_side_effect),
    start_addon: AsyncMock = Depends(start_addon),
) -> None:
    """Test schedule setup addon."""
    start_task = addon_manager.async_schedule_setup_addon({"test_key": "test"})

    expect(addon_manager.task_in_progress()).to_be(True)

    start_task_two = addon_manager.async_schedule_setup_addon({"test_key": "test"})

    await asyncio.gather(start_task, start_task_two)

    expect(addon_manager.task_in_progress()).to_be(False)
    expect(set_addon_options.call_count).to_equal(1)
    expect(start_addon.call_count).to_equal(1)

    set_addon_options.reset_mock()
    start_addon.reset_mock()

    await addon_manager.async_schedule_setup_addon({"test_key": "test"})

    expect(set_addon_options.call_count).to_equal(1)
    expect(start_addon.call_count).to_equal(1)


@test.cases(
    test.case(
        "set_options_error",
        set_addon_options_error=SupervisorError("Boom"),
        set_addon_options_calls=1,
        start_addon_error=None,
        start_addon_calls=0,
        error_message="Failed to set the Test app options: Boom",
    ),
    test.case(
        "start_error",
        set_addon_options_error=None,
        set_addon_options_calls=1,
        start_addon_error=SupervisorError("Boom"),
        start_addon_calls=1,
        error_message="Failed to start the Test app: Boom",
    ),
)
async def schedule_setup_addon_error(
    set_addon_options_error: Exception | None,
    set_addon_options_calls: int,
    start_addon_error: Exception | None,
    start_addon_calls: int,
    error_message: str,
    addon_manager: AddonManager = Depends(addon_manager),
    _installed: AsyncMock = Depends(addon_installed),
    set_addon_options: AsyncMock = Depends(set_addon_options),
    start_addon: AsyncMock = Depends(start_addon),
) -> None:
    """Test schedule setup addon raises error."""
    set_addon_options.side_effect = set_addon_options_error
    start_addon.side_effect = start_addon_error

    async with expect_raises_async(AddonError, match=rf"{error_message}"):
        await addon_manager.async_schedule_setup_addon({"test_key": "test"})

    expect(set_addon_options.call_count).to_equal(set_addon_options_calls)
    expect(start_addon.call_count).to_equal(start_addon_calls)


@test.cases(
    test.case(
        "set_options_error",
        set_addon_options_error=SupervisorError("Boom"),
        set_addon_options_calls=1,
        start_addon_error=None,
        start_addon_calls=0,
        error_log="Failed to set the Test app options: Boom",
    ),
    test.case(
        "start_error",
        set_addon_options_error=None,
        set_addon_options_calls=1,
        start_addon_error=SupervisorError("Boom"),
        start_addon_calls=1,
        error_log="Failed to start the Test app: Boom",
    ),
)
async def schedule_setup_addon_logs_error(
    set_addon_options_error: Exception | None,
    set_addon_options_calls: int,
    start_addon_error: Exception | None,
    start_addon_calls: int,
    error_log: str,
    addon_manager: AddonManager = Depends(addon_manager),
    _installed: AsyncMock = Depends(addon_installed),
    set_addon_options: AsyncMock = Depends(set_addon_options),
    start_addon: AsyncMock = Depends(start_addon),
    caplog=Depends(caplog_fx),
) -> None:
    """Test schedule setup addon logs error."""
    set_addon_options.side_effect = set_addon_options_error
    start_addon.side_effect = start_addon_error

    await addon_manager.async_schedule_setup_addon(
        {"test_key": "test"}, catch_error=True
    )

    expect(error_log in caplog.text).to_be(True)
    expect(set_addon_options.call_count).to_equal(set_addon_options_calls)
    expect(start_addon.call_count).to_equal(start_addon_calls)
