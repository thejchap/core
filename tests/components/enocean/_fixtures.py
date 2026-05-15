"""Tryke fixtures for EnOcean integration tests."""

from typing import Final

from tryke import fixture

from homeassistant.components.enocean.const import DOMAIN
from homeassistant.const import CONF_DEVICE

from tests.common import MockConfigEntry

ENTRY_CONFIG: Final[dict[str, str]] = {
    CONF_DEVICE: "/dev/ttyUSB0",
}


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="device_chip_id",
        data=ENTRY_CONFIG,
    )
