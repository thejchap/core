"""The tests for Kira sensor platform."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.kira import sensor as kira
from homeassistant.core import HomeAssistant

from tests.common import MockEntityPlatform
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_CONFIG = {kira.DOMAIN: {"sensors": [{"host": "127.0.0.1", "port": 17324}]}}

DISCOVERY_INFO = {"name": "kira", "device": "kira"}

DEVICES = []


def add_entities(devices):
    """Mock add devices."""
    DEVICES.extend(devices)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def kira_sensor_callback(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure Kira sensor properly updates its attributes from callback."""
    DEVICES.clear()
    with patch(
        "homeassistant.components.kira.sensor.KiraReceiver.schedule_update_ha_state"
    ) as mock_schedule_update_ha_state:
        mock_kira = MagicMock()
        hass.data[kira.DOMAIN] = {kira.CONF_SENSOR: {}}
        hass.data[kira.DOMAIN][kira.CONF_SENSOR]["kira"] = mock_kira

        kira.setup_platform(hass, TEST_CONFIG, add_entities, DISCOVERY_INFO)
        expect(len(DEVICES)).to_equal(1)
        sensor = DEVICES[0]
        sensor.hass = hass
        sensor.platform = MockEntityPlatform(hass)

        expect(sensor.name).to_equal("kira")

        sensor.hass = hass

        codeName = "FAKE_CODE"
        deviceName = "FAKE_DEVICE"
        codeTuple = (codeName, deviceName)
        sensor._update_callback(codeTuple)

        mock_schedule_update_ha_state.assert_called()

        expect(sensor.state).to_equal(codeName)
        expect(sensor.extra_state_attributes).to_equal({kira.CONF_DEVICE: deviceName})
