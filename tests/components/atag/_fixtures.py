"""Tryke fixtures for Atag tests."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.atag.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
async def mock_pyatag_sleep() -> AsyncGenerator[None]:
    """Mock out pyatag sleeps."""
    asyncio_sleep = asyncio.sleep

    async def sleep(duration, loop=None):
        await asyncio_sleep(0)

    with patch("pyatag.gateway.asyncio.sleep", new=sleep):
        yield
