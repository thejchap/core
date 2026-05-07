"""Tryke fixtures for the nina integration."""

from collections.abc import Generator
from copy import deepcopy
from unittest.mock import AsyncMock, patch

from pynina import Warning
from tryke import Depends, fixture

from homeassistant.components.nina.const import DOMAIN
from homeassistant.core import HomeAssistant

from .const import (
    DUMMY_CONFIG_ENTRY,
    DUMMY_CONFIG_ENTRY_AREA_FILTERS,
    DUMMY_CONFIG_ENTRY_DEFAULT_FILTERS,
)

from tests.common import (
    MockConfigEntry,
    load_json_array_fixture,
    load_json_object_fixture,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.nina.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Provide a common mock config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="NINA",
        data=deepcopy(DUMMY_CONFIG_ENTRY),
        version=1,
        minor_version=3,
    )

    config_entry.add_to_hass(hass)

    return config_entry


@fixture
def nina_region_codes() -> dict[str, str]:
    """Provide region codes."""
    return load_json_object_fixture("regions.json", DOMAIN)


@fixture
def mock_nina_class(
    region_codes: dict[str, str] = Depends(nina_region_codes),
) -> Generator[AsyncMock]:
    """Mock the NINA class."""
    with (
        patch(
            "homeassistant.components.nina.config_flow.Nina", autospec=True
        ) as mock_nina,
        patch("homeassistant.components.nina.coordinator.Nina", new=mock_nina),
    ):
        nina = mock_nina.return_value
        nina.get_all_regional_codes.return_value = region_codes
        yield nina


@fixture
def nina_warnings() -> list[Warning]:
    """Provide sample warnings."""
    raw_data = load_json_array_fixture("warnings.json", DOMAIN)
    return [Warning(**w) for w in raw_data]
