"""Tryke helpers for HA test ports — async raises, zeroconf mocks, etc.

Lives next to ``hass_fixtures`` but kept separate so contributors can grep
for the helper names individually. Import as needed:

    from tests.hass_tryke_helpers import (
        expect_raises_async,
        mock_async_zeroconf,
        requests_mock_session,
    )
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
import re
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import requests_mock as rm_lib
from tryke import fixture


@asynccontextmanager
async def expect_raises_async(
    error_type: type[BaseException],
    *,
    match: str | None = None,
) -> AsyncGenerator[None]:
    """Async equivalent of ``expect(callable).to_raise(...)``.

    Tryke 0.0.27's ``to_raise`` only handles synchronous callables. Use
    this around an inline ``await``::

        async with expect_raises_async(ValueError, match=r"bad"):
            await thing.do_it()
    """
    raised: BaseException | None = None
    try:
        yield
    except BaseException as exc:  # noqa: BLE001
        raised = exc

    if not isinstance(raised, error_type):
        raise AssertionError(
            f"Expected {error_type.__name__} to be raised, "
            f"got {type(raised).__name__ if raised else 'None'}"
        )
    if match is not None and not re.search(match, str(raised)):
        raise AssertionError(f"Expected match {match!r} in {raised!r}")


@fixture
def mock_async_zeroconf() -> Generator[MagicMock]:
    """Patch the async zeroconf instance so flows that consume it don't hit the network.

    pytest-aiohttp / pytest-syrupy adjacent integrations (apple_tv, hue,
    etc.) consume ``async_zeroconf`` at flow init time. Mock the entire
    ``zeroconf.HaAsyncZeroconf`` rather than fight with the real
    implementation.
    """
    with patch(
        "homeassistant.components.zeroconf.async_get_async_instance",
        new=AsyncMock(),
    ) as zc:
        zc.return_value = MagicMock()
        zc.return_value.async_register_service = AsyncMock()
        zc.return_value.async_unregister_service = AsyncMock()
        yield zc


@fixture
def requests_mock_session() -> Generator[rm_lib.Mocker]:
    """Drop-in for the pytest-requests-mock plugin's ``requests_mock`` fixture.

    Wraps ``requests_mock.Mocker()`` (the library context manager) as a
    ``@fixture`` so consumer tests can ``Depends(requests_mock_session)``
    and use it the same way they'd use the pytest plugin's autouse.
    """
    with rm_lib.Mocker() as m:
        yield m


@contextmanager
def patch_requests_mock(*registrations: tuple[str, str, dict[str, Any]]) -> Generator[rm_lib.Mocker]:
    """Inline ``with`` form for one-off requests-mock setups.

    Each ``registrations`` entry is ``(method, url, response_kwargs)``::

        with patch_requests_mock(
            ("GET", "https://example.com/api", {"json": {"ok": True}}),
        ) as m:
            await client.fetch()
    """
    with rm_lib.Mocker() as m:
        for method, url, kwargs in registrations:
            m.register_uri(method, url, **kwargs)
        yield m
