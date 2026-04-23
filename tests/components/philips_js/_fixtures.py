"""Tryke fixtures for Philips JS tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, create_autospec, patch

from haphilipsjs import PhilipsTV
from tryke import Depends, fixture

from . import MOCK_NAME, MOCK_PASSWORD, MOCK_SYSTEM, MOCK_SYSTEM_UNPAIRED, MOCK_USERNAME


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Disable component setup."""
    with (
        patch(
            "homeassistant.components.philips_js.async_setup_entry", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.philips_js.async_unload_entry", return_value=True
        ),
    ):
        yield mock_setup


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
def mock_tv_pairable(tv: PhilipsTV = Depends(mock_tv)) -> PhilipsTV:
    """Return a mock TV that is pairable."""
    tv.system = MOCK_SYSTEM_UNPAIRED
    tv.pairing_type = "digest_auth_pairing"
    tv.api_version = 6
    tv.api_version_detected = 6
    tv.secured_transport = True
    tv.name = MOCK_NAME

    tv.pairRequest.return_value = {}
    tv.pairGrant.return_value = MOCK_USERNAME, MOCK_PASSWORD
    return tv
