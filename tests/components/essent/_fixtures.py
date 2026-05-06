"""Tryke fixtures for the Essent integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from essent_dynamic_pricing import EssentPrices
from tryke import fixture

from homeassistant.components.essent.const import DOMAIN

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Essent",
        data={},
        unique_id=DOMAIN,
        entry_id="test_entry_id",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.essent.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


@fixture
def mock_essent_client() -> Generator[AsyncMock]:
    """Mock EssentClient."""
    with (
        patch(
            "homeassistant.components.essent.coordinator.EssentClient",
            autospec=True,
        ) as mock_client_class,
        patch(
            "homeassistant.components.essent.config_flow.EssentClient",
            new=mock_client_class,
        ),
    ):
        client = mock_client_class.return_value
        client.async_get_prices.return_value = EssentPrices.from_dict(
            load_json_object_fixture("prices.json", DOMAIN)
        )
        yield client
