"""Tryke fixtures for Ridwell integration tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aioridwell.model import EventState, RidwellPickup, RidwellPickupEvent
from tryke import Depends, fixture

from homeassistant.components.ridwell.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

TEST_ACCOUNT_ID = "12345"
TEST_DASHBOARD_URL = "https://www.ridwell.com/users/12345/dashboard"
TEST_PASSWORD = "password"
TEST_USERNAME = "user@email.com"
TEST_USER_ID = "12345"


@fixture
def account() -> Mock:
    """Define a Ridwell account."""
    return Mock(
        account_id=TEST_ACCOUNT_ID,
        address={
            "street1": "123 Main Street",
            "city": "New York",
            "state": "New York",
            "postal_code": "10001",
        },
        async_get_pickup_events=AsyncMock(
            return_value=[
                RidwellPickupEvent(
                    None,
                    "event_123",
                    date(2022, 1, 24),
                    [RidwellPickup("Plastic Film", "offer_123", 1, "product_123", 1)],
                    EventState.INITIALIZED,
                )
            ]
        ),
    )


@fixture
def client(account_: Mock = Depends(account)) -> Mock:
    """Define an aioridwell client."""
    return Mock(
        async_authenticate=AsyncMock(),
        async_get_accounts=AsyncMock(return_value={TEST_ACCOUNT_ID: account_}),
        get_dashboard_url=Mock(return_value=TEST_DASHBOARD_URL),
        user_id=TEST_USER_ID,
    )


@fixture
def config() -> dict[str, Any]:
    """Define a config entry data fixture."""
    return {
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
    }


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    config_: dict[str, Any] = Depends(config),
) -> MockConfigEntry:
    """Define a config entry fixture."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=config_[CONF_USERNAME],
        data=config_,
        entry_id="11554ec901379b9cc8f5a6c1d11ce978",
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def mock_aioridwell(client_: Mock = Depends(client)) -> Generator[None]:
    """Define a fixture to patch aioridwell."""
    with (
        patch(
            "homeassistant.components.ridwell.config_flow.async_get_client",
            return_value=client_,
        ),
        patch(
            "homeassistant.components.ridwell.coordinator.async_get_client",
            return_value=client_,
        ),
    ):
        yield


@fixture
async def setup_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    _mock: None = Depends(mock_aioridwell),
) -> AsyncGenerator[None]:
    """Define a fixture to set up ridwell."""
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield
