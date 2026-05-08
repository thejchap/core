"""Tryke fixtures for the toon integration."""

from __future__ import annotations

from tryke import fixture

from homeassistant.components.toon.const import DOMAIN

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
            },
            "agreement_id": "test-agreement-id",
        },
    )
