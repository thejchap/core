"""Test the Sensirion BLE sensors."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensirion_ble.const import DOMAIN
from homeassistant.components.sensor import ATTR_STATE_CLASS
from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant

from .fixtures import CONFIGURED_NAME, CONFIGURED_PREFIX, SENSIRION_SERVICE_INFO

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def sensors(
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the Sensirion BLE sensors."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=SENSIRION_SERVICE_INFO.address)
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    inject_bluetooth_service_info(
        hass,
        SENSIRION_SERVICE_INFO,
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all()) >= 3).to_be(True)

    for sensor, value, unit, state_class in (
        ("carbon_dioxide", "724", "ppm", "measurement"),
        ("humidity", "27.8", "%", "measurement"),
        ("temperature", "20.1", "°C", "measurement"),
    ):
        state = hass.states.get(f"sensor.{CONFIGURED_PREFIX}_{sensor}")
        expect(state is not None).to_be(True)
        expect(state.state).to_equal(value)
        name_lower = state.attributes[ATTR_FRIENDLY_NAME].lower()
        expect(name_lower).to_equal(
            f"{CONFIGURED_NAME} {sensor}".lower().replace("_", " ")
        )
        expect(state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(unit)
        expect(state.attributes[ATTR_STATE_CLASS]).to_equal(state_class)
    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
