"""Tryke fixtures for Hass.io tests."""

from collections.abc import AsyncGenerator, Generator
import os
import re
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
    JobsInfo,
    LogLevel,
    MountsInfo,
    RootInfo,
    SupervisorState,
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

from homeassistant.components.hassio.const import DATA_CONFIG_STORE
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import SUPERVISOR_TOKEN
from .common import (
    mock_addon_info,
    mock_addon_installed,
    mock_addon_store_info,
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
