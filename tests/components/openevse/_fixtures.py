"""Tryke fixtures for the openevse integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.openevse.const import DOMAIN
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry


@fixture
def mock_charger() -> Generator[MagicMock]:
    """Create a mock OpenEVSE charger."""
    with (
        patch(
            "homeassistant.components.openevse.OpenEVSE",
            autospec=True,
        ) as mock,
        patch(
            "homeassistant.components.openevse.config_flow.OpenEVSE",
            new=mock,
        ),
    ):
        charger = mock.return_value
        charger.update = AsyncMock()
        charger.test_and_get = AsyncMock()
        charger.test_and_get.return_value = {
            "serial": "deadbeeffeed",
            "model": "openevse_wifi_v1",
        }
        charger.ws_start = MagicMock()
        charger.ws_disconnect = AsyncMock()
        charger.websocket = MagicMock()
        charger.callback = None
        charger.status = "Charging"
        yield charger


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.openevse.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def has_serial_number() -> bool:
    """Return a serial number."""
    return True


@fixture
def serial_number(
    has_serial_number: bool = Depends(has_serial_number),
) -> str | None:
    """Return a serial number."""
    if has_serial_number:
        return "deadbeeffeed"
    return None


@fixture
def mock_config_entry(
    serial_number: str | None = Depends(serial_number),
) -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        title="openevse_mock_config",
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100"},
        entry_id="FAKE",
        unique_id=serial_number,
    )
