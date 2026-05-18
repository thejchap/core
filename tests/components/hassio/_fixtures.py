"""Tryke fixtures for Hass.io tests."""

from collections.abc import AsyncGenerator, Generator
from ipaddress import IPv4Address, IPv4Network
import os
import re
from unittest.mock import AsyncMock, MagicMock, patch

from aiohasupervisor import SupervisorClient, SupervisorNotFoundError
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
    RootInfo,
    StoreInfo,
    SupervisorInfo,
    SupervisorState,
    SupervisorStats,
    UpdateChannel,
)
from aiohasupervisor.mounts import MountsClient
from aiohasupervisor.network import NetworkClient
from aiohasupervisor.os import OSClient
from aiohasupervisor.resolution import ResolutionClient
from aiohasupervisor.store import StoreClient
from aiohasupervisor.supervisor import SupervisorManagementClient
from aiohttp.test_utils import TestClient
from tryke import Depends, fixture

from homeassistant.components.hassio.addon_manager import AddonManager
from homeassistant.components.hassio.const import DATA_CONFIG_STORE
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import SUPERVISOR_TOKEN
from .common import (
    mock_addon_info,
    mock_addon_installed,
    mock_addon_manager,
    mock_addon_not_installed,
    mock_addon_stats,
    mock_addon_store_info,
    mock_install_addon_side_effect,
    mock_set_addon_options_side_effect,
    mock_start_addon_side_effect,
)

from tests.hass_fixtures import (
    ClientSessionGenerator,
    aiohttp_client as aiohttp_client_fx,
    hass as hass_fixture,
    hass_client as hass_client_fx,
    local_auth as local_auth_fx,
)


