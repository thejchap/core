"""Tryke fixtures for the NRGkick integration."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

from nrgkick_api import ConnectorType, GridPhases
from tryke import fixture

from homeassistant.components.nrgkick.const import DOMAIN

from tests.common import load_json_object_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.nrgkick.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_nrgkick_api() -> Generator[AsyncMock]:
    """Mock the NRGkick API client and patch it where used."""
    info_data: dict[str, Any] = load_json_object_fixture("info.json", DOMAIN)
    info_data["connector"]["type"] = ConnectorType.TYPE2
    info_data["grid"]["phases"] = GridPhases.L1_L2_L3
    control_data = load_json_object_fixture("control.json", DOMAIN)
    values_data = load_json_object_fixture("values_sensor.json", DOMAIN)

    with (
        patch(
            "homeassistant.components.nrgkick.NRGkickAPI",
            autospec=True,
        ) as mock_api_cls,
        patch(
            "homeassistant.components.nrgkick.config_flow.NRGkickAPI",
            new=mock_api_cls,
        ),
    ):
        api = mock_api_cls.return_value
        api.test_connection.return_value = True
        api.get_info.return_value = info_data
        api.get_control.return_value = control_data
        api.get_values.return_value = values_data
        api.set_current.return_value = 16.0
        api.set_charge_pause.return_value = 0
        api.set_energy_limit.return_value = 0
        api.set_phase_count.return_value = 3
        yield api
