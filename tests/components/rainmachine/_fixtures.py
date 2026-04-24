"""Tryke fixtures for the RainMachine integration tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
import json
from typing import Any
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.rainmachine import DOMAIN
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, CONF_PORT, CONF_SSL
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture

CONTROLLER_MAC = "aa:bb:cc:dd:ee:ff"


@fixture
def data_api_versions() -> dict[str, Any]:
    """Define API version data."""
    return json.loads(load_fixture("api_versions_data.json", "rainmachine"))


@fixture
def data_diagnostics_current() -> dict[str, Any]:
    """Define current diagnostics data."""
    return json.loads(load_fixture("diagnostics_current_data.json", "rainmachine"))


@fixture
def data_machine_firmware_update_status() -> dict[str, Any]:
    """Define machine firmware update status data."""
    return json.loads(
        load_fixture("machine_firmware_update_status_data.json", "rainmachine")
    )


@fixture
def data_programs() -> dict[int, dict[str, Any]]:
    """Define program data."""
    raw_data = json.loads(load_fixture("programs_data.json", "rainmachine"))
    return {program["uid"]: program for program in raw_data}


@fixture
def data_provision_settings() -> dict[str, Any]:
    """Define provisioning settings data."""
    return json.loads(load_fixture("provision_settings_data.json", "rainmachine"))


@fixture
def data_restrictions_current() -> dict[str, Any]:
    """Define current restrictions settings data."""
    return json.loads(load_fixture("restrictions_current_data.json", "rainmachine"))


@fixture
def data_restrictions_universal() -> dict[str, Any]:
    """Define universal restrictions settings data."""
    return json.loads(load_fixture("restrictions_universal_data.json", "rainmachine"))


@fixture
def data_zones() -> dict[int, dict[str, Any]]:
    """Define zone data."""
    raw_data = json.loads(load_fixture("zones_data.json", "rainmachine"))
    zone_details = json.loads(load_fixture("zones_details.json", "rainmachine"))
    zones: dict[int, dict[str, Any]] = {}
    for zone in raw_data:
        [extra] = [z for z in zone_details if z["uid"] == zone["uid"]]
        zones[zone["uid"]] = {**zone, **extra}
    return zones


@fixture
def controller(
    api_versions: dict[str, Any] = Depends(data_api_versions),
    diagnostics_current: dict[str, Any] = Depends(data_diagnostics_current),
    firmware_update: dict[str, Any] = Depends(data_machine_firmware_update_status),
    programs: dict[int, dict[str, Any]] = Depends(data_programs),
    provision_settings: dict[str, Any] = Depends(data_provision_settings),
    restrictions_current: dict[str, Any] = Depends(data_restrictions_current),
    restrictions_universal: dict[str, Any] = Depends(data_restrictions_universal),
    zones: dict[int, dict[str, Any]] = Depends(data_zones),
) -> AsyncMock:
    """Define a regenmaschine controller."""
    ctrl = AsyncMock()
    ctrl.api_version = "4.5.0"
    ctrl.hardware_version = "3"
    ctrl.name = "12345"
    ctrl.mac = CONTROLLER_MAC
    ctrl.software_version = "4.0.925"
    ctrl.api.versions.return_value = api_versions
    ctrl.diagnostics.current.return_value = diagnostics_current
    ctrl.machine.get_firmware_update_status.return_value = firmware_update
    ctrl.programs.all.return_value = programs
    ctrl.provisioning.settings.return_value = provision_settings
    ctrl.restrictions.current.return_value = restrictions_current
    ctrl.restrictions.universal.return_value = restrictions_universal
    ctrl.zones.all.return_value = zones
    return ctrl


@fixture
def client(ctrl: AsyncMock = Depends(controller)) -> AsyncMock:
    """Define a regenmaschine client."""
    return AsyncMock(load_local=AsyncMock(), controllers={CONTROLLER_MAC: ctrl})


@fixture
def config() -> dict[str, Any]:
    """Define a config entry data fixture."""
    return {
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_PASSWORD: "password",
        CONF_PORT: 8080,
        CONF_SSL: True,
    }


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: dict[str, Any] = Depends(config),
) -> MockConfigEntry:
    """Define a config entry fixture."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=CONTROLLER_MAC,
        data=cfg,
        entry_id="81bd010ed0a63b705f6da8407cb26d4b",
    )
    entry.add_to_hass(hass)
    return entry


@fixture
async def setup_rainmachine(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(client),
    cfg: dict[str, Any] = Depends(config),
) -> AsyncGenerator[None]:
    """Define a fixture to set up RainMachine."""
    with (
        patch("homeassistant.components.rainmachine.Client", return_value=_client),
        patch(
            "homeassistant.components.rainmachine.config_flow.Client",
            return_value=_client,
        ),
        patch("homeassistant.components.rainmachine.PLATFORMS", []),
    ):
        assert await async_setup_component(hass, DOMAIN, cfg)
        await hass.async_block_till_done()
        yield
