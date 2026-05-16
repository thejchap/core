"""Tryke fixtures for nx584 tests."""

from collections.abc import Generator
from unittest import mock

from nx584 import client as nx584_client
from tryke import Depends, fixture


@fixture
def fake_zones() -> list[dict]:
    """Return fixture for fake zones."""
    return [
        {"name": "front", "number": 1},
        {"name": "back", "number": 2},
        {"name": "inside", "number": 3},
    ]


@fixture
def client(
    fake_zones: list[dict] = Depends(fake_zones),
) -> Generator[mock.MagicMock]:
    """Mock the nx584 client."""
    with mock.patch.object(nx584_client, "Client") as _mock_client:
        c = nx584_client.Client.return_value
        c.list_zones.return_value = fake_zones
        c.get_version.return_value = "1.1"

        yield _mock_client
