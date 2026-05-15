"""Test the baf init flow."""

from unittest.mock import patch

from aiobafi6.exceptions import DeviceUUIDMismatchError
from tryke import Depends, expect, fixture, test

from homeassistant.components.baf.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import MOCK_UUID, MockBAFDevice

from tests.common import MockConfigEntry
from tests.hass_fixtures import LogCapture, caplog, hass as hass_fixture


def _patch_device_init(side_effect=None):
    """Mock out the BAF Device object."""

    def _create_mock_baf(*args, **kwargs):
        return MockBAFDevice(side_effect)

    return patch("homeassistant.components.baf.Device", _create_mock_baf)


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def config_entry_wrong_uuid(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog_capture: LogCapture = Depends(caplog),
) -> None:
    """Test config entry enters setup retry when uuid mismatches."""
    mismatched_uuid = MOCK_UUID + "0"
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_IP_ADDRESS: "127.0.0.1"}, unique_id=mismatched_uuid
    )
    already_migrated_config_entry.add_to_hass(hass)
    with _patch_device_init(DeviceUUIDMismatchError):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
        await hass.async_block_till_done()
    expect(already_migrated_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
    expect(
        "Unexpected device found at 127.0.0.1; expected 12340, found 1234"
        in caplog_capture.text
    ).to_be(True)
