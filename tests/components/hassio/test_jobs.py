"""Test supervisor jobs manager."""

from collections.abc import Generator
from datetime import datetime
import os
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from aiohasupervisor.models import Job, JobsInfo
from tryke import Depends, expect, fixture, test

from homeassistant.components.hassio.const import MAIN_COORDINATOR
from homeassistant.components.hassio.coordinator import HassioMainDataUpdateCoordinator
from homeassistant.components.hassio.jobs import JobSubscription
from homeassistant.core import HomeAssistant, callback
from homeassistant.setup import async_setup_component

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
    store_info,
    supervisor_client,
    supervisor_info,
    supervisor_root_info,
    supervisor_stats,
)

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)

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
def all_setup_requests(
    addon_installed: AsyncMock = Depends(addon_installed),
    _store_info: AsyncMock = Depends(store_info),
    _addon_changelog: AsyncMock = Depends(addon_changelog),
    _addon_stats: AsyncMock = Depends(addon_stats),
    _jobs_info: AsyncMock = Depends(jobs_info),
    _host_info: AsyncMock = Depends(host_info),
    _supervisor_root_info: AsyncMock = Depends(supervisor_root_info),
    _homeassistant_info: AsyncMock = Depends(homeassistant_info),
    _supervisor_info: AsyncMock = Depends(supervisor_info),
    addons_list: AsyncMock = Depends(addons_list),
    _network_info: AsyncMock = Depends(network_info),
    _os_info: AsyncMock = Depends(os_info),
    _homeassistant_stats: AsyncMock = Depends(homeassistant_stats),
    _supervisor_stats: AsyncMock = Depends(supervisor_stats),
    _ingress_panels: AsyncMock = Depends(ingress_panels),
) -> None:
    """Mock all setup requests (default: without addons)."""
    addons_list.return_value = []
    addon_installed.return_value.update_available = False
    addon_installed.return_value.version = "1.0.0"
    addon_installed.return_value.version_latest = "1.0.0"
    addon_installed.return_value.repository = "core"
    addon_installed.return_value.icon = False


@fixture
def hass_supervisor_ws_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fx),
):
    """Return a websocket client authenticated as the Supervisor user."""
    from homeassistant.components.hassio.const import DATA_CONFIG_STORE  # noqa: PLC0415

    async def create_client():
        hassio_user_id = hass.data[DATA_CONFIG_STORE].data.hassio_user
        hassio_user = await hass.auth.async_get_user(hassio_user_id)
        assert hassio_user
        assert hassio_user.refresh_tokens
        refresh_token = next(iter(hassio_user.refresh_tokens.values()))
        access_token = hass.auth.async_create_access_token(refresh_token)
        return await hass_ws_client(hass, access_token=access_token)

    return create_client


@test
async def job_manager_setup(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: None = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    jobs_info: AsyncMock = Depends(jobs_info),
) -> None:
    """Test setup of job manager."""
    jobs_info.return_value = JobsInfo(
        ignore_conditions=[],
        jobs=[
            Job(
                name="test_job",
                reference=None,
                uuid=uuid4(),
                progress=0,
                stage=None,
                done=False,
                errors=[],
                created=datetime.now(),
                extra=None,
                child_jobs=[
                    Job(
                        name="test_inner_job",
                        reference=None,
                        uuid=uuid4(),
                        progress=0,
                        stage=None,
                        done=False,
                        errors=[],
                        created=datetime.now(),
                        extra=None,
                        child_jobs=[],
                    )
                ],
            )
        ],
    )

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()
    jobs_info.assert_called_once()

    data_coordinator: HassioMainDataUpdateCoordinator = hass.data[MAIN_COORDINATOR]
    expect(len(data_coordinator.jobs.current_jobs)).to_equal(2)
    expect(data_coordinator.jobs.current_jobs[0].name).to_equal("test_job")
    expect(data_coordinator.jobs.current_jobs[1].name).to_equal("test_inner_job")


@test
async def disconnect_on_config_entry_reload(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: None = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    jobs_info: AsyncMock = Depends(jobs_info),
) -> None:
    """Test dispatcher subscription disconnects on config entry reload."""
    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()
    jobs_info.assert_called_once()

    jobs_info.reset_mock()
    data_coordinator: HassioMainDataUpdateCoordinator = hass.data[MAIN_COORDINATOR]
    await hass.config_entries.async_reload(data_coordinator.entry_id)
    await hass.async_block_till_done()
    jobs_info.assert_called_once()


