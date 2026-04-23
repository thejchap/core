"""Test the Nina config flow."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock

from pynina import ApiError, Warning
from tryke import Depends, expect, fixture, test

from homeassistant.components.nina.const import (
    CONF_AREA_FILTER,
    CONF_FILTERS,
    CONF_HEADLINE_FILTER,
    CONF_MESSAGE_SLOTS,
    CONF_REGIONS,
    CONST_REGION_A_TO_D,
    CONST_REGION_E_TO_H,
    CONST_REGION_I_TO_L,
    CONST_REGION_M_TO_Q,
    CONST_REGION_R_TO_U,
    CONST_REGION_V_TO_Z,
    DOMAIN,
    SENSOR_SUFFIXES,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry
from tests.components.nina import setup_platform
from tests.components.nina._fixtures import (
    mock_config_entry,
    mock_nina_class,
    mock_setup_entry,
    nina_warnings,
)
from tests.components.nina.const import DUMMY_USER_INPUT
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


def assert_dummy_entry_created(result: dict[str, Any]) -> None:
    """Asserts that an entry from DUMMY_USER_INPUT is created."""
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NINA")
    expect(result["data"]).to_equal(
        DUMMY_USER_INPUT
        | {
            CONF_REGIONS: {
                "095760000000": "Allersberg, M (Roth - Bayern) + Büchenbach (Roth - Bayern)"
            }
        }
    )
    expect(result["version"]).to_equal(1)
    expect(result["minor_version"]).to_equal(3)


@test
async def step_user_connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    nina_class: AsyncMock = Depends(mock_nina_class),
) -> None:
    """Test starting a flow by user but no connection."""
    nina_class.get_all_regional_codes.side_effect = ApiError(
        "Could not connect to Api"
    )

    result: dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_fetch")


@test
async def step_user_unexpected_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    nina_class: AsyncMock = Depends(mock_nina_class),
) -> None:
    """Test starting a flow by user but with an unexpected exception."""
    nina_class.get_all_regional_codes.side_effect = Exception("DUMMY")

    result: dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def step_user(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
    _nc: AsyncMock = Depends(mock_nina_class),
) -> None:
    """Test starting a flow by user with valid values."""
    result: dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=deepcopy(DUMMY_USER_INPUT),
    )
    assert_dummy_entry_created(result)


@test
async def step_user_no_selection(
    hass: HomeAssistant = Depends(hass_fixture),
    _nc: AsyncMock = Depends(mock_nina_class),
) -> None:
    """Test starting a flow by user with no selection."""
    result: dict[str, Any] = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_FILTERS: {CONF_HEADLINE_FILTER: ""}},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "no_selection"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=deepcopy(DUMMY_USER_INPUT),
    )
    assert_dummy_entry_created(result)


@test
async def step_user_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _config: MockConfigEntry = Depends(mock_config_entry),
    _nc: AsyncMock = Depends(mock_nina_class),
) -> None:
    """Test starting a flow by user, but it was already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def options_flow_init(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    nina_class: AsyncMock = Depends(mock_nina_class),
    warnings_: list[Warning] = Depends(nina_warnings),
) -> None:
    """Test config flow options."""
    await setup_platform(hass, config_entry, nina_class, warnings_)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONST_REGION_A_TO_D: ["072350000000_1"],
            CONST_REGION_E_TO_H: [],
            CONST_REGION_I_TO_L: [],
            CONST_REGION_M_TO_Q: [],
            CONST_REGION_R_TO_U: [],
            CONST_REGION_V_TO_Z: [],
            CONF_FILTERS: {
                CONF_HEADLINE_FILTER: ".*corona.*",
                CONF_AREA_FILTER: ".*",
            },
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({})

    expect(dict(config_entry.data)).to_equal(
        {
            CONF_FILTERS: DUMMY_USER_INPUT[CONF_FILTERS],
            CONF_MESSAGE_SLOTS: DUMMY_USER_INPUT[CONF_MESSAGE_SLOTS],
            CONST_REGION_A_TO_D: ["072350000000_1"],
            CONST_REGION_E_TO_H: [],
            CONST_REGION_I_TO_L: [],
            CONST_REGION_M_TO_Q: [],
            CONST_REGION_R_TO_U: [],
            CONST_REGION_V_TO_Z: [],
            CONF_REGIONS: {
                "072350000000": "Damflos (Trier-Saarburg - Rheinland-Pfalz)"
            },
        }
    )


