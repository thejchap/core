"""Test the Honeywell String Lights config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.honeywell_string_lights.const import (
    CONF_TRANSMITTER,
    DOMAIN,
)
from homeassistant.components.radio_frequency import DATA_COMPONENT, DOMAIN as RF_DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import (
    TRANSMITTER_ENTITY_ID,
    mock_config_entry,
    mock_rf_entity,
)

from tests.common import MockConfigEntry
from tests.components.radio_frequency.common import MockRadioFrequencyEntity
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _rf_entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test the user config flow creates an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_TRANSMITTER: TRANSMITTER_ENTITY_ID},
    )

    entity_entry = entity_registry.async_get(TRANSMITTER_ENTITY_ID)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Honeywell String Lights")
    expect(result["data"]).to_equal({CONF_TRANSMITTER: entity_entry.id})
    expect(result["result"].unique_id).to_equal(entity_entry.id)


@test
async def unique_id_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test aborting when the same transmitter is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_TRANSMITTER: TRANSMITTER_ENTITY_ID},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def no_transmitters(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the flow aborts when no RF transmitters are registered at all."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_transmitters")


@test
async def no_compatible_transmitters(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test aborting when transmitters exist but none support 433.92 MHz OOK."""
    expect(await async_setup_component(hass, RF_DOMAIN, {})).to_be(True)
    await hass.async_block_till_done()
    incompatible = MockRadioFrequencyEntity(
        "incompatible", frequency_ranges=[(868_000_000, 869_000_000)]
    )
    await hass.data[DATA_COMPONENT].async_add_entities([incompatible])

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_compatible_transmitters")