@test
async def job_manager_ws_updates(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: None = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    jobs_info: AsyncMock = Depends(jobs_info),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test job updates sync from Supervisor WS messages."""
    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()
    jobs_info.assert_called_once()

    jobs_info.reset_mock()
    client = await hass_supervisor_ws_client()
    data_coordinator: HassioMainDataUpdateCoordinator = hass.data[MAIN_COORDINATOR]
    expect(data_coordinator.jobs.current_jobs).to_be_falsy()

    # Make an example listener
    job_data: Job | None = None

    @callback
    def mock_subcription_callback(job: Job) -> None:
        nonlocal job_data
        job_data = job

    subscription = JobSubscription(
        mock_subcription_callback, name="test_job", reference="test"
    )
    unsubscribe = data_coordinator.jobs.subscribe(subscription)

    # Send start of job update
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "name": "test_job",
                    "reference": "test",
                    "uuid": (uuid := uuid4().hex),
                    "progress": 0,
                    "stage": None,
                    "done": False,
                    "errors": [],
                    "created": (created := datetime.now().isoformat()),
                    "extra": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(job_data.name).to_equal("test_job")
    expect(job_data.reference).to_equal("test")
    expect(job_data.progress).to_equal(0)
    expect(job_data.done).to_be(False)
    # One job in the cache
    expect(len(data_coordinator.jobs.current_jobs)).to_equal(1)

    # Example progress update
    await client.send_json(
        {
            "id": 2,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "name": "test_job",
                    "reference": "test",
                    "uuid": uuid,
                    "progress": 50,
                    "stage": None,
                    "done": False,
                    "errors": [],
                    "created": created,
                    "extra": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(job_data.name).to_equal("test_job")
    expect(job_data.reference).to_equal("test")
    expect(job_data.progress).to_equal(50)
    expect(job_data.done).to_be(False)
    # Same job, same number of jobs in cache
    expect(len(data_coordinator.jobs.current_jobs)).to_equal(1)

    # Unrelated job update - name change, subscriber should not receive
    await client.send_json(
        {
            "id": 3,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "name": "bad_job",
                    "reference": "test",
                    "uuid": uuid4().hex,
                    "progress": 0,
                    "stage": None,
                    "done": False,
                    "errors": [],
                    "created": created,
                    "extra": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(job_data.name).to_equal("test_job")
    expect(job_data.reference).to_equal("test")
    # New job, cache increases
    expect(len(data_coordinator.jobs.current_jobs)).to_equal(2)

    # Unrelated job update - reference change, subscriber should not receive
    await client.send_json(
        {
            "id": 4,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "name": "test_job",
                    "reference": "bad",
                    "uuid": uuid4().hex,
                    "progress": 0,
                    "stage": None,
                    "done": False,
                    "errors": [],
                    "created": created,
                    "extra": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(job_data.name).to_equal("test_job")
    expect(job_data.reference).to_equal("test")
    # New job, cache increases
    expect(len(data_coordinator.jobs.current_jobs)).to_equal(3)

    # Unsubscribe mock listener, should not receive final update
    unsubscribe()
    await client.send_json(
        {
            "id": 5,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "name": "test_job",
                    "reference": "test",
                    "uuid": uuid,
                    "progress": 100,
                    "stage": None,
                    "done": True,
                    "errors": [],
                    "created": created,
                    "extra": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    await hass.async_block_till_done()

    expect(job_data.name).to_equal("test_job")
    expect(job_data.reference).to_equal("test")
    expect(job_data.progress).to_equal(50)
    expect(job_data.done).to_be(False)
    # Job ended, cache decreases
    expect(len(data_coordinator.jobs.current_jobs)).to_equal(2)

    # REST API should not be used during this sequence
    jobs_info.assert_not_called()


@test
async def job_manager_reload_on_supervisor_restart(
    _env: None = Depends(fixture_supervisor_environ),
    _setup: None = Depends(all_setup_requests),
    hass: HomeAssistant = Depends(hass_fixture),
    jobs_info: AsyncMock = Depends(jobs_info),
    hass_supervisor_ws_client=Depends(hass_supervisor_ws_client),
) -> None:
    """Test job manager reloads cache on supervisor restart."""
    jobs_info.return_value = JobsInfo(
        ignore_conditions=[],
        jobs=[
            Job(
                name="test_job",
                reference="test",
                uuid=uuid4(),
                progress=0,
                stage=None,
                done=False,
                errors=[],
                created=datetime.now(),
                extra=None,
                child_jobs=[],
            )
        ],
    )

    result = await async_setup_component(hass, "hassio", {})
    expect(result).to_be_truthy()
    jobs_info.assert_called_once()

    data_coordinator: HassioMainDataUpdateCoordinator = hass.data[MAIN_COORDINATOR]
    expect(len(data_coordinator.jobs.current_jobs)).to_equal(1)
    expect(data_coordinator.jobs.current_jobs[0].name).to_equal("test_job")

    jobs_info.reset_mock()
    jobs_info.return_value = JobsInfo(ignore_conditions=[], jobs=[])
    client = await hass_supervisor_ws_client()

    # Make an example listener
    job_data: Job | None = None

    @callback
    def mock_subcription_callback(job: Job) -> None:
        nonlocal job_data
        job_data = job

    subscription = JobSubscription(mock_subcription_callback, name="test_job")
    data_coordinator.jobs.subscribe(subscription)

    # Send supervisor restart signal
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
    await hass.async_block_till_done()

    # Listener should be told job is done and cache cleared out
    jobs_info.assert_called_once()
    expect(job_data.name).to_equal("test_job")
    expect(job_data.reference).to_equal("test")
    expect(job_data.done).to_be(True)
    expect(data_coordinator.jobs.current_jobs).to_be_falsy()
