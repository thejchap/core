"""Tryke fixtures for the Yamaha integration tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import Depends, fixture


def _create_zone_mock(name: str, url: str) -> MagicMock:
    zone = MagicMock()
    zone.ctrl_url = url
    zone.surround_programs = []
    zone.zone = name
    return zone


class FakeYamahaDevice:
    """A fake Yamaha device."""

    def __init__(self, ctrl_url: str, name: str, zones=None) -> None:
        """Initialize the fake Yamaha device."""
        self.ctrl_url = ctrl_url
        self.name = name
        self._zones = zones or []

    def zone_controllers(self):
        """Return controllers for all available zones."""
        return self._zones


@fixture
def main_zone() -> MagicMock:
    """Mock the main zone."""
    return _create_zone_mock("Main zone", "http://main")


@fixture
def device(main_zone: MagicMock = Depends(main_zone)) -> Generator[FakeYamahaDevice]:
    """Mock the yamaha device."""
    fake = FakeYamahaDevice("http://receiver", "Receiver", zones=[main_zone])
    with (
        patch("rxv.RXV", return_value=fake),
        patch("rxv.find", return_value=[fake]),
    ):
        yield fake


@fixture
def device2(main_zone: MagicMock = Depends(main_zone)) -> Generator[FakeYamahaDevice]:
    """Mock a second yamaha device."""
    fake = FakeYamahaDevice(
        "http://127.0.0.1:80/YamahaRemoteControl/ctrl", "Receiver 2", zones=[main_zone]
    )
    with (
        patch("rxv.RXV", return_value=fake),
        patch("rxv.find", return_value=[fake]),
    ):
        yield fake
