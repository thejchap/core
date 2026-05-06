"""Define Tryke test fixtures for ReCollect Waste."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aiorecollect.client import PickupEvent, PickupType
from tryke import Depends, fixture

from homeassistant.components.recollect_waste.const import (
    CONF_PLACE_ID,
    CONF_SERVICE_ID,
    DOMAIN,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

TEST_PLACE_ID = "12345"
TEST_SERVICE_ID = "67890"


@fixture
def pickup_events() -> list[PickupEvent]:
    """Define a list of pickup events."""
    return [
        PickupEvent(
            date(2022, 1, 23), [PickupType("garbage", "Trash Collection")], "The Sun"
        )
    ]


@fixture
def client(events: list[PickupEvent] = Depends(pickup_events)) -> Mock:
    """Define a fixture to return a mocked aiopurple API object."""
    return Mock(async_get_pickup_events=AsyncMock(return_value=events))


@fixture
def config() -> dict[str, Any]:
    """Define a config entry data fixture."""
    return {
        CONF_PLACE_ID: TEST_PLACE_ID,
        CONF_SERVICE_ID: TEST_SERVICE_ID,
    }


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: dict[str, Any] = Depends(config),
) -> MockConfigEntry:
    """Define a config entry fixture."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{TEST_PLACE_ID}, {TEST_SERVICE_ID}",
        data=cfg,
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def mock_aiorecollect(_c: Mock = Depends(client)) -> Generator[None]:
    """Define a fixture to patch aiorecollect."""
    with (
        patch(
            "homeassistant.components.recollect_waste.coordinator.Client",
            return_value=_c,
        ),
        patch(
            "homeassistant.components.recollect_waste.config_flow.Client",
            return_value=_c,
        ),
    ):
        yield


@fixture
async def setup_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    _rec: None = Depends(mock_aiorecollect),
) -> None:
    """Set up recollect_waste."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
