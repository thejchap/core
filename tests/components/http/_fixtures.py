"""Tryke fixtures for the http component tests."""

from collections.abc import Generator
from ipaddress import IPv4Address, IPv4Network
import os
from unittest.mock import AsyncMock, MagicMock, patch

from aiohasupervisor import SupervisorClient
from aiohasupervisor.addons import AddonsClient
from aiohasupervisor.backups import BackupsClient
from aiohasupervisor.discovery import DiscoveryClient
from aiohasupervisor.homeassistant import HomeAssistantClient
from aiohasupervisor.host import HostClient
from aiohasupervisor.ingress import IngressClient
from aiohasupervisor.jobs import JobsClient
from aiohasupervisor.models import (
    AddonStage,
    AddonState,
    DockerNetwork,
    HomeAssistantInfo,
    HomeAssistantStats,
    HostInfo,
    InstalledAddon,
    JobsInfo,
    LogLevel,
    MountsInfo,
    NetworkInfo,
    OSInfo,
    ResolutionInfo,
    StoreInfo,
    SupervisorInfo,
    SupervisorStats,
    UpdateChannel,
)
from aiohasupervisor.mounts import MountsClient
from aiohasupervisor.network import NetworkClient
from aiohasupervisor.os import OSClient
from aiohasupervisor.resolution import ResolutionClient
from aiohasupervisor.store import StoreClient
from aiohasupervisor.supervisor import SupervisorManagementClient
from tryke import Depends, fixture


@fixture
def gethostbyaddr_mock() -> Generator[None]:
    """Mock out I/O on getting host by address."""
    with patch(
        "homeassistant.components.http.ban.gethostbyaddr",
        return_value=("example.com", ["0.0.0.0.in-addr.arpa"], ["0.0.0.0"]),
    ):
        yield


@fixture
def supervisor_client() -> Generator[AsyncMock]:
    """Mock the supervisor client."""
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
            "homeassistant.components.hassio.addon_panel.get_supervisor_client",
            return_value=supervisor_client,
        ),
        patch(
            "homeassistant.components.hassio.backup.get_supervisor_client",
            return_value=supervisor_client,
        ),
        patch(
            "homeassistant.components.hassio.discovery.get_supervisor_client",
            return_value=supervisor_client,
        ),
        patch(
            "homeassistant.components.hassio.coordinator.get_supervisor_client",
            return_value=supervisor_client,
        ),
        patch(
            "homeassistant.components.hassio.issues.get_supervisor_client",
            return_value=supervisor_client,
        ),
        patch(
            "homeassistant.components.hassio.jobs.get_supervisor_client",
            return_value=supervisor_client,
        ),
        patch(
            "homeassistant.components.hassio.repairs.get_supervisor_client",
            return_value=supervisor_client,
        ),
        patch(
            "homeassistant.components.hassio.update_helper.get_supervisor_client",
            return_value=supervisor_client,
        ),
    ):
        yield supervisor_client


