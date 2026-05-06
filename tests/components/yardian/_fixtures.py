"""Tryke fixtures for the Yardian tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.yardian import DOMAIN
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_HOST, CONF_NAME

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.yardian.async_setup_entry", return_value=True
    ) as patched_setup_entry:
        yield patched_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Provide a mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="yid123",
        data={
            CONF_HOST: "1.2.3.4",
            CONF_ACCESS_TOKEN: "abc",
            CONF_NAME: "Yardian",
            "yid": "yid123",
            "model": "PRO1902",
            "serialNumber": "SN1",
        },
        title="Yardian Smart Sprinkler",
    )
