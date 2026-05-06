"""Tryke fixtures for Whois integration tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.whois.const import DOMAIN
from homeassistant.const import CONF_DOMAIN
from homeassistant.util import dt as dt_util

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Home Assistant",
        domain=DOMAIN,
        data={
            CONF_DOMAIN: "home-assistant.io",
        },
        unique_id="home-assistant.io",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.whois.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_whois() -> Generator[MagicMock]:
    """Return a mocked query."""
    with (
        patch(
            "homeassistant.components.whois.coordinator.whois_query",
        ) as whois_mock,
        patch("homeassistant.components.whois.config_flow.whois.query", new=whois_mock),
    ):
        domain = whois_mock.return_value
        domain.abuse_contact = "abuse@example.com"
        domain.admin = "admin@example.com"
        domain.creation_date = datetime(2019, 1, 1, 0, 0, 0)
        domain.dnssec = True
        domain.expiration_date = datetime(2023, 1, 1, 0, 0, 0)
        domain.last_updated = datetime(
            2022, 1, 1, 0, 0, 0, tzinfo=dt_util.get_time_zone("Europe/Amsterdam")
        )
        domain.name = "home-assistant.io"
        domain.name_servers = ["ns1.example.com", "ns2.example.com"]
        domain.owner = "owner@example.com"
        domain.registrant = "registrant@example.com"
        domain.registrar = "My Registrar"
        domain.reseller = "Top Domains, Low Prices"
        domain.status = "ok"
        domain.statuses = ["OK"]
        yield whois_mock
