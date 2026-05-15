"""The tests for Kira sensor platform."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.kira import remote as kira
from homeassistant.core import HomeAssistant

from tests.common import MockEntityPlatform
from tests.hass_fixtures import hass as hass_fixture, mock_network

SERVICE_SEND_COMMAND = "send_command"

TEST_CONFIG = {kira.DOMAIN: {"devices": [{"host": "127.0.0.1", "port": 17324}]}}

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
async def service_call(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test Kira's ability to send commands."""
    DEVICES.clear()
    mock_kira = MagicMock()
    hass.data[kira.DOMAIN] = {kira.CONF_REMOTE: {}}
    hass.data[kira.DOMAIN][kira.CONF_REMOTE]["kira"] = mock_kira

    kira.setup_platform(hass, TEST_CONFIG, add_entities, DISCOVERY_INFO)
    expect(len(DEVICES)).to_equal(1)
    remote = DEVICES[0]
    remote.hass = hass
    remote.platform = MockEntityPlatform(hass)

    expect(remote.name).to_equal("kira")

    command = ["FAKE_COMMAND"]
    device = "FAKE_DEVICE"
    commandTuple = (command[0], device)
    remote.send_command(device=device, command=command)

    mock_kira.sendCode.assert_called_with(commandTuple)
