"""The tests for the hassio switch."""

from dataclasses import replace
import os
from unittest.mock import AsyncMock, Mock, patch

from aiohasupervisor.models import AddonState, InstalledAddonComplete, StoreInfo
from tryke import Depends, expect, fixture, test

from homeassistant.components.hassio import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

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

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

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
    supervisor_client: AsyncMock = Depends(supervisor_client),
) -> None:
    """Mock all setup requests."""
    addons_list.return_value[1] = replace(
        addons_list.return_value[1], name="test-two", slug="test-two"
    )
    supervisor_client.store.info.return_value = StoreInfo(
        addons=MOCK_STORE_ADDONS, repositories=MOCK_REPOSITORIES
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
            addon.name = "test-two"
            addon.slug = "test-two"
            addon.version = "3.1.0"
            addon.version_latest = "3.1.0"
            addon.update_available = False
            addon.state = AddonState.STOPPED
            addon.url = "https://github.com"
            addon.auto_update = False

        return addon

    addon_installed.side_effect = mock_addon_info


@fixture
async def setup_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    _entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    _mock_all: None = Depends(mock_all),
) -> MockConfigEntry:
    """Set up the hassio integration and enable entity."""
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

    return config_entry


async def enable_entity(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    config_entry: MockConfigEntry,
    entity_id: str,
) -> None:
    """Enable an entity and reload the config entry."""
    entity_registry.async_update_entity(entity_id, disabled_by=None)
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()


@test.cases(
    test.case(
        "test_on_started",
        entity_id="switch.test",
        expected="on",
        addon_state="started",
    ),
    test.case(
        "test_two_off_stopped",
        entity_id="switch.test_two",
        expected="off",
        addon_state="stopped",
    ),
)
async def switch_state(
    entity_id: str,
    expected: str,
    addon_state: str,
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    addon_installed: AsyncMock = Depends(addon_installed),
    setup_integration: MockConfigEntry = Depends(setup_integration),
) -> None:
    """Test hassio addon switch state."""
    addon_installed.return_value.state = addon_state

    expect(hass.states.get(entity_id)).to_be_none()

    await enable_entity(hass, entity_registry, setup_integration, entity_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(expected)


@test
async def switch_turn_on(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    addon_installed: AsyncMock = Depends(addon_installed),
    setup_integration: MockConfigEntry = Depends(setup_integration),
) -> None:
    """Test turning on addon switch."""
    entity_id = "switch.test_two"
    addon_installed.return_value.state = "stopped"

    aioclient_mock.post(
        "http://127.0.0.1/addons/test-two/start", json={"result": "ok"}
    )

    expect(hass.states.get(entity_id)).to_be_none()

    await enable_entity(hass, entity_registry, setup_integration, entity_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("off")

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id},
        blocking=True,
    )

    expect(aioclient_mock.mock_calls[-1][1].path).to_equal("/addons/test-two/start")
    expect(aioclient_mock.mock_calls[-1][0]).to_equal("POST")


@test
async def switch_turn_off(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    addon_installed: AsyncMock = Depends(addon_installed),
    setup_integration: MockConfigEntry = Depends(setup_integration),
) -> None:
    """Test turning off addon switch."""
    entity_id = "switch.test"
    addon_installed.return_value.state = "started"

    aioclient_mock.post("http://127.0.0.1/addons/test/stop", json={"result": "ok"})

    expect(hass.states.get(entity_id)).to_be_none()

    await enable_entity(hass, entity_registry, setup_integration, entity_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("on")

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_id},
        blocking=True,
    )

    expect(aioclient_mock.mock_calls[-1][1].path).to_equal("/addons/test/stop")
    expect(aioclient_mock.mock_calls[-1][0]).to_equal("POST")
