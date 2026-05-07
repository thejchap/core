"""Test the Novy Hood config flow."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.novy_cooker_hood.commands import COMMAND_LIGHT
from homeassistant.components.novy_cooker_hood.const import (
    CONF_CODE,
    CONF_TRANSMITTER,
    DOMAIN,
)
from homeassistant.components.radio_frequency import DATA_COMPONENT, DOMAIN as RF_DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import (
    TRANSMITTER_ENTITY_ID,
    mock_config_entry,
    mock_get_codes,
    mock_rf_entity,
    mock_toggle_gap,
)

from tests.common import MockConfigEntry
from tests.components.radio_frequency.common import MockRadioFrequencyEntity
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _toggle: None = Depends(mock_toggle_gap),
) -> None:
    """Anchor fixture (mock_toggle_gap autouse equivalent)."""


async def _start_user_flow(hass: HomeAssistant, code: str = "1") -> dict:
    """Start the flow and submit the user step with the given code."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(CONF_CODE in result["data_schema"].schema).to_be(True)

    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TRANSMITTER: TRANSMITTER_ENTITY_ID,
            CONF_CODE: code,
        },
    )


@test
async def user_flow_test_then_finish(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    get_codes: MagicMock = Depends(mock_get_codes),
    rf_entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Submitting the user step fires the test, then Finish creates the entry."""
    result = await _start_user_flow(hass, code="3")

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("test_light")
    get_codes.async_load_command.assert_awaited_with(COMMAND_LIGHT)
    expect(len(rf_entity.send_command_calls)).to_equal(2)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "finish"}
    )

    entity_entry = entity_registry.async_get(TRANSMITTER_ENTITY_ID)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Novy Cooker Hood")
    expect(result["data"]).to_equal(
        {
            CONF_TRANSMITTER: entity_entry.id,
            CONF_CODE: 3,
        }
    )
    expect(result["result"].unique_id).to_equal(f"{entity_entry.id}_3")


@test
async def user_flow_retry_picks_different_code(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    get_codes: MagicMock = Depends(mock_get_codes),
    rf_entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Retry returns to the user step; a new code re-fires the test and saves."""
    result = await _start_user_flow(hass, code="1")
    expect(result["type"]).to_be(FlowResultType.MENU)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "retry"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TRANSMITTER: TRANSMITTER_ENTITY_ID,
            CONF_CODE: "7",
        },
    )
    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(get_codes.async_load_command.await_count).to_equal(2)
    expect(len(rf_entity.send_command_calls)).to_equal(4)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "finish"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_CODE]).to_equal(7)


@test
async def user_flow_test_transmit_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    rf_entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
) -> None:
    """A transmit failure surfaces as a `test_failed` menu with a Retry option."""
    with patch(
        "homeassistant.components.novy_cooker_hood.config_flow.async_send_command",
        side_effect=HomeAssistantError("nope"),
    ):
        result = await _start_user_flow(hass)

    expect(result["type"]).to_be(FlowResultType.MENU)
    expect(result["step_id"]).to_equal("test_failed")


@test
async def unique_id_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test aborting when the same transmitter+code is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TRANSMITTER: TRANSMITTER_ENTITY_ID,
            CONF_CODE: "1",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def same_transmitter_different_code_is_allowed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    get_codes: MagicMock = Depends(mock_get_codes),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    rf_entity: MockRadioFrequencyEntity = Depends(mock_rf_entity),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """A second hood on the same transmitter but a different code is allowed."""
    config_entry.add_to_hass(hass)

    result = await _start_user_flow(hass, code="5")
    expect(result["type"]).to_be(FlowResultType.MENU)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "finish"}
    )
    entity_entry = entity_registry.async_get(TRANSMITTER_ENTITY_ID)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_CODE]).to_equal(5)
    expect(result["result"].unique_id).to_equal(f"{entity_entry.id}_5")


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
    expect(await async_setup_component(hass, RF_DOMAIN, {})).to_be_truthy()
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