@fixture
def supervisor_is_connected(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock supervisor is connected."""
    supervisor_client.supervisor.ping.return_value = None
    return supervisor_client.supervisor.ping


@fixture
def hassio_env(
    supervisor_is_connected: AsyncMock = Depends(supervisor_is_connected),
) -> Generator[None]:
    """Inject hassio env vars."""
    with (
        patch.dict(os.environ, {"SUPERVISOR": "127.0.0.1"}),
        patch.dict(os.environ, {"SUPERVISOR_TOKEN": "123456"}),
    ):
        yield


@fixture
def resolution_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock resolution info from supervisor."""
    supervisor_client.resolution.info.return_value = ResolutionInfo(
        suggestions=[],
        unsupported=[],
        unhealthy=[],
        issues=[],
        checks=[],
    )
    return supervisor_client.resolution.info


@fixture
def os_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock os info API from supervisor."""
    supervisor_client.os.info.return_value = OSInfo(
        version="1.0.0",
        version_latest="1.0.0",
        update_available=False,
        board=None,
        boot=None,
        data_disk=None,
        boot_slots={},
    )
    return supervisor_client.os.info


@fixture
def store_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock store info."""
    supervisor_client.store.info.return_value = StoreInfo(
        addons=[], repositories=[]
    )
    return supervisor_client.store.info


@fixture
def supervisor_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock supervisor info API from supervisor."""
    supervisor_client.supervisor.info.return_value = SupervisorInfo(
        version="1.0.0",
        version_latest="1.0.0",
        update_available=False,
        channel=UpdateChannel.STABLE,
        arch="",
        supported=True,
        healthy=True,
        ip_address=IPv4Address("172.30.32.2"),
        timezone=None,
        logging=LogLevel.INFO,
        debug=False,
        debug_block=False,
        diagnostics=None,
        auto_update=True,
        country=None,
        detect_blocking_io=False,
    )
    return supervisor_client.supervisor.info


@fixture
def homeassistant_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock Home Assistant info API from supervisor."""
    supervisor_client.homeassistant.info.return_value = HomeAssistantInfo(
        version="1.0.0",
        version_latest="1.0.0",
        update_available=False,
        machine=None,
        ip_address=IPv4Address("172.30.32.1"),
        arch=None,
        image="homeassistant",
        boot=True,
        port=8123,
        ssl=False,
        watchdog=True,
        audio_input=None,
        audio_output=None,
        backups_exclude_database=False,
        duplicate_log_file=False,
    )
    return supervisor_client.homeassistant.info


@fixture
def host_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock host info API from supervisor."""
    supervisor_client.host.info.return_value = HostInfo(
        agent_version=None,
        apparmor_version=None,
        chassis="vm",
        virtualization=None,
        cpe=None,
        deployment=None,
        disk_free=1.6,
        disk_total=100.0,
        disk_used=98.4,
        disk_life_time=None,
        features=[],
        hostname=None,
        llmnr_hostname=None,
        kernel="4.19.0-6-amd64",
        operating_system="Debian GNU/Linux 10 (buster)",
        timezone=None,
        dt_utc=None,
        dt_synchronized=None,
        use_ntp=None,
        startup_time=None,
        boot_timestamp=None,
        broadcast_llmnr=None,
        broadcast_mdns=None,
    )
    return supervisor_client.host.info


@fixture
def network_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock network info API from supervisor."""
    supervisor_client.network.info.return_value = NetworkInfo(
        interfaces=[],
        docker=DockerNetwork(
            interface="hassio",
            address=IPv4Network("172.30.32.0/23"),
            gateway=IPv4Address("172.30.32.1"),
            dns=IPv4Address("172.30.32.3"),
        ),
        host_internet=True,
        supervisor_internet=True,
    )
    return supervisor_client.network.info


@fixture
def addons_list(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock addons list API from supervisor."""
    supervisor_client.addons.list.return_value = [
        InstalledAddon(
            detached=False,
            advanced=False,
            available=True,
            build=False,
            description="",
            homeassistant=None,
            icon=False,
            logo=False,
            name="test",
            repository="core",
            slug="test",
            stage=AddonStage.STABLE,
            update_available=True,
            url="https://github.com/home-assistant/addons/test",
            version_latest="2.0.1",
            version="2.0.0",
            state=AddonState.STARTED,
        ),
        InstalledAddon(
            detached=False,
            advanced=False,
            available=True,
            build=False,
            description="",
            homeassistant=None,
            icon=False,
            logo=False,
            name="test2",
            repository="core",
            slug="test2",
            stage=AddonStage.STABLE,
            update_available=False,
            url="https://github.com",
            version_latest="3.1.0",
            version="3.1.0",
            state=AddonState.STOPPED,
        ),
    ]
    return supervisor_client.addons.list


@fixture
def addon_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock Supervisor add-on info."""
    from tests.components.hassio.common import mock_addon_info  # noqa: PLC0415

    return mock_addon_info(supervisor_client, None)


@fixture
def homeassistant_stats(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock Home Assistant stats API from supervisor."""
    supervisor_client.homeassistant.stats.return_value = HomeAssistantStats(
        cpu_percent=0.99,
        memory_usage=182611968,
        memory_limit=3977146368,
        memory_percent=4.59,
        network_rx=362570232,
        network_tx=82374138,
        blk_read=46010945536,
        blk_write=15051526144,
    )
    return supervisor_client.homeassistant.stats


@fixture
def supervisor_stats(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock supervisor stats API from supervisor."""
    supervisor_client.supervisor.stats.return_value = SupervisorStats(
        cpu_percent=0.99,
        memory_usage=182611968,
        memory_limit=3977146368,
        memory_percent=4.59,
        network_rx=362570232,
        network_tx=82374138,
        blk_read=46010945536,
        blk_write=15051526144,
    )
    return supervisor_client.supervisor.stats


@fixture
def ingress_panels(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock ingress panels API from supervisor."""
    supervisor_client.ingress.panels.return_value = {}
    return supervisor_client.ingress.panels


@fixture
def hassio_bundle(
    _hassio_env: None = Depends(hassio_env),
    _resolution_info: AsyncMock = Depends(resolution_info),
    _os_info: AsyncMock = Depends(os_info),
    _store_info: AsyncMock = Depends(store_info),
    _supervisor_info: AsyncMock = Depends(supervisor_info),
    _homeassistant_info: AsyncMock = Depends(homeassistant_info),
    _host_info: AsyncMock = Depends(host_info),
    _network_info: AsyncMock = Depends(network_info),
    _addons_list: AsyncMock = Depends(addons_list),
    _addon_info: AsyncMock = Depends(addon_info),
    _homeassistant_stats: AsyncMock = Depends(homeassistant_stats),
    _supervisor_stats: AsyncMock = Depends(supervisor_stats),
    _ingress_panels: AsyncMock = Depends(ingress_panels),
) -> None:
    """Bundle hassio fixtures used by supervisor IP tests."""
