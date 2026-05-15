"""The tests for assist_pipeline logbook."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import assist_pipeline, logbook
from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component

from ._fixtures import init_components

from tests.common import MockConfigEntry
from tests.components.logbook.common import MockRow, mock_humanify
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_components),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves hass before the test body."""
    return hass


@test
async def recording_event(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test recording event."""
    hass.config.components.add("recorder")
    assert await async_setup_component(hass, "logbook", {})
    await hass.async_block_till_done()

    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    satellite_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "satellite-1234")},
    )

    device_registry.async_update_device(satellite_device.id, name="My Satellite")
    event = mock_humanify(
        hass,
        [
            MockRow(
                assist_pipeline.EVENT_RECORDING,
                {ATTR_DEVICE_ID: satellite_device.id},
            ),
        ],
    )[0]

    expect(event[logbook.LOGBOOK_ENTRY_NAME]).to_equal("My Satellite")
    expect(event[logbook.LOGBOOK_ENTRY_DOMAIN]).to_equal(assist_pipeline.DOMAIN)
    expect(event[logbook.LOGBOOK_ENTRY_MESSAGE]).to_equal(
        "My Satellite captured an audio sample"
    )
