"""Tryke fixtures for The Things Network tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture
from ttn_client import TTNSensorValue

from homeassistant.components.thethingsnetwork.const import (
    CONF_APP_ID,
    DOMAIN,
    TTN_API_HOST,
)
from homeassistant.const import CONF_API_KEY, CONF_HOST

from tests.common import MockConfigEntry

HOST = "example.com"
APP_ID = "my_app"
API_KEY = "my_api_key"

DEVICE_ID = "my_device"
DEVICE_ID_2 = "my_device_2"
DEVICE_FIELD = "a_field"
DEVICE_FIELD_2 = "a_field_2"
DEVICE_FIELD_VALUE = 42

DATA = {
    DEVICE_ID: {
        DEVICE_FIELD: TTNSensorValue(
            {
                "end_device_ids": {"device_id": DEVICE_ID},
                "received_at": "2024-03-11T08:49:11.153738893Z",
            },
            DEVICE_FIELD,
            DEVICE_FIELD_VALUE,
        )
    }
}


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=APP_ID,
        title=APP_ID,
        data={
            CONF_APP_ID: APP_ID,
            CONF_HOST: TTN_API_HOST,
            CONF_API_KEY: API_KEY,
        },
    )


@fixture
def mock_ttnclient() -> Generator[MagicMock]:
    """Mock TTNClient."""

    with (
        patch(
            "homeassistant.components.thethingsnetwork.coordinator.TTNClient",
            autospec=True,
        ) as ttn_client,
        patch(
            "homeassistant.components.thethingsnetwork.config_flow.TTNClient",
            new=ttn_client,
        ),
    ):
        instance = ttn_client.return_value
        instance.fetch_data = AsyncMock(return_value=DATA)
        yield ttn_client
