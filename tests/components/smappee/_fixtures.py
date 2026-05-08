"""Tryke fixtures for the smappee integration."""

from __future__ import annotations

from tryke import fixture

from homeassistant.components.smappee.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF

from tests.common import MockConfigEntry


@fixture
def mock_local_config_entry() -> MockConfigEntry:
    """Return a local-mode mocked config entry (no OAuth)."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={"host": "1.2.3.4"},
        unique_id="smappee1006000212",
        source=SOURCE_ZEROCONF,
    )


@fixture
def mock_cloud_config_entry() -> MockConfigEntry:
    """Return a cloud-mode mocked config entry with OAuth token."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="smappeeCloud",
        source=SOURCE_USER,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "expires_at": 9999999999,
                "token_type": "Bearer",
            },
        },
    )
