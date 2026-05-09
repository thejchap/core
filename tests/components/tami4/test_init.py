"""Test the Tami4 component."""

# Tami4EdgeAPI -> pypasser -> pydub reads os.environ["PATH"] at import time
# (scans for ffmpeg/avconv). Sibling tests use
# patch.dict(os.environ, {}, clear=True) and tryke worker reuse means we can
# inherit a PATH-less environ. Set a default before the import.
import os as _os

_os.environ.setdefault("PATH", "/usr/bin:/bin")
del _os

from datetime import datetime
from unittest.mock import patch

from Tami4EdgeAPI import exceptions
from Tami4EdgeAPI.device import Device
from Tami4EdgeAPI.device_metadata import DeviceMetadata
from Tami4EdgeAPI.water_quality import UV, Filter, WaterQuality
from tryke import Depends, expect, fixture, test

from homeassistant.components.tami4.const import CONF_REFRESH_TOKEN, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


async def _create_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Device name",
        data={CONF_REFRESH_TOKEN: "refresh_token"},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _device_metadata() -> DeviceMetadata:
    return DeviceMetadata(
        id=1,
        name="Drink Water",
        connected=True,
        psn="psn",
        type="type",
        device_firmware="v1.1",
    )


def _device() -> Device:
    water_quality = WaterQuality(
        uv=UV(
            upcoming_replacement=int(datetime.now().timestamp()),
            installed=True,
        ),
        filter=Filter(
            upcoming_replacement=int(datetime.now().timestamp()),
            milli_litters_passed=1000,
            installed=True,
        ),
    )
    return Device(
        water_quality=water_quality, device_metadata=_device_metadata(), drinks=[]
    )


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture so tryke resolves Depends() per the migration pattern."""


@test
async def init_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup and that we can create the entry."""
    with (
        patch(
            "Tami4EdgeAPI.Tami4EdgeAPI.Tami4EdgeAPI._get_devices_metadata",
            return_value=[_device_metadata()],
        ),
        patch(
            "Tami4EdgeAPI.Tami4EdgeAPI.Tami4EdgeAPI.get_device",
            return_value=_device(),
        ),
    ):
        entry = await _create_config_entry(hass)
        expect(entry.state).to_be(ConfigEntryState.LOADED)


@test
async def init_with_api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test init with api error."""
    with (
        patch(
            "Tami4EdgeAPI.Tami4EdgeAPI.Tami4EdgeAPI._get_devices_metadata",
            return_value=[_device_metadata()],
        ),
        patch(
            "Tami4EdgeAPI.Tami4EdgeAPI.Tami4EdgeAPI.get_device",
            return_value=_device(),
            side_effect=exceptions.APIRequestFailedException,
        ),
    ):
        entry = await _create_config_entry(hass)
        expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.cases(
    test.case(
        "refresh_token_expired",
        side_effect=exceptions.RefreshTokenExpiredException,
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "token_refresh_failed",
        side_effect=exceptions.TokenRefreshFailedException,
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def init_error_raised(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    side_effect: type[Exception],
    expected_state: ConfigEntryState,
) -> None:
    """Test init when an error is raised."""
    with (
        patch(
            "Tami4EdgeAPI.Tami4EdgeAPI.Tami4EdgeAPI._get_devices_metadata",
            return_value=[_device_metadata()],
            side_effect=side_effect,
        ),
        patch(
            "Tami4EdgeAPI.Tami4EdgeAPI.Tami4EdgeAPI.get_device",
            return_value=_device(),
        ),
    ):
        entry = await _create_config_entry(hass)
        expect(entry.state).to_be(expected_state)


@test
async def load_unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Config entry can be unloaded."""
    with (
        patch(
            "Tami4EdgeAPI.Tami4EdgeAPI.Tami4EdgeAPI._get_devices_metadata",
            return_value=[_device_metadata()],
        ),
        patch(
            "Tami4EdgeAPI.Tami4EdgeAPI.Tami4EdgeAPI.get_device",
            return_value=_device(),
        ),
    ):
        entry = await _create_config_entry(hass)

        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

        expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