@test
async def options_flow_with_no_selection(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    nina_class: AsyncMock = Depends(mock_nina_class),
    warnings_: list[Warning] = Depends(nina_warnings),
) -> None:
    """Test config flow options with no selection."""
    await setup_platform(hass, config_entry, nina_class, warnings_)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONST_REGION_A_TO_D: [],
            CONST_REGION_E_TO_H: [],
            CONST_REGION_I_TO_L: [],
            CONST_REGION_M_TO_Q: [],
            CONST_REGION_R_TO_U: [],
            CONST_REGION_V_TO_Z: [],
            CONF_FILTERS: {CONF_HEADLINE_FILTER: ""},
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect(result["errors"]).to_equal({"base": "no_selection"})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONST_REGION_A_TO_D: ["095760000000_0"],
            CONST_REGION_E_TO_H: [],
            CONST_REGION_I_TO_L: [],
            CONST_REGION_M_TO_Q: [],
            CONST_REGION_R_TO_U: [],
            CONST_REGION_V_TO_Z: [],
            CONF_FILTERS: {
                CONF_HEADLINE_FILTER: ".*corona.*",
                CONF_AREA_FILTER: ".*",
            },
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({})

    expect(dict(config_entry.data)).to_equal(
        {
            CONF_FILTERS: DUMMY_USER_INPUT[CONF_FILTERS],
            CONF_MESSAGE_SLOTS: DUMMY_USER_INPUT[CONF_MESSAGE_SLOTS],
            CONST_REGION_A_TO_D: ["095760000000_0"],
            CONST_REGION_E_TO_H: [],
            CONST_REGION_I_TO_L: [],
            CONST_REGION_M_TO_Q: [],
            CONST_REGION_R_TO_U: [],
            CONST_REGION_V_TO_Z: [],
            CONF_REGIONS: {"095760000000": "Allersberg, M (Roth - Bayern)"},
        }
    )


@test
async def options_flow_connection_error(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    nina_class: AsyncMock = Depends(mock_nina_class),
    warnings_: list[Warning] = Depends(nina_warnings),
) -> None:
    """Test config flow options but no connection."""
    nina_class.get_all_regional_codes.side_effect = ApiError(
        "Could not connect to Api"
    )

    await setup_platform(hass, config_entry, nina_class, warnings_)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_fetch")


@test
async def options_flow_unexpected_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    nina_class: AsyncMock = Depends(mock_nina_class),
    warnings_: list[Warning] = Depends(nina_warnings),
) -> None:
    """Test config flow options but with an unexpected exception."""
    nina_class.get_all_regional_codes.side_effect = Exception("DUMMY")

    await setup_platform(hass, config_entry, nina_class, warnings_)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def options_flow_entity_removal(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    nina_class: AsyncMock = Depends(mock_nina_class),
    warnings_: list[Warning] = Depends(nina_warnings),
) -> None:
    """Test if old entities are removed."""
    await setup_platform(hass, config_entry, nina_class, warnings_)

    entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )

    entities_per_slot = len(SENSOR_SUFFIXES) + 1

    expect(len(entries)).to_equal(
        config_entry.data.get(CONF_MESSAGE_SLOTS) * entities_per_slot
    )

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    new_slot_count = 2

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_MESSAGE_SLOTS: new_slot_count,
            CONST_REGION_A_TO_D: ["095760000000"],
            CONST_REGION_E_TO_H: [],
            CONST_REGION_I_TO_L: [],
            CONST_REGION_M_TO_Q: [],
            CONST_REGION_R_TO_U: [],
            CONST_REGION_V_TO_Z: [],
            CONF_FILTERS: {},
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )

    expect(len(entries)).to_equal(new_slot_count * entities_per_slot)
