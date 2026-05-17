"""Tryke fixtures for Google Pub/Sub component tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, Mock, patch

from tryke import Depends, fixture

from tests.hass_fixtures import mock_network

GOOGLE_PUBSUB_PATH = "homeassistant.components.google_pubsub"


@fixture
def mock_client() -> Generator[MagicMock]:
    """Mock the pubsub client."""
    with patch(f"{GOOGLE_PUBSUB_PATH}.PublisherClient") as client:
        client.from_service_account_json = MagicMock(return_value=MagicMock())
        yield client


@fixture
def mock_is_file() -> Generator[MagicMock]:
    """Mock os.path.isfile."""
    with patch(f"{GOOGLE_PUBSUB_PATH}.os.path.isfile") as is_file:
        is_file.return_value = True
        yield is_file


@fixture
def mock_json() -> Generator[None]:
    """Mock json.dumps."""
    with patch(f"{GOOGLE_PUBSUB_PATH}.json.dumps", Mock(return_value=MagicMock())):
        yield


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _mock_is_file: MagicMock = Depends(mock_is_file),
    _mock_json: None = Depends(mock_json),
) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0
