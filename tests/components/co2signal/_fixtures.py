"""Tryke fixtures for co2signal."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.co2signal.const import DOMAIN
from homeassistant.const import CONF_API_KEY

from tests.common import MockConfigEntry
from tests.components.co2signal import VALID_RESPONSE


@fixture
def electricity_maps() -> Generator[MagicMock]:
    """Mock the ElectricityMaps client."""
    with (
        patch(
            "homeassistant.components.co2signal.ElectricityMaps",
            autospec=True,
        ) as electricity_maps,
        patch(
            "homeassistant.components.co2signal.config_flow.ElectricityMaps",
            new=electricity_maps,
        ),
    ):
        client = electricity_maps.return_value
        client.carbon_intensity_for_home_assistant.return_value = VALID_RESPONSE
        yield client


@fixture
def config_entry() -> MockConfigEntry:
    """Return a MockConfigEntry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "api_key", "location": ""},
        entry_id="904a74160aa6f335526706bee85dfb83",
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
