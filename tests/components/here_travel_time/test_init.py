"""The test for the HERE Travel Time integration."""

from datetime import datetime
from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.here_travel_time.config_flow import (
    DEFAULT_OPTIONS,
    HERETravelTimeConfigFlow,
)
from homeassistant.components.here_travel_time.const import (
    CONF_ARRIVAL_TIME,
    CONF_DEPARTURE_TIME,
    CONF_ROUTE_MODE,
    CONF_TRAFFIC_MODE,
    DOMAIN,
    ROUTE_MODE_FASTEST,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from ._fixtures import valid_response
from .const import DEFAULT_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    hass as hass_fixture,
    issue_registry as issue_registry_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _valid: MagicMock = Depends(valid_response),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test.cases(
    test.case("default", options=DEFAULT_OPTIONS),
    test.case(
        "departure_time",
        options={
            CONF_ROUTE_MODE: ROUTE_MODE_FASTEST,
            CONF_DEPARTURE_TIME: datetime.now(),
        },
    ),
    test.case(
        "arrival_time",
        options={
            CONF_ROUTE_MODE: ROUTE_MODE_FASTEST,
            CONF_ARRIVAL_TIME: datetime.now(),
        },
    ),
    test.case(
        "route_mode_only",
        options={CONF_ROUTE_MODE: ROUTE_MODE_FASTEST},
    ),
)
async def unload_entry(
    *,
    options: dict,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that unloading an entry works."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="0123456789",
        data=DEFAULT_CONFIG,
        options=options,
        version=HERETravelTimeConfigFlow.VERSION,
        minor_version=HERETravelTimeConfigFlow.MINOR_VERSION,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)


@test
async def migrate_entry_v1_1_v1_2(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test successful migration of entry data."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=DEFAULT_CONFIG,
        options=DEFAULT_OPTIONS,
        version=1,
        minor_version=1,
    )
    mock_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    updated_entry = hass.config_entries.async_get_entry(mock_entry.entry_id)

    expect(updated_entry is not None).to_be(True)
    expect(updated_entry.state).to_be(ConfigEntryState.LOADED)
    expect(updated_entry.minor_version).to_equal(2)
    expect(updated_entry.options[CONF_TRAFFIC_MODE]).to_be(True)


@test
async def issue_multiple_here_integrations_detected(
    hass: HomeAssistant = Depends(_trigger_executor),
    issue_registry: ir.IssueRegistry = Depends(issue_registry_fixture),
) -> None:
    """Test that an issue is created when multiple HERE integrations are detected."""
    entry1 = MockConfigEntry(
        domain=DOMAIN,
        unique_id="1234567890",
        data=DEFAULT_CONFIG,
        options=DEFAULT_OPTIONS,
    )
    entry2 = MockConfigEntry(
        domain=DOMAIN,
        unique_id="0987654321",
        data=DEFAULT_CONFIG,
        options=DEFAULT_OPTIONS,
    )
    entry1.add_to_hass(hass)
    await hass.config_entries.async_setup(entry1.entry_id)
    entry2.add_to_hass(hass)
    await hass.config_entries.async_setup(entry2.entry_id)
    await hass.async_block_till_done()

    expect(len(issue_registry.issues)).to_equal(1)
