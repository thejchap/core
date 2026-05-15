"""Tryke skip stub (pending port)."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.moat.const import DOMAIN
from homeassistant.components.sensor import ATTR_STATE_CLASS
from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant

from . import MOAT_S2_SERVICE_INFO
from ._fixtures import mock_bluetooth

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import hass as hass_fixture, mock_network

_FAKE_TRANSLATIONS = {
    "component.sensor.entity_component.voltage.name": "Voltage",
    "component.sensor.entity_component.temperature.name": "Temperature",
    "component.sensor.entity_component.humidity.name": "Humidity",
    "component.sensor.entity_component.battery.name": "Battery",
    "component.sensor.entity_component.signal_strength.name": "Signal strength",
}


async def _fake_get_translations(
    hass, language, category, integrations=None, config_flow=None
):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bt: None = Depends(mock_bluetooth),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def sensors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up creates the sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
    )
    entry.add_to_hass(hass)

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
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        expect(len(hass.states.async_all())).to_equal(0)
        inject_bluetooth_service_info(hass, MOAT_S2_SERVICE_INFO)
        await hass.async_block_till_done()
        expect(len(hass.states.async_all())).to_equal(4)

        temp_sensor = hass.states.get("sensor.moat_s2_eeff_voltage")
        temp_sensor_attribtes = temp_sensor.attributes
        expect(temp_sensor.state).to_equal("3.061")
        expect(temp_sensor_attribtes[ATTR_FRIENDLY_NAME]).to_equal(
            "Moat S2 EEFF Voltage"
        )
        expect(temp_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("V")
        expect(temp_sensor_attribtes[ATTR_STATE_CLASS]).to_equal("measurement")

        expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()


_ = (mock_bluetooth,)
