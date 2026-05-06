"""Tryke fixtures for yamaha_musiccast tests."""

from collections.abc import Generator
from unittest.mock import patch

from aiomusiccast import MusicCastConnectionException
from tryke import fixture

from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo


@fixture
def silent_ssdp_scanner() -> Generator[None]:
    """Start SSDP component and get Scanner, prevent actual SSDP traffic."""
    with (
        patch("homeassistant.components.ssdp.Scanner._async_start_ssdp_listeners"),
        patch("homeassistant.components.ssdp.Scanner._async_stop_ssdp_listeners"),
        patch("homeassistant.components.ssdp.Scanner.async_scan"),
        patch("homeassistant.components.ssdp.Server._async_start_upnp_servers"),
        patch("homeassistant.components.ssdp.Server._async_stop_upnp_servers"),
    ):
        yield


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.yamaha_musiccast.async_setup_entry", return_value=True
    ):
        yield


@fixture
def mock_get_device_info_valid() -> Generator[None]:
    """Mock getting valid device info from musiccast API."""
    with patch(
        "aiomusiccast.MusicCastDevice.get_device_info",
        return_value={"system_id": "1234567890", "model_name": "MC20"},
    ):
        yield


@fixture
def mock_get_device_info_invalid() -> Generator[None]:
    """Mock getting invalid device info from musiccast API."""
    with patch(
        "aiomusiccast.MusicCastDevice.get_device_info",
        return_value={"type": "no_yamaha"},
    ):
        yield


@fixture
def mock_get_device_info_exception() -> Generator[None]:
    """Mock raising an unexpected Exception."""
    with patch(
        "aiomusiccast.MusicCastDevice.get_device_info",
        side_effect=Exception("mocked error"),
    ):
        yield


@fixture
def mock_get_device_info_mc_exception() -> Generator[None]:
    """Mock raising an unexpected Exception."""
    with patch(
        "aiomusiccast.MusicCastDevice.get_device_info",
        side_effect=MusicCastConnectionException("mocked error"),
    ):
        yield


@fixture
def mock_ssdp_yamaha() -> Generator[None]:
    """Mock that the SSDP detected device is a musiccast device."""
    with patch("aiomusiccast.MusicCastDevice.check_yamaha_ssdp", return_value=True):
        yield


@fixture
def mock_ssdp_no_yamaha() -> Generator[None]:
    """Mock that the SSDP detected device is not a musiccast device."""
    with patch("aiomusiccast.MusicCastDevice.check_yamaha_ssdp", return_value=False):
        yield


@fixture
def mock_valid_discovery_information() -> Generator[None]:
    """Mock that the ssdp scanner returns a useful upnp description."""
    with patch(
        "homeassistant.components.ssdp.async_get_discovery_info_by_st",
        return_value=[
            SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                ssdp_location="http://127.0.0.1:9000/MediaRenderer/desc.xml",
                ssdp_headers={
                    "_host": "127.0.0.1",
                },
                upnp={},
            )
        ],
    ):
        yield


@fixture
def mock_empty_discovery_information() -> Generator[None]:
    """Mock that the ssdp scanner returns no upnp description."""
    with patch(
        "homeassistant.components.ssdp.async_get_discovery_info_by_st", return_value=[]
    ):
        yield
