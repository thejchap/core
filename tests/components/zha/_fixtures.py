"""Tryke fixtures for the ZHA integration tests.

Ported from ``tests/components/zha/conftest.py``. Mirrors the zigpy
``ControllerApplication`` mock + autouse plumbing originally provided by
the pytest fixtures.
"""

from collections.abc import Generator
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

from tryke import fixture
import zhaquirks
from zigpy.application import ControllerApplication
import zigpy.backups
from zigpy.backups import BackupManager
import zigpy.types


@fixture
def globally_load_quirks() -> None:
    """Load quirks automatically so ZHA tests run deterministically."""
    zhaquirks.setup()


@fixture
def disable_platform_only() -> Generator[None]:
    """Disable platforms to speed up tests."""
    with patch("homeassistant.components.zha.PLATFORMS", []):
        yield


@fixture
def mock_multipan_platform() -> Generator[None]:
    """Mock the multipan platform."""
    with (
        patch(
            "homeassistant.components.zha.silabs_multiprotocol.async_get_channel",
            return_value=None,
        ),
        patch(
            "homeassistant.components.zha.silabs_multiprotocol.async_using_multipan",
            return_value=False,
        ),
    ):
        yield


@fixture
def speed_up_radio_mgr() -> Generator[None]:
    """Speed up the radio manager connection time by removing delays."""
    with patch("homeassistant.components.zha.radio_manager.CONNECT_DELAY_S", 0.00001):
        yield


@fixture
def mock_app() -> Generator[AsyncMock]:
    """Mock zigpy app interface.

    Direct port of the ``mock_app`` autouse fixture from the dev branch's
    ``test_config_flow.py``. Patches ``zigpy.application.ControllerApplication.new``
    so config-flow probes resolve through this mock instead of touching real
    radio hardware.
    """
    mock_app = create_autospec(ControllerApplication, instance=True)
    mock_app.backups = create_autospec(BackupManager, instance=True)
    mock_app.backups.backups = []
    mock_app.state = MagicMock()
    mock_app.state.network_info.extended_pan_id = zigpy.types.EUI64.convert(
        "AABBCCDDEE000000"
    )
    mock_app.state.network_info.metadata = {
        "ezsp": {
            "can_burn_userdata_custom_eui64": True,
            "can_rewrite_custom_eui64": False,
        }
    }
    mock_app.add_listener = MagicMock()
    mock_app.groups = MagicMock()
    mock_app.devices = MagicMock()

    with patch(
        "zigpy.application.ControllerApplication.new",
        AsyncMock(return_value=mock_app),
    ):
        yield mock_app


def _make_backup_factory():
    """Create a stateful zigpy NetworkBackup factory."""
    state = {"num_calls": 0}

    def inner(*, backup_time_offset: int = 0) -> zigpy.backups.NetworkBackup:
        backup = zigpy.backups.NetworkBackup()
        backup.backup_time += timedelta(seconds=backup_time_offset)
        backup.node_info.ieee = zigpy.types.EUI64.convert(
            f"AABBCCDDEE{state['num_calls']:06X}"
        )
        state["num_calls"] += 1
        return backup

    return inner


@fixture
def make_backup():
    """Zigpy network backup factory that creates unique backups with each call."""
    return _make_backup_factory()


@fixture
def backup() -> zigpy.backups.NetworkBackup:
    """Zigpy network backup with non-default settings."""
    return _make_backup_factory()()
