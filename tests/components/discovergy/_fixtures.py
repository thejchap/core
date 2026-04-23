"""Tryke fixtures for Discovergy."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from pydiscovergy.models import Reading
from tryke import Depends, fixture

from homeassistant.components.discovergy.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.components.discovergy.const import GET_METERS, LAST_READING, LAST_READING_GAS
from tests.hass_fixtures import hass


def _meter_last_reading(meter_id: str) -> Reading:
    """Side effect function for Discovergy mock."""
    return (
        LAST_READING_GAS
        if meter_id == "d81a652fe0824f9a9d336016587d3b9d"
        else LAST_READING
    )


@fixture
def discovergy() -> Generator[AsyncMock]:
    """Mock the pydiscovergy client."""
    with (
        patch(
            "homeassistant.components.discovergy.Discovergy",
            autospec=True,
        ) as mock_discovergy,
        patch(
            "homeassistant.components.discovergy.config_flow.Discovergy",
            new=mock_discovergy,
        ),
    ):
        mock = mock_discovergy.return_value
        mock.meters.return_value = GET_METERS
        mock.meter_last_reading.side_effect = _meter_last_reading
        yield mock


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass),
) -> MockConfigEntry:
    """Return a MockConfigEntry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="user@example.org",
        unique_id="user@example.org",
        data={CONF_EMAIL: "user@example.org", CONF_PASSWORD: "supersecretpassword"},
    )


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf."""
    from zeroconf import DNSCache  # noqa: PLC0415

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        yield mock_zc