@fixture
def disable_security_filter() -> Generator[None]:
    """Disable the security filter to ensure the integration is secure."""
    with patch(
        "homeassistant.components.http.security_filter.FILTERS",
        re.compile("not-matching-anything"),
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
        patch(
            "homeassistant.components.hassio.switch.get_supervisor_client",
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
def supervisor_root_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock root info API from supervisor."""
    supervisor_client.info.return_value = RootInfo(
        supervisor="222",
        homeassistant="0.110.0",
        hassos="1.2.3",
        docker="",
        hostname=None,
        operating_system=None,
        features=[],
        machine=None,
        machine_id=None,
        arch="",
        state=SupervisorState.RUNNING,
        supported_arch=[],
        supported=True,
        channel=UpdateChannel.STABLE,
        logging=LogLevel.INFO,
        timezone="Etc/UTC",
    )
    return supervisor_client.info


@fixture
def ingress_panels(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock ingress panels API from supervisor."""
    supervisor_client.ingress.panels.return_value = {}
    return supervisor_client.ingress.panels


@fixture
def hassio_env(
    supervisor_is_connected: AsyncMock = Depends(supervisor_is_connected),
    supervisor_root_info: AsyncMock = Depends(supervisor_root_info),
) -> Generator[None]:
    """Inject hassio env vars."""
    from aiohasupervisor import SupervisorError  # noqa: PLC0415

    supervisor_root_info.side_effect = SupervisorError()
    with (
        patch.dict(os.environ, {"SUPERVISOR": "127.0.0.1"}),
        patch.dict(os.environ, {"SUPERVISOR_TOKEN": SUPERVISOR_TOKEN}),
    ):
        yield


@fixture
async def hassio_stubs(
    _security: None = Depends(disable_security_filter),
    _env: None = Depends(hassio_env),
    hass: HomeAssistant = Depends(hass_fixture),
    _local_auth: object = Depends(local_auth_fx),
    _ingress: AsyncMock = Depends(ingress_panels),
    _supervisor: AsyncMock = Depends(supervisor_client),
) -> AsyncGenerator[None]:
    """Create mock hassio http client setup."""
    with patch(
        "homeassistant.components.hassio.issues.SupervisorIssues.setup",
    ):
        await async_setup_component(hass, "hassio", {})
    yield


@fixture
async def hassio_client(
    _stubs: None = Depends(hassio_stubs),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> TestClient:
    """Return a Hass.io HTTP client."""
    return await hass_client()


@fixture
async def hassio_noauth_client(
    _stubs: None = Depends(hassio_stubs),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> TestClient:
    """Return a Hass.io HTTP client without auth."""
    return await aiohttp_client(hass.http.app)


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
def addon_not_installed(
    addon_store_info: AsyncMock = Depends(addon_store_info),
    addon_info: AsyncMock = Depends(addon_info),
) -> AsyncMock:
    """Mock add-on not installed."""
    addon_info.side_effect = SupervisorNotFoundError
    return mock_addon_not_installed(addon_store_info, addon_info)


@fixture
def addon_manager(
    hass: HomeAssistant = Depends(hass_fixture),
    _supervisor: AsyncMock = Depends(supervisor_client),
) -> AddonManager:
    """Return an AddonManager instance."""
    return mock_addon_manager(hass)


@fixture
def install_addon(
    supervisor_client: AsyncMock = Depends(supervisor_client),
    addon_store_info: AsyncMock = Depends(addon_store_info),
    addon_info: AsyncMock = Depends(addon_info),
) -> AsyncMock:
    """Mock install add-on."""
    supervisor_client.store.install_addon.side_effect = mock_install_addon_side_effect(
        addon_store_info, addon_info
    )
    return supervisor_client.store.install_addon


@fixture
def start_addon(
    supervisor_client: AsyncMock = Depends(supervisor_client),
    addon_store_info: AsyncMock = Depends(addon_store_info),
    addon_info: AsyncMock = Depends(addon_info),
) -> AsyncMock:
    """Mock start add-on."""
    supervisor_client.addons.start_addon.side_effect = mock_start_addon_side_effect(
        addon_store_info, addon_info
    )
    return supervisor_client.addons.start_addon


@fixture
def restart_addon(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock restart add-on."""
    supervisor_client.addons.restart_addon.side_effect = None
    return supervisor_client.addons.restart_addon


@fixture
def stop_addon(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock stop add-on."""
    return supervisor_client.addons.stop_addon


@fixture
def set_addon_options(
    supervisor_client: AsyncMock = Depends(supervisor_client),
    addon_info: AsyncMock = Depends(addon_info),
) -> AsyncMock:
    """Mock set add-on options."""
    supervisor_client.addons.set_addon_options.side_effect = (
        mock_set_addon_options_side_effect(addon_info.return_value.options)
    )
    return supervisor_client.addons.set_addon_options


@fixture
def set_addon_options_no_side_effect(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock set add-on options without applying options to addon_info.

    Mirrors the pytest fixture parametrize override
    ``@pytest.mark.parametrize("set_addon_options_side_effect", [None])``.
    """
    supervisor_client.addons.set_addon_options.side_effect = None
    return supervisor_client.addons.set_addon_options


@fixture
def uninstall_addon(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock uninstall add-on."""
    return supervisor_client.addons.uninstall_addon


@fixture
def create_backup(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock create backup."""
    return supervisor_client.backups.partial_backup


@fixture
def update_addon(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock update add-on."""
    return supervisor_client.store.update_addon


@fixture
def get_addon_discovery_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock get add-on discovery info."""
    supervisor_client.discovery.list.return_value = []
    supervisor_client.discovery.list.side_effect = None
    return supervisor_client.discovery.list


@fixture
def get_discovery_message(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock getting a discovery message by uuid."""
    supervisor_client.discovery.get.side_effect = None
    return supervisor_client.discovery.get


@fixture
async def hassio_client_supervisor(
    _stubs: None = Depends(hassio_stubs),
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> TestClient:
    """Return an HTTP client authenticated as the supervisor user."""
    hassio_user_id = hass.data[DATA_CONFIG_STORE].data.hassio_user
    hassio_user = await hass.auth.async_get_user(hassio_user_id)
    assert hassio_user
    assert hassio_user.refresh_tokens
    refresh_token = next(iter(hassio_user.refresh_tokens.values()))
    access_token = hass.auth.async_create_access_token(refresh_token)
    return await aiohttp_client(
        hass.http.app,
        headers={"Authorization": f"Bearer {access_token}"},
    )


@fixture
def store_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock store info."""
    supervisor_client.store.info.return_value = StoreInfo(addons=[], repositories=[])
    return supervisor_client.store.info


@fixture
def addon_stats(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock addon stats info."""
    return mock_addon_stats(supervisor_client)


@fixture
def addon_changelog(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock addon changelog."""
    supervisor_client.store.addon_changelog.return_value = ""
    return supervisor_client.store.addon_changelog


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
def jobs_info(
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> AsyncMock:
    """Mock jobs info from supervisor."""
    supervisor_client.jobs.info.return_value = JobsInfo(ignore_conditions=[], jobs=[])
    return supervisor_client.jobs.info


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
