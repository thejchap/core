"""Tryke fixtures for Cloudflare tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import fixture

from . import get_mock_client


@fixture
def cfupdate_flow() -> Generator[MagicMock]:
    """Mock the CloudflareUpdater for easier config flow testing."""
    mock_cfupdate = get_mock_client()
    with patch(
        "homeassistant.components.cloudflare.config_flow.pycfdns.Client",
        return_value=mock_cfupdate,
    ) as mock_api:
        yield mock_api
