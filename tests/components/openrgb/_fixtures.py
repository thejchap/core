"""Tryke fixtures for OpenRGB tests."""

from __future__ import annotations

from collections.abc import Generator
import importlib
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.openrgb.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import hass as hass_fixture


def _process_openrgb_dump(dump: Any) -> Any:
    """Reconstruct OpenRGB objects from dump."""
    if isinstance(dump, dict):
        if "__enum__" in dump:
            module_name, class_name = dump["__enum__"].rsplit(".", 1)
            return getattr(importlib.import_module(module_name), class_name)(
                dump["value"]
            )
        return SimpleNamespace(**{k: _process_openrgb_dump(v) for k, v in dump.items()})
    if isinstance(dump, list):
        return [_process_openrgb_dump(item) for item in dump]
    return dump


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Computer",
        data={
            CONF_NAME: "Test Computer",
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 6742,
        },
        entry_id="01J0EXAMPLE0CONFIGENTRY00",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.openrgb.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_openrgb_device() -> MagicMock:
    """Return a mocked OpenRGB device."""
    device_obj = _process_openrgb_dump(
        load_json_object_fixture("device_ene_dram.json", DOMAIN)
    )

    device = MagicMock(spec=device_obj)
    device.configure_mock(**vars(device_obj))

    type(device).data = property(
        lambda self: {attr: getattr(self, attr) for attr in vars(device_obj)}
    )

    device.set_color = MagicMock()
    device.set_mode = MagicMock()

    return device


@fixture
def mock_openrgb_client(
    mock_openrgb_device: MagicMock = Depends(mock_openrgb_device),
) -> Generator[MagicMock]:
    """Return a mocked OpenRGB client."""
    with (
        patch(
            "homeassistant.components.openrgb.coordinator.OpenRGBClient",
            autospec=True,
        ) as client_mock,
        patch(
            "homeassistant.components.openrgb.config_flow.OpenRGBClient",
            new=client_mock,
        ),
        patch(
            "homeassistant.components.openrgb.coordinator.Debouncer",
            return_value=None,
        ),
    ):
        client = client_mock.return_value

        client.protocol_version = 4
        client.devices = [mock_openrgb_device]
        client.profiles = []

        client.update = MagicMock()
        client.connect = MagicMock()
        client.disconnect = MagicMock()
        client.load_profile = MagicMock()

        client.client_class_mock = client_mock

        yield client


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_openrgb_client: MagicMock = Depends(mock_openrgb_client),
) -> MockConfigEntry:
    """Set up the OpenRGB integration for testing."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    return mock_config_entry
