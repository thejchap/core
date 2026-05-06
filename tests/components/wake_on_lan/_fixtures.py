"""Tryke fixtures for Wake on Lan tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.wake_on_lan.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_BROADCAST_ADDRESS, CONF_BROADCAST_PORT, CONF_MAC
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry

DEFAULT_MAC = "00:01:02:03:04:05"


@fixture
def mock_send_magic_packet() -> Generator[AsyncMock]:
    """Mock magic packet."""
    with patch("wakeonlan.send_magic_packet") as mock_send:
        yield mock_send


@fixture
def mock_subprocess_call() -> Generator[MagicMock]:
    """Mock subprocess call."""
    with patch("homeassistant.components.wake_on_lan.switch.sp.call") as mock_sp:
        mock_sp.return_value = 1
        yield mock_sp


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock async_setup_entry."""
    with patch(
        "homeassistant.components.wake_on_lan.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


def get_default_config() -> dict[str, Any]:
    """Return the default config."""
    return {
        CONF_MAC: DEFAULT_MAC,
        CONF_BROADCAST_ADDRESS: "255.255.255.255",
        CONF_BROADCAST_PORT: 9,
    }


async def setup_loaded_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Set up a loaded entry for tests."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title=f"Wake on LAN {DEFAULT_MAC}",
        source=SOURCE_USER,
        options=get_default_config(),
        entry_id="1",
    )

    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    return config_entry
