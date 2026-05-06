"""Test the Switch as X config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.switch_as_x.config_flow import SwitchAsXConfigFlowHandler
from homeassistant.components.switch_as_x.const import (
    CONF_INVERT,
    CONF_TARGET_DOMAIN,
    DOMAIN,
)
from homeassistant.const import CONF_ENTITY_ID, STATE_ON, Platform
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from . import STATE_MAP
from ._fixtures import mock_setup_entry, setup_homeassistant

from tests.common import MockConfigEntry, get_schema_suggested_value
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _ha: None = Depends(setup_homeassistant),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test.cases(
    test.case("cover", target_domain=Platform.COVER),
    test.case("fan", target_domain=Platform.FAN),
    test.case("light", target_domain=Platform.LIGHT),
    test.case("lock", target_domain=Platform.LOCK),
    test.case("siren", target_domain=Platform.SIREN),
    test.case("valve", target_domain=Platform.VALVE),
)
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    target_domain: Platform,
) -> None:
    """Test the config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ENTITY_ID: "switch.ceiling",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("ceiling")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            CONF_ENTITY_ID: "switch.ceiling",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            CONF_ENTITY_ID: "switch.ceiling",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        }
    )


@test.cases(
    test.case(
        "cover_user_user",
        target_domain=Platform.COVER,
        hidden_by_before=er.RegistryEntryHider.USER,
        hidden_by_after=er.RegistryEntryHider.USER,
    ),
    test.case(
        "fan_user_user",
        target_domain=Platform.FAN,
        hidden_by_before=er.RegistryEntryHider.USER,
        hidden_by_after=er.RegistryEntryHider.USER,
    ),
    test.case(
        "light_user_user",
        target_domain=Platform.LIGHT,
        hidden_by_before=er.RegistryEntryHider.USER,
        hidden_by_after=er.RegistryEntryHider.USER,
    ),
    test.case(
        "lock_user_user",
        target_domain=Platform.LOCK,
        hidden_by_before=er.RegistryEntryHider.USER,
        hidden_by_after=er.RegistryEntryHider.USER,
    ),
    test.case(
        "siren_user_user",
        target_domain=Platform.SIREN,
        hidden_by_before=er.RegistryEntryHider.USER,
        hidden_by_after=er.RegistryEntryHider.USER,
    ),
    test.case(
        "valve_user_user",
        target_domain=Platform.VALVE,
        hidden_by_before=er.RegistryEntryHider.USER,
        hidden_by_after=er.RegistryEntryHider.USER,
    ),
    test.case(
        "cover_none_integration",
        target_domain=Platform.COVER,
        hidden_by_before=None,
        hidden_by_after=er.RegistryEntryHider.INTEGRATION,
    ),
    test.case(
        "fan_none_integration",
        target_domain=Platform.FAN,
        hidden_by_before=None,
        hidden_by_after=er.RegistryEntryHider.INTEGRATION,
    ),
    test.case(
        "light_none_integration",
        target_domain=Platform.LIGHT,
        hidden_by_before=None,
        hidden_by_after=er.RegistryEntryHider.INTEGRATION,
    ),
    test.case(
        "lock_none_integration",
        target_domain=Platform.LOCK,
        hidden_by_before=None,
        hidden_by_after=er.RegistryEntryHider.INTEGRATION,
    ),
    test.case(
        "siren_none_integration",
        target_domain=Platform.SIREN,
        hidden_by_before=None,
        hidden_by_after=er.RegistryEntryHider.INTEGRATION,
    ),
    test.case(
        "valve_none_integration",
        target_domain=Platform.VALVE,
        hidden_by_before=None,
        hidden_by_after=er.RegistryEntryHider.INTEGRATION,
    ),
)
async def config_flow_registered_entity(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    target_domain: Platform,
    hidden_by_before: er.RegistryEntryHider | None,
    hidden_by_after: er.RegistryEntryHider,
) -> None:
    """Test the config flow hides a registered entity."""
    switch_entity_entry = entity_registry.async_get_or_create(
        "switch", "test", "unique", suggested_object_id="ceiling"
    )
    expect(switch_entity_entry.entity_id).to_equal("switch.ceiling")
    entity_registry.async_update_entity("switch.ceiling", hidden_by=hidden_by_before)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ENTITY_ID: "switch.ceiling",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("ceiling")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            CONF_ENTITY_ID: "switch.ceiling",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            CONF_ENTITY_ID: "switch.ceiling",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        }
    )

    switch_entity_entry = entity_registry.async_get("switch.ceiling")
    expect(switch_entity_entry.hidden_by).to_equal(hidden_by_after)


@test.cases(
    test.case("cover", target_domain=Platform.COVER),
    test.case("fan", target_domain=Platform.FAN),
    test.case("light", target_domain=Platform.LIGHT),
    test.case("lock", target_domain=Platform.LOCK),
    test.case("siren", target_domain=Platform.SIREN),
    test.case("valve", target_domain=Platform.VALVE),
)
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    target_domain: Platform,
) -> None:
    """Test reconfiguring."""
    switch_state = STATE_ON
    hass.states.async_set("switch.ceiling", switch_state)
    switch_as_x_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: "switch.ceiling",
            CONF_INVERT: True,
            CONF_TARGET_DOMAIN: target_domain,
        },
        title="ABC",
        version=SwitchAsXConfigFlowHandler.VERSION,
        minor_version=SwitchAsXConfigFlowHandler.MINOR_VERSION,
    )
    switch_as_x_config_entry.add_to_hass(hass)

    expect(
        await hass.config_entries.async_setup(switch_as_x_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get(f"{target_domain}.abc")
    expect(state.state).to_equal(STATE_MAP[True][target_domain][switch_state])

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry is not None).to_be(True)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect(get_schema_suggested_value(result["data_schema"].schema, CONF_INVERT)).to_be(
        True
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_INVERT: False,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_ENTITY_ID: "switch.ceiling",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        }
    )
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            CONF_ENTITY_ID: "switch.ceiling",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        }
    )
    expect(config_entry.title).to_equal("ABC")

    # Check config entry is reloaded with new options
    await hass.async_block_till_done()

    # Check the entity was updated, no new entity was created
    expect(len(hass.states.async_all())).to_equal(2)

    # Check the state of the entity has changed as expected
    state = hass.states.get(f"{target_domain}.abc")
    expect(state.state).to_equal(STATE_MAP[False][target_domain][switch_state])
