"""Tryke fixtures for ping tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from icmplib import Host
from tryke import fixture


@fixture
def patch_setup() -> Generator[None]:
    """Patch setup methods."""
    with (
        patch(
            "homeassistant.components.ping.async_setup_entry",
            return_value=True,
        ),
        patch("homeassistant.components.ping.async_setup", return_value=True),
    ):
        yield


@fixture
def patch_ping() -> Generator[Host]:
    """Patch icmplib async_ping."""
    mock = Host("10.10.10.10", 5, [10, 1, 2, 5, 6])

    with (
        patch("homeassistant.components.ping.helpers.async_ping", return_value=mock),
        patch("homeassistant.components.ping.async_ping", return_value=mock),
    ):
        yield mock
