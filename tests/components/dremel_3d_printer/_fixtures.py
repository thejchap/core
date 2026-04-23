"""Tryke fixtures for Dremel 3D Printer."""

from collections.abc import Generator
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import requests_mock
from tryke import Depends, fixture

from homeassistant.components.dremel_3d_printer.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass

HOST = "1.2.3.4"
CONF_DATA = {CONF_HOST: HOST}


def patch_async_setup_entry():
    """Patch the async entry setup of Dremel 3D Printer."""
    return patch(
        "homeassistant.components.dremel_3d_printer.async_setup_entry",
        return_value=True,
    )


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass),
) -> MockConfigEntry:
    """Add config entry in Home Assistant."""
    entry = MockConfigEntry(domain=DOMAIN, data=CONF_DATA, unique_id="123456789")
    entry.add_to_hass(hass)
    return entry


@fixture
def connection() -> Generator[None]:
    """Mock Dremel 3D Printer connection."""
    with requests_mock.Mocker() as mock:
        mock.post(
            f"http://{HOST}/command",
            response_list=[
                {"text": load_fixture("dremel_3d_printer/command_1.json")},
                {"text": load_fixture("dremel_3d_printer/command_2.json")},
                {"text": load_fixture("dremel_3d_printer/command_1.json")},
                {"text": load_fixture("dremel_3d_printer/command_2.json")},
            ],
        )

        mock.post(
            f"https://{HOST}:11134/getHomeMessage",
            text=load_fixture("dremel_3d_printer/get_home_message.json"),
            status_code=HTTPStatus.OK,
        )
        yield


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
