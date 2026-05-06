"""Tryke fixtures for Blue Current tests."""

from tryke import fixture

from homeassistant.components.blue_current.const import DOMAIN

from tests.common import MockConfigEntry


@fixture
def config_entry() -> MockConfigEntry:
    """Define a config entry fixture."""
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="uuid",
        unique_id="1234",
        data={"api_token": "123"},
    )
