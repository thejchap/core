"""Tryke fixtures for the Aquacell integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from aioaquacell import AquacellApi, Softener
from tryke import fixture

from tests.common import load_json_array_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.aquacell.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_aquacell_api() -> Generator[MagicMock]:
    """Build a fixture for the Aquacell API."""
    with (
        patch(
            "homeassistant.components.aquacell.AquacellApi",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.aquacell.config_flow.AquacellApi",
            new=mock_client,
        ),
    ):
        mock_aquacell_api: AquacellApi = mock_client.return_value
        mock_aquacell_api.authenticate.return_value = "refresh-token"

        softeners_dict = load_json_array_fixture(
            "aquacell/get_all_softeners_one_softener.json"
        )

        softeners = [Softener.from_dict(softener) for softener in softeners_dict]
        mock_aquacell_api.get_all_softeners.return_value = softeners

        yield mock_aquacell_api
