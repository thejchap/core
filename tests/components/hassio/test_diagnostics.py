"""Test Supervisor diagnostics."""

from dataclasses import replace
from http import HTTPStatus
import os
from typing import cast
from unittest.mock import AsyncMock, Mock, patch

from aiohasupervisor.models import AddonState, InstalledAddonComplete
from tryke import Depends, expect, fixture, test

from homeassistant.components.hassio import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.json import JsonObjectType

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
    supervisor_info,
    supervisor_root_info,
    supervisor_stats,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client as hass_client_fx,
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
    _addon_stats: AsyncMock = Depends(addon_stats),
    _addon_changelog: AsyncMock = Depends(addon_changelog),
    _resolution_info: AsyncMock = Depends(resolution_info),
    _jobs_info: AsyncMock = Depends(jobs_info),
    _host_info: AsyncMock = Depends(host_info),
    _supervisor_root_info: AsyncMock = Depends(supervisor_root_info),
    homeassistant_info: AsyncMock = Depends(homeassistant_info),
    supervisor_info: AsyncMock = Depends(supervisor_info),
    _addons_list: AsyncMock = Depends(addons_list),
    _network_info: AsyncMock = Depends(network_info),
    os_info: AsyncMock = Depends(os_info),
    _homeassistant_stats: AsyncMock = Depends(homeassistant_stats),
    _supervisor_stats: AsyncMock = Depends(supervisor_stats),
    _ingress_panels: AsyncMock = Depends(ingress_panels),
) -> None:
    """Mock all setup requests."""
    homeassistant_info.return_value = replace(
        homeassistant_info.return_value,
        version="1.0.0dev221",
        version_latest="1.0.0dev222",
        update_available=True,
    )
    os_info.return_value = replace(
        os_info.return_value,
        version="1.0.0dev2221",
        version_latest="1.0.0dev2222",
        update_available=True,
    )
    supervisor_info.return_value = replace(
        supervisor_info.return_value,
        version_latest="1.0.1dev222",
        update_available=True,
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
            addon.version_latest = "3.1.0"
            addon.update_available = False
            addon.state = AddonState.STOPPED
            addon.url = "https://github.com"
            addon.auto_update = False

        return addon

    addon_installed.side_effect = mock_addon_info


async def _get_diagnostics_for_config_entry(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    config_entry: MockConfigEntry,
) -> JsonObjectType:
    """Return the diagnostics config entry for the specified domain."""
    expect(await async_setup_component(hass, "diagnostics", {})).to_be_truthy()
    await hass.async_block_till_done()

    client = await hass_client()
    response = await client.get(
        f"/api/diagnostics/config_entry/{config_entry.entry_id}"
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    return cast(JsonObjectType, await response.json())


@test
async def diagnostics(
    _mock_all: None = Depends(mock_all),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fx),
) -> None:
    """Test diagnostic information."""
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

    response = await _get_diagnostics_for_config_entry(hass, hass_client, config_entry)
    diagnostics_data = cast(JsonObjectType, response["data"])

    expect("core" in diagnostics_data["coordinator_data"]).to_equal(True)
    expect("supervisor" in diagnostics_data["coordinator_data"]).to_equal(True)
    expect("os" in diagnostics_data["coordinator_data"]).to_equal(True)
    expect("host" in diagnostics_data["coordinator_data"]).to_equal(True)
    expect("addons" in diagnostics_data["addons_coordinator_data"]).to_equal(True)

    expect(len(diagnostics_data["devices"])).to_equal(6)
