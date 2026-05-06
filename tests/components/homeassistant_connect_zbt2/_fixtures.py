"""Tryke fixtures for the Home Assistant Connect ZBT-2 integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from aiohasupervisor import SupervisorClient
from aiohasupervisor.addons import AddonsClient
from aiohasupervisor.backups import BackupsClient
from aiohasupervisor.discovery import DiscoveryClient
from aiohasupervisor.homeassistant import HomeAssistantClient
from aiohasupervisor.host import HostClient
from aiohasupervisor.ingress import IngressClient
from aiohasupervisor.jobs import JobsClient
from aiohasupervisor.models import JobsInfo, MountsInfo
from aiohasupervisor.mounts import MountsClient
from aiohasupervisor.network import NetworkClient
from aiohasupervisor.os import OSClient
from aiohasupervisor.resolution import ResolutionClient
from aiohasupervisor.store import StoreClient
from aiohasupervisor.supervisor import SupervisorManagementClient
from tryke import Depends, fixture

from tests.components.hassio.common import (
    mock_addon_info,
    mock_addon_installed,
    mock_addon_store_info,
    mock_start_addon_side_effect,
)


@fixture
def mock_usb_serial_by_id() -> Generator[MagicMock]:
    """Mock usb serial by id."""
    with patch(
        "homeassistant.components.zha.config_flow.usb.get_serial_by_id"
    ) as mock_usb_serial_by_id:
        mock_usb_serial_by_id.side_effect = lambda x: x
        yield mock_usb_serial_by_id


@fixture
def mock_zha() -> Generator[None]:
    """Mock the zha integration."""
    mock_connect_app = MagicMock()
    mock_connect_app.__aenter__.return_value.backups.backups = [MagicMock()]
    mock_connect_app.__aenter__.return_value.backups.create_backup.return_value = (
        MagicMock()
    )

    with (
        patch(
            "homeassistant.components.zha.radio_manager.ZhaRadioManager.create_zigpy_app",
            return_value=mock_connect_app,
        ),
        patch(
            "homeassistant.components.zha.async_setup_entry",
            return_value=True,
        ),
    ):
        yield


@fixture
def mock_zha_get_last_network_settings() -> Generator[None]:
    """Mock zha.api.async_get_last_network_settings."""
    with patch(
        "homeassistant.components.zha.api.async_get_last_network_settings",
        AsyncMock(return_value=None),
    ):
        yield


@fixture
def mock_usb_path_exists() -> Generator[None]:
    """Mock os.path.exists to allow the Connect ZBT-2 integration to load."""
    with patch(
        "homeassistant.components.homeassistant_connect_zbt2.os.path.exists",
        return_value=True,
    ):
        yield


@fixture
def mock_firmware_update_client() -> Generator[MagicMock]:
    """Mock the FirmwareUpdateClient to avoid network requests."""
    with patch(
        "homeassistant.components.homeassistant_hardware.coordinator.FirmwareUpdateClient",
        autospec=True,
    ) as mock_client:
        mock_client.return_value.async_update_data = AsyncMock(return_value=None)
        yield mock_client


@fixture
def supervisor_client() -> Generator[AsyncMock]:
    """Mock the supervisor client.

    Trimmed-down port of ``tests/components/conftest.py``'s
    ``supervisor_client`` fixture covering the Connect ZBT-2 surface
    area (addons / store / supervisor management).
    """
    supervisor_client = AsyncMock(spec=SupervisorClient)
    supervisor_client.addons = AsyncMock(spec=AddonsClient)
    supervisor_client.backups = AsyncMock(spec=BackupsClient)
    supervisor_client.discovery = AsyncMock(spec=DiscoveryClient)
    supervisor_client.homeassistant = AsyncMock(spec=HomeAssistantClient)
    supervisor_client.host = AsyncMock(spec=HostClient)
    supervisor_client.ingress = AsyncMock(spec=IngressClient)
    supervisor_client.jobs = AsyncMock(spec=JobsClient)
    supervisor_client.jobs.info.return_value = JobsInfo(ignore_conditions=[], jobs=[])
    supervisor_client.mounts = AsyncMock(spec=MountsClient)
    supervisor_client.mounts.info.return_value = MagicMock(
        spec=MountsInfo, default_backup_mount=None, mounts=[]
    )
    supervisor_client.network = AsyncMock(spec=NetworkClient)
    supervisor_client.os = AsyncMock(spec=OSClient)
    supervisor_client.resolution = AsyncMock(spec=ResolutionClient)
    supervisor_client.supervisor = AsyncMock(spec=SupervisorManagementClient)
    supervisor_client.store = AsyncMock(spec=StoreClient)

    with (
        patch(
            "homeassistant.components.hassio.get_supervisor_client",
            return_value=supervisor_client,
        ),
        patch(
            "homeassistant.components.hassio.handler.get_supervisor_client",
            return_value=supervisor_client,
        ),
        patch(
            "homeassistant.components.hassio.addon_manager.get_supervisor_client",
            return_value=supervisor_client,
        ),
        patch(
            "homeassistant.components.hassio.coordinator.get_supervisor_client",
            return_value=supervisor_client,
        ),
    ):
        yield supervisor_client


@fixture
def addon_store_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock Supervisor add-on store info."""
    return mock_addon_store_info(supervisor_client, None)


@fixture
def addon_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock Supervisor add-on info."""
    return mock_addon_info(supervisor_client, None)


@fixture
def addon_installed(
    addon_store_info: AsyncMock = Depends(addon_store_info),
    addon_info: AsyncMock = Depends(addon_info),
) -> AsyncMock:
    """Mock add-on already installed but not running."""
    return mock_addon_installed(addon_store_info, addon_info)


@fixture
def start_addon(
    supervisor_client: AsyncMock = Depends(supervisor_client),
    addon_store_info: AsyncMock = Depends(addon_store_info),
    addon_info: AsyncMock = Depends(addon_info),
) -> AsyncMock:
    """Mock start add-on."""
    side_effect = mock_start_addon_side_effect(addon_store_info, addon_info)
    supervisor_client.addons.start_addon.side_effect = side_effect
    return supervisor_client.addons.start_addon


@fixture
def supervisor() -> Generator[None]:
    """Mock Supervisor."""
    with patch(
        "homeassistant.components.homeassistant_hardware.firmware_config_flow.is_hassio",
        return_value=True,
    ):
        yield


@fixture
def setup_entry() -> Generator[AsyncMock]:
    """Mock entry setup."""
    with patch(
        "homeassistant.components.homeassistant_connect_zbt2.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def autouse_bundle(
    _zha: None = Depends(mock_zha),
    _zha_settings: None = Depends(mock_zha_get_last_network_settings),
    _usb_path: None = Depends(mock_usb_path_exists),
    _firmware: MagicMock = Depends(mock_firmware_update_client),
    _usb_serial: MagicMock = Depends(mock_usb_serial_by_id),
    _setup_entry: AsyncMock = Depends(setup_entry),
) -> None:
    """Bundle all the autouse-equivalent fixtures into one Depends target."""
