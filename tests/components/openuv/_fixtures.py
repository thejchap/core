"""Tryke fixtures for OpenUV tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
import json
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, fixture

from homeassistant.components.openuv.const import (
    CONF_FROM_WINDOW,
    CONF_TO_WINDOW,
    DOMAIN,
)
from homeassistant.const import (
    CONF_API_KEY,
    CONF_ELEVATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture

TEST_API_KEY = "abcde12345"
TEST_ELEVATION = 0
TEST_LATITUDE = 51.528308
TEST_LONGITUDE = -0.3817765


@fixture
async def set_time_zone(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Set the time zone for the tests."""
    await hass.config.async_set_time_zone("America/Regina")


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.openuv.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def data_protection_window() -> dict[str, Any]:
    """Define a fixture to return UV protection window data."""
    return json.loads(load_fixture("protection_window_data.json", "openuv"))


@fixture
def data_uv_index() -> dict[str, Any]:
    """Define a fixture to return UV index data."""
    return json.loads(load_fixture("uv_index_data.json", "openuv"))


@fixture
def client(
    data_protection_window: dict[str, Any] = Depends(data_protection_window),
    data_uv_index: dict[str, Any] = Depends(data_uv_index),
) -> Mock:
    """Define a mock Client object."""
    return Mock(
        latitude=TEST_LATITUDE,
        longitude=TEST_LONGITUDE,
        uv_index=AsyncMock(return_value=data_uv_index),
        uv_protection_window=AsyncMock(return_value=data_protection_window),
    )


@fixture
def config() -> dict[str, Any]:
    """Define a config entry data fixture."""
    return {
        CONF_API_KEY: TEST_API_KEY,
        CONF_ELEVATION: TEST_ELEVATION,
        CONF_LATITUDE: TEST_LATITUDE,
        CONF_LONGITUDE: TEST_LONGITUDE,
    }


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config),
) -> MockConfigEntry:
    """Define a config entry fixture."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{config[CONF_LATITUDE]}, {config[CONF_LONGITUDE]}",
        data=config,
        options={CONF_FROM_WINDOW: 3.5, CONF_TO_WINDOW: 3.5},
    )
    entry.add_to_hass(hass)
    return entry


@fixture
async def mock_pyopenuv(
    client: Mock = Depends(client),
    _: None = Depends(set_time_zone),
) -> AsyncGenerator[None]:
    """Define a fixture to patch pyopenuv."""
    with (
        patch(
            "homeassistant.components.openuv.config_flow.Client", return_value=client
        ),
        patch("homeassistant.components.openuv.Client", return_value=client),
    ):
        yield


@fixture
async def setup_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
    _mock_pyopenuv: None = Depends(mock_pyopenuv),
) -> None:
    """Define a fixture to set up openuv."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
