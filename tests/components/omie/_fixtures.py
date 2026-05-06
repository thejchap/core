"""Tryke fixtures for the OMIE integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.omie.const import DOMAIN

from . import spot_price_fetcher

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="OMIE",
        domain=DOMAIN,
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.omie.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_pyomie() -> Generator[MagicMock]:
    """Mock pyomie.spot_price with realistic responses."""
    with (
        patch("homeassistant.components.omie.coordinator.pyomie") as mock,
        patch("homeassistant.components.omie.config_flow.pyomie", mock),
    ):
        mock.spot_price.side_effect = spot_price_fetcher({})
        yield mock
