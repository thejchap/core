"""Test the air-Q coordinator."""

import logging
from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.airq import AirQCoordinator
from homeassistant.components.airq.const import DOMAIN
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from ._fixtures import mock_airq
from .common import TEST_DEVICE_DATA, TEST_DEVICE_INFO

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)

MOCKED_ENTRY = MockConfigEntry(
    domain=DOMAIN,
    data={
        CONF_IP_ADDRESS: "192.168.0.0",
        CONF_PASSWORD: "password",
    },
    unique_id="123-456",
)

STATUS_WARMUP = {
    "co": "co sensor still in warm up phase; waiting time = 18 s",
    "tvoc": "tvoc sensor still in warm up phase; waiting time = 18 s",
    "so2": "so2 sensor still in warm up phase; waiting time = 17 s",
}


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def logging_in_coordinator_first_update_data(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test that the first AirQCoordinator._async_update_data call logs necessary setup."""
    caplog.set_level(logging.DEBUG)
    coordinator = AirQCoordinator(hass, MOCKED_ENTRY)

    expect("name" not in coordinator.device_info).to_be_truthy()

    await coordinator._async_update_data()

    expect(
        "'name' not found in AirQCoordinator.device_info, fetching from the device"
        in caplog.text
    ).to_be_truthy()
    expect(coordinator.device_info.get("name")).to_equal(TEST_DEVICE_INFO["name"])
    expect(
        f"Updated AirQCoordinator.device_info for 'name' {TEST_DEVICE_INFO['name']}"
        in caplog.text
    ).to_be_truthy()

    expect("Following sensors are still warming up" not in caplog.text).to_be_truthy()


@test
async def logging_in_coordinator_subsequent_update_data(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test that the second AirQCoordinator._async_update_data call has nothing to log."""
    caplog.set_level(logging.DEBUG)
    coordinator = AirQCoordinator(hass, MOCKED_ENTRY)
    coordinator.device_info.update(DeviceInfo(**TEST_DEVICE_INFO))

    await coordinator._async_update_data()
    expect("name" in coordinator.device_info).to_be_truthy()
    expect(
        "'name' not found in AirQCoordinator.device_info, fetching from the device"
        not in caplog.text
    ).to_be_truthy()
    expect(
        f"Updated AirQCoordinator.device_info for 'name' {TEST_DEVICE_INFO['name']}"
        not in caplog.text
    ).to_be_truthy()


@test
async def logging_when_warming_up_sensor_present(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test that warming up sensors are logged."""
    caplog.set_level(logging.DEBUG)
    coordinator = AirQCoordinator(hass, MOCKED_ENTRY)
    mock_airq.get_latest_data.return_value = TEST_DEVICE_DATA | {
        "Status": STATUS_WARMUP
    }
    await coordinator._async_update_data()
    expect(
        f"Following sensors are still warming up: {set(STATUS_WARMUP.keys())}"
        in caplog.text
    ).to_be_truthy()
