"""Tryke fixtures for soundtouch config flow tests."""

from __future__ import annotations

from collections.abc import Generator

from requests_mock import Mocker
from tryke import Depends, fixture

from tests.common import load_fixture

DEVICE_1_ID = "020000000001"
DEVICE_1_IP = "192.168.42.1"
DEVICE_1_URL = f"http://{DEVICE_1_IP}:8090"
DEVICE_1_NAME = "My SoundTouch 1"


@fixture
def device1_info() -> str:
    """Load SoundTouch device 1 info response."""
    return load_fixture("soundtouch/device1_info.xml")


@fixture
def device1_now_playing_standby() -> str:
    """Load SoundTouch device 1 now_playing response."""
    return load_fixture("soundtouch/device1_now_playing_standby.xml")


@fixture
def device1_presets() -> str:
    """Load SoundTouch device 1 presets response."""
    return load_fixture("soundtouch/device1_presets.xml")


@fixture
def device1_volume() -> str:
    """Load SoundTouch device 1 volume response."""
    return load_fixture("soundtouch/device1_volume.xml")


@fixture
def device1_zone_master() -> str:
    """Load SoundTouch device 1 getZone response."""
    return load_fixture("soundtouch/device1_getZone_master.xml")


@fixture
def requests_mocker() -> Generator[Mocker]:
    """Provide a requests_mock.Mocker."""
    with Mocker() as mock:
        yield mock


@fixture
def device1_requests_mock_standby(
    mock: Mocker = Depends(requests_mocker),
    info: str = Depends(device1_info),
    volume: str = Depends(device1_volume),
    presets: str = Depends(device1_presets),
    zone_master: str = Depends(device1_zone_master),
    now_playing: str = Depends(device1_now_playing_standby),
) -> Mocker:
    """Mock SoundTouch device 1 API - standby."""
    mock.get(f"{DEVICE_1_URL}/info", text=info)
    mock.get(f"{DEVICE_1_URL}/volume", text=volume)
    mock.get(f"{DEVICE_1_URL}/presets", text=presets)
    mock.get(f"{DEVICE_1_URL}/getZone", text=zone_master)
    mock.get(f"{DEVICE_1_URL}/now_playing", text=now_playing)
    return mock
