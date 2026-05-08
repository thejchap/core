"""Tryke fixtures for the Philips JS integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, create_autospec, patch

from haphilipsjs import PhilipsTV
from tryke import Depends, fixture

from homeassistant.components.philips_js.const import DOMAIN

from . import MOCK_CONFIG, MOCK_NAME, MOCK_SERIAL_NO, MOCK_SYSTEM

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Disable component setup."""
    with (
        patch(
            "homeassistant.components.philips_js.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.philips_js.async_unload_entry", return_value=True
        ),
    ):
        yield mock_setup_entry


@fixture
def mock_tv() -> Generator[PhilipsTV]:
    """Disable component actual use."""
    tv = create_autospec(PhilipsTV)
    tv.sources = {}
    tv.channels = {}
    tv.application = None
    tv.applications = {}
    tv.system = MOCK_SYSTEM
    tv.name = MOCK_NAME
    tv.api_version = 1
    tv.api_version_detected = None
    tv.on = True
    tv.notify_change_supported = False
    tv.pairing_type = None
    tv.powerstate = None
    tv.source_id = None
    tv.ambilight_current_configuration = None
    tv.ambilight_styles = {}
    tv.ambilight_cached = {}

    with (
        patch(
            "homeassistant.components.philips_js.config_flow.PhilipsTV", return_value=tv
        ),
        patch("homeassistant.components.philips_js.PhilipsTV", return_value=tv),
    ):
        yield tv


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Get standard player config entry."""
    return MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG, title=MOCK_NAME, unique_id=MOCK_SERIAL_NO
    )
