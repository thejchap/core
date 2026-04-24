"""Tryke fixtures for Roku integration tests."""

from __future__ import annotations

from collections.abc import Generator
import json
from typing import Any
from unittest.mock import MagicMock, patch

from rokuecp import Device as RokuDevice
from tryke import Depends, fixture

from homeassistant.components.roku.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, async_load_fixture
from tests.hass_fixtures import hass as hass_fixture


def app_icon_url(*args: Any, **kwargs: Any) -> str:
    """Get the URL to the application icon."""
    app_id = args[0]
    return f"http://192.168.1.160:8060/query/icon/{app_id}"


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Roku",
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.160"},
        unique_id="1GU48T017973",
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch("homeassistant.components.roku.async_setup_entry", return_value=True):
        yield


@fixture
async def mock_device(
    hass: HomeAssistant = Depends(hass_fixture),
) -> RokuDevice:
    """Return the mocked roku device (default roku3)."""
    return RokuDevice(
        json.loads(await async_load_fixture(hass, "roku/roku3.json"))
    )


@fixture
async def mock_device_rokutv(
    hass: HomeAssistant = Depends(hass_fixture),
) -> RokuDevice:
    """Return the mocked rokutv-7820x device."""
    return RokuDevice(
        json.loads(await async_load_fixture(hass, "roku/rokutv-7820x.json"))
    )


@fixture
def mock_roku_config_flow(
    device: RokuDevice = Depends(mock_device),
) -> Generator[MagicMock]:
    """Return a mocked Roku client."""
    with patch(
        "homeassistant.components.roku.config_flow.Roku", autospec=True
    ) as roku_mock:
        client = roku_mock.return_value
        client.app_icon_url.side_effect = app_icon_url
        client.update.return_value = device
        yield client


@fixture
def mock_roku_config_flow_rokutv(
    device: RokuDevice = Depends(mock_device_rokutv),
) -> Generator[MagicMock]:
    """Return a mocked Roku config_flow client for rokutv."""
    with patch(
        "homeassistant.components.roku.config_flow.Roku", autospec=True
    ) as roku_mock:
        client = roku_mock.return_value
        client.app_icon_url.side_effect = app_icon_url
        client.update.return_value = device
        yield client
