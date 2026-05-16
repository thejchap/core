"""Tryke fixtures for auth tests."""

from tryke import Depends, fixture

from tests.hass_fixtures import (
    ClientSessionGenerator,
    aiohttp_client as aiohttp_client_fx,
    current_request_with_host as current_request_with_host_fx,
)


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
