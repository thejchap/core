"""Freedompro component tests."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.freedompro.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import init_integration, mock_freedompro

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

ENTITY_ID = f"{DOMAIN}.fake_name"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
def domain_const_importable() -> None:
    """Smoke test: the freedompro integration's DOMAIN constant imports cleanly."""
    expect(DOMAIN).to_equal("freedompro")


@test
async def async_setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test a successful setup entry."""
    expect(entry is not None).to_be(True)
    expect(hass.states is not None).to_be(True)


@test
async def config_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for setup failure if connection to Freedompro is missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Feedompro",
        unique_id="0123456",
        data={
            "api_key": "gdhsksjdhcncjdkdjndjdkdmndjdjdkd",
        },
    )

    with patch(
        "homeassistant.components.freedompro.coordinator.get_list",
        return_value={
            "state": False,
        },
    ):
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test successful unload of entry."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
