"""Test hue_ble setup process."""

from unittest.mock import patch

from bleak.backends.device import BLEDevice
from HueBLE import ConnectionError as HueBleConnectionError, HueBleError
from tryke import Depends, expect, fixture, test

from homeassistant.components.hue_ble.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import TEST_DEVICE_MAC, TEST_DEVICE_NAME

from tests.common import MockConfigEntry
from tests.components.bluetooth import generate_ble_device
from tests.hass_fixtures import LogCapture, caplog as caplog_fixture, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test.cases(
    test.case(
        "no_device",
        ble_device=None,
        scanner_count=2,
        connect_result=True,
        poll_state_result=None,
        message="The light was not found.",
    ),
    test.case(
        "no_scanners",
        ble_device=None,
        scanner_count=0,
        connect_result=True,
        poll_state_result=None,
        message="No Bluetooth scanners are available to search for the light.",
    ),
    test.case(
        "error_connect",
        ble_device=generate_ble_device(TEST_DEVICE_MAC, TEST_DEVICE_NAME),
        scanner_count=2,
        connect_result=False,
        poll_state_result=HueBleConnectionError,
        message="Device found but unable to connect.",
    ),
    test.case(
        "error_poll",
        ble_device=generate_ble_device(TEST_DEVICE_MAC, TEST_DEVICE_NAME),
        scanner_count=2,
        connect_result=True,
        poll_state_result=HueBleError,
        message="Device found and connected but unable to poll values from it.",
    ),
)
async def setup_error(
    *,
    ble_device: BLEDevice | None,
    scanner_count: int,
    connect_result: Exception | bool | None,
    poll_state_result: type[Exception] | None,
    message: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that ConfigEntryNotReady is raised if there is an error condition."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="abcd", data={})
    entry.add_to_hass(hass)
    with (
        patch(
            "homeassistant.components.hue_ble.async_ble_device_from_address",
            return_value=ble_device,
        ),
        patch(
            "homeassistant.components.hue_ble.async_scanner_count",
            return_value=scanner_count,
        ),
        patch(
            "homeassistant.components.hue_ble.HueBleLight.connect",
            side_effect=[connect_result],
        ),
        patch(
            "homeassistant.components.hue_ble.HueBleLight.poll_state",
            side_effect=[poll_state_result],
        ),
    ):
        expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
        await hass.async_block_till_done()
        expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
        expect(message in caplog.text).to_be(True)


@test
async def setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the config is loaded if there are no errors."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id="abcd", data={})
    entry.add_to_hass(hass)
    with (
        patch(
            "homeassistant.components.hue_ble.async_ble_device_from_address",
            return_value=generate_ble_device(TEST_DEVICE_MAC, TEST_DEVICE_NAME),
        ),
        patch(
            "homeassistant.components.hue_ble.async_scanner_count",
            return_value=1,
        ),
        patch(
            "homeassistant.components.hue_ble.HueBleLight.connect",
            return_value=None,
        ),
        patch(
            "homeassistant.components.hue_ble.HueBleLight.poll_state",
            return_value=None,
        ),
    ):
        expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
        await hass.async_block_till_done()
        expect(entry.state).to_be(ConfigEntryState.LOADED)
