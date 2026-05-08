"""Tryke fixtures for the Plugwise integration."""

from collections.abc import Generator
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from munch import Munch
from packaging.version import Version
from tryke import fixture

from homeassistant.components.plugwise.const import DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)

from tests.common import MockConfigEntry, load_fixture


def build_smile(**attrs):
    """Build smile Munch from provided attributes."""
    smile = Munch()
    for k, v in attrs.items():
        setattr(smile, k, v)
    return smile


def _read_json(environment: str, call: str) -> dict[str, Any]:
    """Decode the json data."""
    fixture_data = load_fixture(f"plugwise/{environment}/{call}.json")
    return json.loads(fixture_data)


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.plugwise.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_smile_config_flow() -> Generator[MagicMock]:
    """Return a mocked Smile client."""
    with patch(
        "homeassistant.components.plugwise.config_flow.Smile",
        autospec=True,
    ) as api_mock:
        api = api_mock.return_value
        api.connect.return_value = Version("4.3.2")
        api.smile = build_smile(
            hostname="smile12345",
            model="Test Model",
            model_id="Test Model ID",
            name="Test Smile Name",
            version="4.3.2",
        )
        yield api


@fixture
def mock_smile_adam() -> Generator[MagicMock]:
    """Create a Mock Adam environment for testing exceptions."""
    chosen_env = "m_adam_multiple_devices_per_zone"
    data = _read_json(chosen_env, "data")
    with (
        patch(
            "homeassistant.components.plugwise.coordinator.Smile", autospec=True
        ) as api_mock,
        patch(
            "homeassistant.components.plugwise.config_flow.Smile",
            new=api_mock,
        ),
    ):
        api = api_mock.return_value
        api.async_update.return_value = data
        api.cooling_present = False
        api.connect.return_value = Version("3.0.15")
        api.gateway_id = "fe799307f1624099878210aa0b9f1475"
        api.heater_id = "90986d591dcd426cae3ec3e8111ff730"
        api.reboot = True
        api.smile = build_smile(
            hostname="smile98765",
            model="Gateway",
            model_id="smile_open_therm",
            name="Adam",
            type="thermostat",
            version="3.0.15",
        )
        yield api


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="My Plugwise",
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
            CONF_PASSWORD: "test-password",
            CONF_PORT: 80,
            CONF_USERNAME: "smile",
        },
        unique_id="smile98765",
    )
