"""Tryke fixtures for Tami4 tests."""

from collections.abc import Generator
from datetime import datetime
from unittest.mock import AsyncMock, patch

from Tami4EdgeAPI.device import Device
from Tami4EdgeAPI.device_metadata import DeviceMetadata
from Tami4EdgeAPI.water_quality import UV, Filter, WaterQuality
from tryke import fixture


@fixture
def mock__get_devices_metadata() -> Generator[None]:
    """Mock _get_devices_metadata which makes a call to the API."""
    device_metadata = DeviceMetadata(
        id=1,
        name="Drink Water",
        connected=True,
        psn="psn",
        type="type",
        device_firmware="v1.1",
    )

    with patch(
        "Tami4EdgeAPI.Tami4EdgeAPI.Tami4EdgeAPI._get_devices_metadata",
        return_value=[device_metadata],
    ):
        yield


@fixture
def mock__get_devices_metadata_no_name() -> Generator[None]:
    """Mock _get_devices_metadata returning no device name."""
    device_metadata = DeviceMetadata(
        id=1,
        name=None,
        connected=True,
        psn="psn",
        type="type",
        device_firmware="v1.1",
    )

    with patch(
        "Tami4EdgeAPI.Tami4EdgeAPI.Tami4EdgeAPI._get_devices_metadata",
        return_value=[device_metadata],
    ):
        yield


@fixture
def mock_get_device() -> Generator[None]:
    """Mock get_device which makes a call to the API."""
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

    device_metadata = DeviceMetadata(
        id=1,
        name="Drink Water",
        connected=True,
        psn="psn",
        type="type",
        device_firmware="v1.1",
    )

    device = Device(
        water_quality=water_quality, device_metadata=device_metadata, drinks=[]
    )

    with patch(
        "Tami4EdgeAPI.Tami4EdgeAPI.Tami4EdgeAPI.get_device",
        return_value=device,
    ):
        yield


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.tami4.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
