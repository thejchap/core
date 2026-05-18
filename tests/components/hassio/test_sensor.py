"""The tests for the hassio sensors."""

from dataclasses import replace
from datetime import timedelta
import os
from unittest.mock import AsyncMock, Mock, patch

from aiohasupervisor import SupervisorError
from aiohasupervisor.models import AddonState, InstalledAddonComplete, StoreInfo
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.hassio import DOMAIN
from homeassistant.components.hassio.const import (
    HASSIO_STATS_UPDATE_INTERVAL,
    REQUEST_REFRESH_DELAY,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, translation
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import (
    addon_changelog,
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
    supervisor_root_info,
    supervisor_stats,
)
from .common import MOCK_REPOSITORIES, MOCK_STORE_ADDONS

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    caplog as caplog_fx,
    entity_registry as entity_registry_fx,
    freezer as freezer_fx,
    hass as hass_fixture,
    mock_network,
)

MOCK_ENVIRON = {"SUPERVISOR": "127.0.0.1", "SUPERVISOR_TOKEN": "abcdefgh"}


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_all(
    addon_installed: AsyncMock = Depends(addon_installed),
    _store_info: AsyncMock = Depends(store_info),
    _addon_changelog: AsyncMock = Depends(addon_changelog),
    _addon_stats: AsyncMock = Depends(addon_stats),
    _resolution_info: AsyncMock = Depends(resolution_info),
    _jobs_info: AsyncMock = Depends(jobs_info),
    host_info: AsyncMock = Depends(host_info),
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
    """Mock all setup requests."""
    host_info.return_value = replace(host_info.return_value, agent_version="1.0.0")
    addons_list.return_value[1] = replace(
        addons_list.return_value[1], version_latest="3.2.0", update_available=True
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
            addon.version_latest = "3.2.0"
            addon.update_available = True
            addon.state = AddonState.STOPPED
            addon.url = "https://github.com"
            addon.auto_update = False

        return addon

    addon_installed.side_effect = mock_addon_info


@test.cases(
    test.case(
        "os_version",
        entity_id="sensor.home_assistant_operating_system_version",
        expected="1.0.0",
    ),
    test.case(
        "os_newest_version",
        entity_id="sensor.home_assistant_operating_system_newest_version",
        expected="1.0.0",
    ),
    test.case(
        "host_os_agent_version",
        entity_id="sensor.home_assistant_host_os_agent_version",
        expected="1.0.0",
    ),
    test.case(
        "core_cpu",
        entity_id="sensor.home_assistant_core_cpu_percent",
        expected="0.99",
    ),
    test.case(
        "supervisor_cpu",
        entity_id="sensor.home_assistant_supervisor_cpu_percent",
        expected="0.99",
    ),
    test.case("test_version", entity_id="sensor.test_version", expected="2.0.0"),
    test.case(
        "test_newest_version",
        entity_id="sensor.test_newest_version",
        expected="2.0.1",
    ),
    test.case("test2_version", entity_id="sensor.test2_version", expected="3.1.0"),
    test.case(
        "test2_newest_version",
        entity_id="sensor.test2_newest_version",
        expected="3.2.0",
    ),
    test.case(
        "test_cpu_percent", entity_id="sensor.test_cpu_percent", expected="0.99"
    ),
    test.case(
        "test2_cpu_percent",
        entity_id="sensor.test2_cpu_percent",
        expected="unavailable",
    ),
    test.case(
        "test_memory_percent",
        entity_id="sensor.test_memory_percent",
        expected="4.59",
    ),
    test.case(
        "test2_memory_percent",
        entity_id="sensor.test2_memory_percent",
        expected="unavailable",
    ),
)
async def sensor(
    entity_id: str,
    expected: str,
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    _mock_all: None = Depends(mock_all),
) -> None:
    """Test hassio OS and addons sensor."""
    supervisor_client.store.info.return_value = StoreInfo(
        addons=MOCK_STORE_ADDONS, repositories=MOCK_REPOSITORIES
    )

    # Pre-load hassio translations so entity_ids resolve via translation_key.
    await translation.async_load_integrations(hass, {"hassio"})

    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        expect(result).to_be_truthy()
    await hass.async_block_till_done()

    # Verify that the entity is disabled by default.
    expect(hass.states.get(entity_id)).to_be_none()

    # Enable the entity.
    entity_registry.async_update_entity(entity_id, disabled_by=None)
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # There is a REQUEST_REFRESH_DELAYs cooldown on the debouncer
    async_fire_time_changed(
        hass, dt_util.now() + timedelta(seconds=REQUEST_REFRESH_DELAY)
    )
    await hass.async_block_till_done()

    # Verify that the entity have the expected state.
    state = hass.states.get(entity_id)
    expect(state.state).to_equal(expected)


@test.cases(
    test.case(
        "cpu_percent", entity_id="sensor.test_cpu_percent", expected="0.99"
    ),
    test.case(
        "memory_percent", entity_id="sensor.test_memory_percent", expected="4.59"
    ),
)
async def stats_addon_sensor(
    entity_id: str,
    expected: str,
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    caplog=Depends(caplog_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    addon_stats: AsyncMock = Depends(addon_stats),
    supervisor_client: AsyncMock = Depends(supervisor_client),
    _mock_all: None = Depends(mock_all),
) -> None:
    """Test stats addons sensor."""
    supervisor_client.store.info.return_value = StoreInfo(
        addons=MOCK_STORE_ADDONS, repositories=MOCK_REPOSITORIES
    )

    # Pre-load hassio translations so entity_ids resolve via translation_key.
    await translation.async_load_integrations(hass, {"hassio"})

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
        ).to_be_truthy()
    await hass.async_block_till_done()

    # Verify that the entity is disabled by default.
    expect(hass.states.get(entity_id)).to_be_none()

    addon_stats.side_effect = SupervisorError
    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    expect("Could not fetch stats" not in caplog.text).to_be_truthy()

    addon_stats.side_effect = None
    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    expect("Could not fetch stats" not in caplog.text).to_be_truthy()

    # Enable the entity and wait for the reload to complete.
    entity_registry.async_update_entity(entity_id, disabled_by=None)
    freezer.tick(config_entries.RELOAD_AFTER_UPDATE_DELAY)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    # Verify the entity is still enabled
    expect(entity_registry.async_get(entity_id).disabled_by).to_be_none()

    # The config entry just reloaded, so we need to wait for the next update
    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    expect(hass.states.get(entity_id) is not None).to_be_truthy()

    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    # Verify that the entity have the expected state.
    state = hass.states.get(entity_id)
    expect(state.state).to_equal(expected)

    addon_stats.side_effect = SupervisorError
    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(entity_id)
    expect(state.state).to_equal(STATE_UNAVAILABLE)
    expect("Could not fetch stats" in caplog.text).to_be_truthy()

    # Disable the entity again and verify stats API calls stop
    addon_stats.side_effect = None
    addon_stats.reset_mock()
    entity_registry.async_update_entity(
        entity_id, disabled_by=er.RegistryEntryDisabler.USER
    )
    freezer.tick(config_entries.RELOAD_AFTER_UPDATE_DELAY)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    # After reload with entity disabled, stats should not be fetched
    addon_stats.reset_mock()
    freezer.tick(HASSIO_STATS_UPDATE_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    addon_stats.assert_not_called()
