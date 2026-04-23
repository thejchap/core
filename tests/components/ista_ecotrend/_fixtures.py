"""Tryke fixtures for ista EcoTrend tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.ista_ecotrend.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from tests.common import MockConfigEntry


@fixture
def ista_config_entry() -> MockConfigEntry:
    """Mock ista EcoTrend configuration entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test-password",
        },
        unique_id="26e93f1a-c828-11ea-87d0-0242ac130003",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ista_ecotrend.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


def get_consumption_data(obj_uuid: str | None = None) -> dict[str, Any]:
    """Mock function get_consumption_data."""
    return {
        "consumptionUnitId": obj_uuid,
        "consumptions": [],
        "costs": [],
    }


@fixture
def mock_ista() -> Generator[MagicMock]:
    """Mock Pyecotrend_ista client."""
    with (
        patch(
            "homeassistant.components.ista_ecotrend.PyEcotrendIsta",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.ista_ecotrend.config_flow.PyEcotrendIsta",
            new=mock_client,
        ),
        patch(
            "homeassistant.components.ista_ecotrend.coordinator.PyEcotrendIsta",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.get_account.return_value = {
            "firstName": "Max",
            "lastName": "Istamann",
            "activeConsumptionUnit": "26e93f1a-c828-11ea-87d0-0242ac130003",
        }
        client.get_consumption_unit_details.return_value = {
            "consumptionUnits": [
                {
                    "id": "26e93f1a-c828-11ea-87d0-0242ac130003",
                    "address": {
                        "street": "Luxemburger Str.",
                        "houseNumber": "1",
                    },
                },
            ]
        }
        client.get_uuids.return_value = [
            "26e93f1a-c828-11ea-87d0-0242ac130003",
        ]
        client.get_consumption_data.side_effect = get_consumption_data

        yield client
