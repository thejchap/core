"""Tryke fixtures for the hue integration."""

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fx


@fixture
def no_request_delay() -> Generator[None]:
    """Make the request refresh delay 0 for instant tests."""
    with patch("homeassistant.components.hue.const.REQUEST_REFRESH_DELAY", 0):
        yield


@fixture
def mock_bridge_v1(
    hass: HomeAssistant = Depends(hass_fx),
    _delay: None = Depends(no_request_delay),
) -> Mock:
    """Mock a Hue bridge with V1 api."""
    from .conftest import create_mock_bridge

    return create_mock_bridge(hass, api_version=1)
