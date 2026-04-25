"""Tryke fixtures for Kostal Plenticore tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from pykoplenti import ApiClient
from tryke import Depends, fixture

from tests.common import MockConfigEntry


@fixture
def mock_apiclient() -> ApiClient:
    """Return a mocked ApiClient instance."""
    apiclient = MagicMock(spec=ApiClient)
    apiclient.__aenter__.return_value = apiclient
    apiclient.__aexit__ = AsyncMock()
    return apiclient


@fixture
def mock_apiclient_class(
    apiclient: ApiClient = Depends(mock_apiclient),
) -> Generator[type[ApiClient]]:
    """Return a mocked ApiClient class."""
    with patch(
        "homeassistant.components.kostal_plenticore.config_flow.ApiClient",
        autospec=True,
    ) as mock_api_class:
        mock_api_class.return_value = apiclient
        yield mock_api_class


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mocked ConfigEntry for testing."""
    return MockConfigEntry(
        entry_id="2ab8dd92a62787ddfe213a67e09406bd",
        title="scb",
        domain="kostal_plenticore",
        data={"host": "192.168.1.2", "password": "SecretPassword"},
    )
