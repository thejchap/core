"""Tryke fixtures for Notion tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
import json
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aionotion.bridge.models import Bridge
from aionotion.listener.models import Listener
from aionotion.sensor.models import Sensor
from aionotion.user.models import UserPreferences
from tryke import Depends, fixture

from homeassistant.components.notion.const import (
    CONF_REFRESH_TOKEN,
    CONF_USER_UUID,
    DOMAIN,
)
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture

TEST_USERNAME = "user@host.com"
TEST_PASSWORD = "password123"
TEST_REFRESH_TOKEN = "abcde12345"
TEST_USER_UUID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.notion.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def data_bridge() -> dict[str, Any]:
    """Define bridge data."""
    return json.loads(load_fixture("bridge_data.json", "notion"))


@fixture
def data_listener() -> dict[str, Any]:
    """Define listener data."""
    return json.loads(load_fixture("listener_data.json", "notion"))


@fixture
def data_sensor() -> dict[str, Any]:
    """Define sensor data."""
    return json.loads(load_fixture("sensor_data.json", "notion"))


@fixture
def data_user_preferences() -> dict[str, Any]:
    """Define user preferences data."""
    return json.loads(load_fixture("user_preferences_data.json", "notion"))


@fixture
def client(
    data_bridge_: dict[str, Any] = Depends(data_bridge),
    data_listener_: dict[str, Any] = Depends(data_listener),
    data_sensor_: dict[str, Any] = Depends(data_sensor),
    data_user_preferences_: dict[str, Any] = Depends(data_user_preferences),
) -> Mock:
    """Define a fixture for an aionotion client."""
    return Mock(
        bridge=Mock(
            async_all=AsyncMock(
                return_value=[
                    Bridge.from_dict(bridge) for bridge in data_bridge_["base_stations"]
                ]
            )
        ),
        listener=Mock(
            async_all=AsyncMock(
                return_value=[
                    Listener.from_dict(listener)
                    for listener in data_listener_["listeners"]
                ]
            )
        ),
        refresh_token=TEST_REFRESH_TOKEN,
        sensor=Mock(
            async_all=AsyncMock(
                return_value=[
                    Sensor.from_dict(sensor) for sensor in data_sensor_["sensors"]
                ]
            )
        ),
        user=Mock(
            async_preferences=AsyncMock(
                return_value=UserPreferences.from_dict(
                    data_user_preferences_["user_preferences"]
                )
            )
        ),
        user_uuid=TEST_USER_UUID,
    )


@fixture
def config() -> dict[str, Any]:
    """Define a config entry data fixture."""
    return {
        CONF_USERNAME: TEST_USERNAME,
        CONF_USER_UUID: TEST_USER_UUID,
        CONF_REFRESH_TOKEN: TEST_REFRESH_TOKEN,
    }


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    config_: dict[str, Any] = Depends(config),
) -> MockConfigEntry:
    """Define a config entry fixture."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=TEST_USERNAME, data=config_)
    entry.add_to_hass(hass)
    return entry


@fixture
async def mock_aionotion(
    client_: Mock = Depends(client),
) -> AsyncGenerator[None]:
    """Define a fixture to patch aionotion."""
    with (
        patch(
            "homeassistant.components.notion.async_get_client_with_credentials",
            AsyncMock(return_value=client_),
        ),
        patch(
            "homeassistant.components.notion.async_get_client_with_refresh_token",
            AsyncMock(return_value=client_),
        ),
        patch(
            "homeassistant.components.notion.config_flow.async_get_client_with_credentials",
            AsyncMock(return_value=client_),
        ),
    ):
        yield
