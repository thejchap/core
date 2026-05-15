"""Tryke fixtures for P1 Monitor integration tests."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from p1monitor import Phases, Settings, SmartMeter, WaterMeter
from tryke import Depends, fixture

from homeassistant.components.p1_monitor.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network


_P1_TRANSLATIONS = {
    "component.p1_monitor.entity.sensor.consumption_day.name": "Consumption day",
    "component.p1_monitor.entity.sensor.consumption_total.name": "Consumption total",
    "component.p1_monitor.entity.sensor.current_phase_l1.name": "Current phase L1",
    "component.p1_monitor.entity.sensor.current_phase_l2.name": "Current phase L2",
    "component.p1_monitor.entity.sensor.current_phase_l3.name": "Current phase L3",
    "component.p1_monitor.entity.sensor.energy_consumption_high.name": "Energy consumption - High tariff",
    "component.p1_monitor.entity.sensor.energy_consumption_low.name": "Energy consumption - Low tariff",
    "component.p1_monitor.entity.sensor.energy_consumption_price_high.name": "Energy consumption price - High",
    "component.p1_monitor.entity.sensor.energy_consumption_price_low.name": "Energy consumption price - Low",
    "component.p1_monitor.entity.sensor.energy_production_high.name": "Energy production - High tariff",
    "component.p1_monitor.entity.sensor.energy_production_low.name": "Energy production - Low tariff",
    "component.p1_monitor.entity.sensor.energy_production_price_high.name": "Energy production price - High",
    "component.p1_monitor.entity.sensor.energy_production_price_low.name": "Energy production price - Low",
    "component.p1_monitor.entity.sensor.energy_tariff_period.name": "Energy tariff period",
    "component.p1_monitor.entity.sensor.gas_consumption.name": "Gas consumption",
    "component.p1_monitor.entity.sensor.gas_consumption_price.name": "Gas consumption price",
    "component.p1_monitor.entity.sensor.power_consumed_phase_l1.name": "Power consumed phase L1",
    "component.p1_monitor.entity.sensor.power_consumed_phase_l2.name": "Power consumed phase L2",
    "component.p1_monitor.entity.sensor.power_consumed_phase_l3.name": "Power consumed phase L3",
    "component.p1_monitor.entity.sensor.power_consumption.name": "Power consumption",
    "component.p1_monitor.entity.sensor.power_produced_phase_l1.name": "Power produced phase L1",
    "component.p1_monitor.entity.sensor.power_produced_phase_l2.name": "Power produced phase L2",
    "component.p1_monitor.entity.sensor.power_produced_phase_l3.name": "Power produced phase L3",
    "component.p1_monitor.entity.sensor.power_production.name": "Power production",
    "component.p1_monitor.entity.sensor.pulse_count.name": "Pulse count",
    "component.p1_monitor.entity.sensor.voltage_phase_l1.name": "Voltage phase L1",
    "component.p1_monitor.entity.sensor.voltage_phase_l2.name": "Voltage phase L2",
    "component.p1_monitor.entity.sensor.voltage_phase_l3.name": "Voltage phase L3",
}


async def _fake_get_translations(
    hass, language, category, integrations=None, config_flow=None
):
    return _P1_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _P1_TRANSLATIONS


@fixture
def p1_translations():
    """Inject p1_monitor translations so entity slugs include translation_key names."""
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        yield


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="monitor",
        domain=DOMAIN,
        data={CONF_HOST: "example", CONF_PORT: 80},
        unique_id="unique_thingy",
        version=2,
    )


@fixture
def mock_p1monitor():
    """Return a mocked P1 Monitor client."""
    with patch(
        "homeassistant.components.p1_monitor.coordinator.P1Monitor"
    ) as p1monitor_mock:
        client = p1monitor_mock.return_value
        client.smartmeter = AsyncMock(
            return_value=SmartMeter.from_dict(
                json.loads(load_fixture("p1_monitor/smartmeter.json"))
            )
        )
        client.phases = AsyncMock(
            return_value=Phases.from_dict(
                json.loads(load_fixture("p1_monitor/phases.json"))
            )
        )
        client.settings = AsyncMock(
            return_value=Settings.from_dict(
                json.loads(load_fixture("p1_monitor/settings.json"))
            )
        )
        client.watermeter = AsyncMock(
            return_value=WaterMeter.from_dict(
                json.loads(load_fixture("p1_monitor/watermeter.json"))
            )
        )
        yield client


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    client: MagicMock = Depends(mock_p1monitor),
) -> MockConfigEntry:
    """Set up the P1 Monitor integration for testing."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    return config_entry
