"""Tryke fixtures for feedreader."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import Mock, patch

from tryke import Depends, fixture

from homeassistant.components.feedreader.const import DOMAIN

from tests.common import load_fixture_bytes


@fixture
def feed_one_event() -> bytes:
    """Load test feed data for one event."""
    return load_fixture_bytes("feedreader.xml", DOMAIN)


@fixture
def feed_htmlentities() -> bytes:
    """Load test feed data with HTML Entities."""
    return load_fixture_bytes("feedreader9.xml", DOMAIN)


@fixture
def feed_atom_htmlentities() -> bytes:
    """Load test ATOM feed data with HTML Entities."""
    return load_fixture_bytes("feedreader10.xml", DOMAIN)


@fixture
def feedparser(
    feed_one_event: bytes = Depends(feed_one_event),
) -> Generator[Mock]:
    """Patch feedparser library."""
    with patch(
        "homeassistant.components.feedreader.config_flow.feedparser.http.get",
        return_value=feed_one_event,
    ) as fp:
        yield fp


@fixture
def setup_entry() -> Generator[Mock]:
    """Patch async_setup_entry."""
    with patch(
        "homeassistant.components.feedreader.async_setup_entry"
    ) as setup:
        yield setup
