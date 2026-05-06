"""Tryke fixtures for Suez Water tests."""

from collections.abc import Generator
from datetime import date
from unittest.mock import AsyncMock, patch

from pysuez import AggregatedData, PriceResult
from pysuez.const import ATTRIBUTION
from tryke import fixture

from homeassistant.components.suez_water.const import CONF_COUNTER_ID

MOCK_DATA = {
    "username": "test-username",
    "password": "test-password",
    CONF_COUNTER_ID: "123456",
}


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.suez_water.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def suez_client() -> Generator[AsyncMock]:
    """Create mock for suez_water external api."""
    with (
        patch(
            "homeassistant.components.suez_water.coordinator.SuezClient", autospec=True
        ) as mock_client,
        patch(
            "homeassistant.components.suez_water.config_flow.SuezClient",
            new=mock_client,
        ),
    ):
        suez_client = mock_client.return_value
        suez_client.check_credentials.return_value = True

        result = AggregatedData(
            value=160,
            current_month={
                date.fromisoformat("2024-01-01"): 130,
                date.fromisoformat("2024-01-02"): 145,
            },
            previous_month={
                date.fromisoformat("2024-12-01"): 154,
                date.fromisoformat("2024-12-02"): 166,
            },
            current_year=1500,
            previous_year=1000,
            attribution=ATTRIBUTION,
            highest_monthly_consumption=2558,
            history={
                date.fromisoformat("2024-01-01"): 130,
                date.fromisoformat("2024-01-02"): 145,
                date.fromisoformat("2024-12-01"): 154,
                date.fromisoformat("2024-12-02"): 166,
            },
        )

        suez_client.fetch_aggregated_data.return_value = result
        suez_client.get_price.return_value = PriceResult(
            "OK", {"price": 4.74}, "Price is 4.74"
        )
        yield suez_client
