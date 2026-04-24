"""Tryke fixtures for PVOutput tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from pvo import Status, System
from tryke import Depends, fixture

from homeassistant.components.pvoutput.const import CONF_SYSTEM_ID, DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="12345",
        domain=DOMAIN,
        data={CONF_API_KEY: "tskey-MOCK", CONF_SYSTEM_ID: 12345},
        unique_id="12345",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.pvoutput.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_pvoutput() -> Generator[MagicMock]:
    """Return a mocked PVOutput client."""
    with (
        patch(
            "homeassistant.components.pvoutput.coordinator.PVOutput", autospec=True
        ) as pvoutput_mock,
        patch(
            "homeassistant.components.pvoutput.config_flow.PVOutput",
            new=pvoutput_mock,
        ),
    ):
        pvoutput = pvoutput_mock.return_value
        pvoutput.status.return_value = Status.from_dict(
            load_json_object_fixture("status.json", DOMAIN)
        )
        pvoutput.system.return_value = System.from_dict(
            load_json_object_fixture("system.json", DOMAIN)
        )
        yield pvoutput


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _mock: MagicMock = Depends(mock_pvoutput),
) -> MockConfigEntry:
    """Set up the PVOutput integration for testing."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
