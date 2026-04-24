"""Tryke fixtures for Sanix integration tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

from sanix import (
    ATTR_API_BATTERY,
    ATTR_API_DEVICE_NO,
    ATTR_API_DISTANCE,
    ATTR_API_FILL_PERC,
    ATTR_API_SERVICE_DATE,
    ATTR_API_SSID,
    ATTR_API_STATUS,
    ATTR_API_TIME,
)
from sanix.models import Measurement
from tryke import fixture

from homeassistant.components.sanix.const import CONF_SERIAL_NUMBER, DOMAIN
from homeassistant.const import CONF_TOKEN

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_sanix() -> Generator[MagicMock]:
    """Build a fixture for the Sanix API that connects successfully and returns measurements."""
    fx = load_json_object_fixture("get_measurements.json", DOMAIN)
    with (
        patch(
            "homeassistant.components.sanix.config_flow.Sanix",
            autospec=True,
        ) as mock_sanix_api,
        patch(
            "homeassistant.components.sanix.Sanix",
            new=mock_sanix_api,
        ),
    ):
        mock_sanix_api.return_value.fetch_data.return_value = Measurement(
            battery=fx[ATTR_API_BATTERY],
            device_no=fx[ATTR_API_DEVICE_NO],
            distance=fx[ATTR_API_DISTANCE],
            fill_perc=fx[ATTR_API_FILL_PERC],
            service_date=datetime.strptime(
                fx[ATTR_API_SERVICE_DATE], "%d.%m.%Y"
            ).date(),
            ssid=fx[ATTR_API_SSID],
            status=fx[ATTR_API_STATUS],
            time=datetime.strptime(fx[ATTR_API_TIME], "%d.%m.%Y %H:%M:%S").replace(
                tzinfo=ZoneInfo("Europe/Warsaw")
            ),
        )
        yield mock_sanix_api


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Sanix",
        unique_id="1810088",
        data={CONF_SERIAL_NUMBER: "1234", CONF_TOKEN: "abcd"},
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.sanix.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry
