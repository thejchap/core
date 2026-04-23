"""Tryke fixtures for the Orvibo integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

with patch("socket.socket.bind"):
    import orvibo.s20  # noqa: F401

from tryke import fixture

from homeassistant.components.orvibo.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_MAC

from tests.common import MockConfigEntry


@fixture
def mock_s20() -> Generator[MagicMock]:
    """Mock the Orvibo S20 class."""
    with patch("homeassistant.components.orvibo.config_flow.S20") as mock_class:
        yield mock_class


@fixture
def mock_discover() -> Generator[MagicMock]:
    """Mock Orvibo S20 discovery returning multiple devices."""
    with patch("homeassistant.components.orvibo.config_flow.discover") as mock_func:
        mock_func.return_value = {
            "192.168.1.100": {"mac": b"\xac\xcf\x23\x12\x34\x56"},
            "192.168.1.101": {"mac": b"\xac\xcf\x23\x78\x9a\xbc"},
        }
        yield mock_func


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry for an Orvibo S20 switch."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Orvibo (192.168.1.10)",
        data={CONF_HOST: "192.168.1.10", CONF_MAC: "aa:bb:cc:dd:ee:ff"},
        unique_id="aa:bb:cc:dd:ee:ff",
    )


@fixture
def mock_setup_entry() -> Generator[MagicMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.orvibo.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup
