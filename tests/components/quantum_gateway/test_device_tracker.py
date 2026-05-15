"""Tests for the quantum_gateway device tracker."""

from collections.abc import Generator
import os
from unittest.mock import AsyncMock, patch

from requests import RequestException
from tryke import Depends, expect, fixture, test

from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER_DOMAIN
from homeassistant.components.device_tracker import legacy
from homeassistant.const import CONF_PASSWORD, CONF_PLATFORM, STATE_HOME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture, mock_network


async def _setup_platform(hass: HomeAssistant) -> None:
    """Set up the quantum_gateway integration."""
    result = await async_setup_component(
        hass,
        DEVICE_TRACKER_DOMAIN,
        {
            DEVICE_TRACKER_DOMAIN: {
                CONF_PLATFORM: "quantum_gateway",
                CONF_PASSWORD: "fake_password",
            }
        },
    )
    await hass.async_block_till_done()
    assert result


@fixture
def yaml_devices(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[str]:
    """Return path to yaml devices file (legacy device_tracker)."""
    yaml_devices = hass.config.path(legacy.YAML_DEVICES)
    if os.path.isfile(yaml_devices):
        os.remove(yaml_devices)
    yield yaml_devices
    if os.path.isfile(yaml_devices):
        os.remove(yaml_devices)


@fixture
def mock_scanner() -> Generator[AsyncMock]:
    """Mock QuantumGatewayScanner instance."""
    with patch(
        "homeassistant.components.quantum_gateway.device_tracker.QuantumGatewayScanner",
        autospec=True,
    ) as mock_scanner:
        client = mock_scanner.return_value
        client.success_init = True
        client.scan_devices.return_value = ["ff:ff:ff:ff:ff:ff", "ff:ff:ff:ff:ff:fe"]
        client.get_device_name.side_effect = {
            "ff:ff:ff:ff:ff:ff": "",
            "ff:ff:ff:ff:ff:fe": "desktop",
        }.get
        yield mock_scanner


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _yaml: str = Depends(yaml_devices),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def get_scanner(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    scanner: AsyncMock = Depends(mock_scanner),
) -> None:
    """Test creating a quantum gateway scanner."""
    await _setup_platform(hass)

    device_1 = hass.states.get("device_tracker.desktop")
    expect(device_1 is not None).to_be(True)
    expect(device_1.state).to_equal(STATE_HOME)

    device_2 = hass.states.get("device_tracker.ff_ff_ff_ff_ff_ff")
    expect(device_2 is not None).to_be(True)
    expect(device_2.state).to_equal(STATE_HOME)


@test
async def get_scanner_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    scanner: AsyncMock = Depends(mock_scanner),
) -> None:
    """Test failure when creating a quantum gateway scanner."""
    scanner.side_effect = RequestException("Error")
    await _setup_platform(hass)

    expect("quantum_gateway.device_tracker" in hass.config.components).to_be(False)


@test
async def scan_devices_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    scanner: AsyncMock = Depends(mock_scanner),
) -> None:
    """Test failure when scanning devices."""
    scanner.return_value.scan_devices.side_effect = RequestException("Error")
    await _setup_platform(hass)

    expect("quantum_gateway.device_tracker" in hass.config.components).to_be(True)

    device_1 = hass.states.get("device_tracker.desktop")
    expect(device_1 is None).to_be(True)

    device_2 = hass.states.get("device_tracker.ff_ff_ff_ff_ff_ff")
    expect(device_2 is None).to_be(True)
