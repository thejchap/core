"""Tryke fixtures for the cast integration."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pychromecast
from pychromecast.controllers import multizone
from tryke import Depends, fixture


@fixture
def get_multizone_status_mock() -> MagicMock:
    """Mock pychromecast dial."""
    mock = MagicMock(spec_set=pychromecast.dial.get_multizone_status)
    mock.return_value.dynamic_groups = []
    return mock


@fixture
def get_cast_type_mock() -> MagicMock:
    """Mock pychromecast dial."""
    return MagicMock(spec_set=pychromecast.dial.get_cast_type)


@fixture
def castbrowser_mock() -> MagicMock:
    """Mock pychromecast CastBrowser."""
    return MagicMock(spec=pychromecast.discovery.CastBrowser)


@fixture
def mz_mock() -> MagicMock:
    """Mock pychromecast MultizoneManager."""
    return MagicMock(spec_set=multizone.MultizoneManager)


@fixture
def quick_play_mock() -> MagicMock:
    """Mock pychromecast quick_play."""
    return MagicMock()


@fixture
def get_chromecast_mock() -> MagicMock:
    """Mock pychromecast get_chromecast_from_cast_info."""
    return MagicMock()


@fixture
def cast_mock_patches(
    mz: MagicMock = Depends(mz_mock),
    quick_play: MagicMock = Depends(quick_play_mock),
    castbrowser: MagicMock = Depends(castbrowser_mock),
    get_cast_type: MagicMock = Depends(get_cast_type_mock),
    get_chromecast: MagicMock = Depends(get_chromecast_mock),
    get_multizone_status: MagicMock = Depends(get_multizone_status_mock),
) -> Generator[None]:
    """Patch pychromecast for cast tests."""
    ignore_cec_orig = list(pychromecast.IGNORE_CEC)

    with (
        patch(
            "homeassistant.components.cast.discovery.pychromecast.discovery.CastBrowser",
            castbrowser,
        ),
        patch(
            "homeassistant.components.cast.helpers.dial.get_cast_type",
            get_cast_type,
        ),
        patch(
            "homeassistant.components.cast.helpers.dial.get_multizone_status",
            get_multizone_status,
        ),
        patch(
            "homeassistant.components.cast.media_player.MultizoneManager",
            return_value=mz,
        ),
        patch(
            "homeassistant.components.cast.media_player.zeroconf.async_get_instance",
        ),
        patch(
            "homeassistant.components.cast.media_player.quick_play",
            quick_play,
        ),
        patch(
            "homeassistant.components.cast.media_player.pychromecast.get_chromecast_from_cast_info",
            get_chromecast,
        ),
    ):
        yield

    pychromecast.IGNORE_CEC = list(ignore_cec_orig)
