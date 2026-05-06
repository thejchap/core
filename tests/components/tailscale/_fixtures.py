"""Tryke fixtures for Tailscale tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tailscale.models import Devices
from tryke import fixture

from homeassistant.components.tailscale.const import CONF_TAILNET, DOMAIN
from homeassistant.const import CONF_API_KEY

from tests.common import MockConfigEntry, load_fixture


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="homeassistant.github",
        domain=DOMAIN,
        data={CONF_TAILNET: "homeassistant.github", CONF_API_KEY: "tskey-MOCK"},
        unique_id="homeassistant.github",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.tailscale.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_tailscale_config_flow() -> Generator[MagicMock]:
    """Return a mocked Tailscale client."""
    with patch(
        "homeassistant.components.tailscale.config_flow.Tailscale", autospec=True
    ) as tailscale_mock:
        tailscale = tailscale_mock.return_value
        tailscale.devices.return_value = Devices.from_json(
            load_fixture("tailscale/devices.json")
        ).devices
        yield tailscale
