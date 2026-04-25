"""Test the generic thermostat config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import PRESET_AWAY
from homeassistant.components.generic_thermostat.config_flow import _validate_config
from homeassistant.components.generic_thermostat.const import (
    CONF_AC_MODE,
    CONF_COLD_TOLERANCE,
    CONF_HEATER,
    CONF_HOT_TOLERANCE,
    CONF_KEEP_ALIVE,
    CONF_MAX_DUR,
    CONF_MIN_DUR,
    CONF_PRESETS,
    CONF_SENSOR,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.schema_config_entry_flow import SchemaFlowError

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.skip("uses syrupy snapshot")
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow."""


@test.skip("uses syrupy snapshot")
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring."""


@test.skip("uses syrupy snapshot")
async def config_flow_preset_accepts_float(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow with preset is a float."""


@test
async def config_flow_with_keep_alive(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow when keep_alive is set."""
    with patch(
        "homeassistant.components.generic_thermostat.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        # Keep_alive input data for test.
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "My thermostat",
                CONF_HEATER: "switch.run",
                CONF_SENSOR: "sensor.temperature",
                CONF_AC_MODE: False,
                CONF_COLD_TOLERANCE: 0.3,
                CONF_HOT_TOLERANCE: 0.3,
                CONF_KEEP_ALIVE: {"seconds": 60},
            },
        )

        # Complete config flow.
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_PRESETS[PRESET_AWAY]: 21,
            },
        )

        expect(result["type"]).to_equal("create_entry")

        val = result["options"].get(CONF_KEEP_ALIVE)
        expect(val is not None).to_be(True)
        expect(isinstance(val, dict)).to_be(True)
        expect(val).to_equal({"seconds": 60})

        await hass.async_block_till_done()
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def validate_config_min_max_duration() -> None:
    """Test _validate_config with min and max cycle duration validation."""
    # Test valid case: min_dur < max_dur.
    user_input = {
        CONF_MIN_DUR: {"seconds": 30},
        CONF_MAX_DUR: {"minutes": 1},
    }
    result = await _validate_config(None, user_input)
    expect(result).to_equal(user_input)

    # Test invalid case: min_dur >= max_dur.
    user_input_invalid = {
        CONF_MIN_DUR: {"minutes": 2},
        CONF_MAX_DUR: {"minutes": 1},
    }
    raised = False
    try:
        await _validate_config(None, user_input_invalid)
    except SchemaFlowError as exc:
        raised = True
        expect(str(exc)).to_equal("min_max_runtime")
    expect(raised).to_be(True)

    # Test equal durations (should fail).
    user_input_equal = {
        CONF_MIN_DUR: {"minutes": 1},
        CONF_MAX_DUR: {"minutes": 1},
    }
    raised = False
    try:
        await _validate_config(None, user_input_equal)
    except SchemaFlowError as exc:
        raised = True
        expect(str(exc)).to_equal("min_max_runtime")
    expect(raised).to_be(True)

    # Test without both durations (should pass).
    user_input_partial = {
        CONF_MIN_DUR: {"seconds": 30},
    }
    result = await _validate_config(None, user_input_partial)
    expect(result).to_equal(user_input_partial)
