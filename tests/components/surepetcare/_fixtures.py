"""Tryke fixtures for the Sure Petcare integration."""

from collections.abc import Generator
from unittest.mock import NonCallableMagicMock, patch

from surepy import MESTART_RESOURCE
from tryke import fixture

from . import MOCK_API_DATA


async def _mock_call(method: str, resource: str) -> dict | None:
    if method == "GET" and resource == MESTART_RESOURCE:
        return {"data": MOCK_API_DATA}
    return None


@fixture
def surepetcare() -> Generator[NonCallableMagicMock]:
    """Mock the SurePetcare for easier testing."""
    with patch("surepy.SureAPIClient", autospec=True) as mock_client_class:
        client = mock_client_class.return_value
        client.resources = {}
        client.call = _mock_call
        client.get_token.return_value = "token"
        yield client
