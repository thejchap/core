"""Common helpers for the teslemetry integration tests."""

from __future__ import annotations

import time
from unittest.mock import patch

from homeassistant.components.teslemetry.const import DOMAIN
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id="abc-123",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_at": int(time.time()) + 3600,
            },
        },
    )


async def setup_platform(
    hass: HomeAssistant,
    platforms: list[Platform] | None = None,
) -> MockConfigEntry:
    """Set up the Teslemetry platform."""
    mock_entry = mock_config_entry()
    mock_entry.add_to_hass(hass)

    if platforms is None:
        await hass.config_entries.async_setup(mock_entry.entry_id)
    else:
        with patch("homeassistant.components.teslemetry.PLATFORMS", platforms):
            await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    return mock_entry


async def reload_platform(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    platforms: list[Platform] | None = None,
) -> None:
    """Reload the Teslemetry platform."""
    if platforms is None:
        await hass.config_entries.async_reload(entry.entry_id)
    else:
        with patch("homeassistant.components.teslemetry.PLATFORMS", platforms):
            await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
