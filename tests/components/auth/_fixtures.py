"""Tryke fixtures for auth tests."""

import asyncio
from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, fixture

from tests.hass_fixtures import (
    ClientSessionGenerator,
    aiohttp_client as aiohttp_client_fx,
    current_request_with_host as current_request_with_host_fx,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
async def aiohttp_client(
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fx),
) -> ClientSessionGenerator:
    """Return aiohttp_client (sockets are allowed in tryke fixture)."""
    return aiohttp_client


@fixture
def current_request_with_host(
    _request_with_host: None = Depends(current_request_with_host_fx),
) -> None:
    """Re-export current_request_with_host fixture for auth tests."""


@fixture
def mock_session() -> Generator[AiohttpClientMocker]:
    """Mock aiohttp.ClientSession."""
    mocker = AiohttpClientMocker()

    with patch(
        "aiohttp.ClientSession",
        side_effect=lambda *args, **kwargs: mocker.create_session(
            asyncio.get_event_loop()
        ),
    ):
        yield mocker
