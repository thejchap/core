"""Tryke fixtures for qwikswitch tests."""

from tryke import Depends, fixture

from tests.hass_fixtures import mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    """Anchor module-level fixtures."""
    return 0


@fixture
def qs_devices() -> list[dict[str, str]]:
    """Return a set of devices as a response."""
    return [
        {
            "id": "@a00001",
            "name": "Switch 1",
            "type": "rel",
            "val": "OFF",
            "time": "1522777506",
            "rssi": "51%",
        },
        {
            "id": "@a00002",
            "name": "Light 2",
            "type": "rel",
            "val": "ON",
            "time": "1522777507",
            "rssi": "45%",
        },
        {
            "id": "@a00003",
            "name": "Dim 3",
            "type": "dim",
            "val": "280c00",
            "time": "1522777544",
            "rssi": "62%",
        },
    ]
