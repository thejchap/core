"""Tryke fixtures for Ondilo ICO tests."""

from tryke import fixture

from homeassistant.components.ondilo_ico.const import DOMAIN

from tests.common import MockConfigEntry


@fixture
def config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Ondilo ICO",
        data={"auth_implementation": DOMAIN, "token": {"access_token": "fake_token"}},
    )
