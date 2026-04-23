"""Tryke fixtures for Namecheap DynamicDNS tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.namecheapdns.const import DOMAIN
from homeassistant.const import CONF_DOMAIN, CONF_HOST, CONF_PASSWORD

from tests.common import MockConfigEntry

TEST_HOST = "home"
TEST_DOMAIN = "example.com"
TEST_PASSWORD = "test-password"

TEST_USER_INPUT = {
    CONF_HOST: TEST_HOST,
    CONF_DOMAIN: TEST_DOMAIN,
    CONF_PASSWORD: TEST_PASSWORD,
}


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.namecheapdns.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_namecheap() -> Generator[AsyncMock]:
    """Mock update_namecheapdns."""
    with patch(
        "homeassistant.components.namecheapdns.config_flow.update_namecheapdns",
        return_value=True,
    ) as mock:
        yield mock


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock Namecheap Dynamic DNS configuration entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"{TEST_HOST}.{TEST_DOMAIN}",
        data=TEST_USER_INPUT,
        entry_id="12345",
    )
