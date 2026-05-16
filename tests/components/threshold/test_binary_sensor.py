"""The test for the threshold sensor platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.threshold.const import (
    ATTR_HYSTERESIS,
    ATTR_LOWER,
    ATTR_POSITION,
    ATTR_SENSOR_VALUE,
    ATTR_TYPE,
    ATTR_UPPER,
    CONF_HYSTERESIS,
    CONF_LOWER,
    CONF_UPPER,
    DOMAIN,
    POSITION_ABOVE,
    POSITION_BELOW,
    POSITION_IN_RANGE,
    POSITION_UNKNOWN,
    TYPE_LOWER,
    TYPE_RANGE,
    TYPE_UPPER,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_PLATFORM,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    Platform,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fx,
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("at_threshold", vals=[15], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("above", vals=[15, 16], expected_position=POSITION_ABOVE, expected_state=STATE_ON),
    test.case("above_below", vals=[15, 16, 14], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("below_threshold", vals=[15, 16, 14, 15], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("cat", vals=[15, 16, 14, 15, "cat"], expected_position=POSITION_UNKNOWN, expected_state=STATE_UNKNOWN),
    test.case("cat_recovery", vals=[15, 16, 14, 15, "cat", 15], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("none", vals=[15, None], expected_position=POSITION_UNKNOWN, expected_state=STATE_UNKNOWN),
)
async def sensor_upper_test(
    vals: list[float | str | None],
    expected_position: str,
    expected_state: str,
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test if source is above threshold."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_UPPER: "15",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    expect(await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_ENTITY_ID]).to_equal("sensor.test_monitored")
    expect(state.attributes[ATTR_UPPER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_UPPER])
    )
    expect(state.attributes[ATTR_HYSTERESIS]).to_equal(0.0)
    expect(state.attributes[ATTR_TYPE]).to_equal(TYPE_UPPER)

    for val in vals:
        hass.states.async_set("sensor.test_monitored", val)
        await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_POSITION]).to_equal(expected_position)
    expect(state.state).to_equal(expected_state)


@test.cases(
    test.case("at_threshold", vals=[15], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("above", vals=[15, 16], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("above_below", vals=[15, 16, 14], expected_position=POSITION_BELOW, expected_state=STATE_ON),
    test.case("below_threshold", vals=[15, 16, 14, 15], expected_position=POSITION_BELOW, expected_state=STATE_ON),
    test.case("cat", vals=[15, 16, 14, 15, "cat"], expected_position=POSITION_UNKNOWN, expected_state=STATE_UNKNOWN),
    test.case("cat_recovery", vals=[15, 16, 14, 15, "cat", 15], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("none", vals=[15, None], expected_position=POSITION_UNKNOWN, expected_state=STATE_UNKNOWN),
)
async def sensor_lower_test(
    vals: list[float | str | None],
    expected_position: str,
    expected_state: str,
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test if source is below threshold."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_LOWER: "15",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    expect(await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_ENTITY_ID]).to_equal("sensor.test_monitored")
    expect(state.attributes[ATTR_LOWER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_LOWER])
    )
    expect(state.attributes[ATTR_HYSTERESIS]).to_equal(0.0)
    expect(state.attributes[ATTR_TYPE]).to_equal(TYPE_LOWER)

    for val in vals:
        hass.states.async_set("sensor.test_monitored", val)
        await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_POSITION]).to_equal(expected_position)
    expect(state.state).to_equal(expected_state)


@test.cases(
    test.case("thresh_plus_hyst", vals=[17.5], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("thresh_minus_hyst", vals=[17.5, 12.5], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("above_20", vals=[17.5, 12.5, 20], expected_position=POSITION_ABOVE, expected_state=STATE_ON),
    test.case("above_then_13", vals=[17.5, 12.5, 20, 13], expected_position=POSITION_ABOVE, expected_state=STATE_ON),
    test.case("crosses_12", vals=[17.5, 12.5, 20, 13, 12], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("then_17", vals=[17.5, 12.5, 20, 13, 12, 17], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("then_18", vals=[17.5, 12.5, 20, 13, 12, 17, 18], expected_position=POSITION_ABOVE, expected_state=STATE_ON),
    test.case("then_cat", vals=[17.5, 12.5, 20, 13, 12, 17, 18, "cat"], expected_position=POSITION_UNKNOWN, expected_state=STATE_UNKNOWN),
    test.case("then_cat_18", vals=[17.5, 12.5, 20, 13, 12, 17, 18, "cat", 18], expected_position=POSITION_ABOVE, expected_state=STATE_ON),
    test.case("18_none", vals=[18, None], expected_position=POSITION_UNKNOWN, expected_state=STATE_UNKNOWN),
    test.case("below_within_to_above", vals=[14, 17.6], expected_position=POSITION_ABOVE, expected_state=STATE_ON),
    test.case("above_within_to_below", vals=[16, 12.4], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("below_within_to_above_within", vals=[14, 16], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("above_within_to_below_within", vals=[16, 14], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("above_to_above_within_to_below_within", vals=[20, 16, 14], expected_position=POSITION_ABOVE, expected_state=STATE_ON),
    test.case("below_to_below_within_to_above_within", vals=[10, 14, 16], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
)
async def sensor_upper_hysteresis_test(
    vals: list[float | str | None],
    expected_position: str,
    expected_state: str,
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test if source is above threshold using hysteresis."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_UPPER: "15",
            CONF_HYSTERESIS: "2.5",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    expect(await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_ENTITY_ID]).to_equal("sensor.test_monitored")
    expect(state.attributes[ATTR_UPPER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_UPPER])
    )
    expect(state.attributes[ATTR_HYSTERESIS]).to_equal(2.5)
    expect(state.attributes[ATTR_TYPE]).to_equal(TYPE_UPPER)

    for val in vals:
        hass.states.async_set("sensor.test_monitored", val)
        await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_POSITION]).to_equal(expected_position)
    expect(state.state).to_equal(expected_state)


@test.cases(
    test.case("thresh_plus_hyst", vals=[17.5], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("thresh_minus_hyst", vals=[17.5, 12.5], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("above_20", vals=[17.5, 12.5, 20], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("above_then_13", vals=[17.5, 12.5, 20, 13], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("crosses_12", vals=[17.5, 12.5, 20, 13, 12], expected_position=POSITION_BELOW, expected_state=STATE_ON),
    test.case("then_17", vals=[17.5, 12.5, 20, 13, 12, 17], expected_position=POSITION_BELOW, expected_state=STATE_ON),
    test.case("then_18", vals=[17.5, 12.5, 20, 13, 12, 17, 18], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("then_cat", vals=[17.5, 12.5, 20, 13, 12, 17, 18, "cat"], expected_position=POSITION_UNKNOWN, expected_state=STATE_UNKNOWN),
    test.case("then_cat_18", vals=[17.5, 12.5, 20, 13, 12, 17, 18, "cat", 18], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("18_none", vals=[18, None], expected_position=POSITION_UNKNOWN, expected_state=STATE_UNKNOWN),
    test.case("below_within_to_above", vals=[14, 17.6], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("above_within_to_below", vals=[16, 12.4], expected_position=POSITION_BELOW, expected_state=STATE_ON),
    test.case("below_within_to_above_within", vals=[14, 16], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("above_within_to_below_within", vals=[16, 14], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("above_to_above_within_to_below_within", vals=[20, 16, 14], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("below_to_below_within_to_above_within", vals=[10, 14, 16], expected_position=POSITION_BELOW, expected_state=STATE_ON),
)
async def sensor_lower_hysteresis_test(
    vals: list[float | str | None],
    expected_position: str,
    expected_state: str,
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test if source is below threshold using hysteresis."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_LOWER: "15",
            CONF_HYSTERESIS: "2.5",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    expect(await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_ENTITY_ID]).to_equal("sensor.test_monitored")
    expect(state.attributes[ATTR_LOWER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_LOWER])
    )
    expect(state.attributes[ATTR_HYSTERESIS]).to_equal(2.5)
    expect(state.attributes[ATTR_TYPE]).to_equal(TYPE_LOWER)

    for val in vals:
        hass.states.async_set("sensor.test_monitored", val)
        await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_POSITION]).to_equal(expected_position)
    expect(state.state).to_equal(expected_state)


@test.cases(
    test.case("at_lower", vals=[10], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("lower_to_upper", vals=[10, 20], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("then_16", vals=[10, 20, 16], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("below_9", vals=[10, 20, 16, 9], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("above_21", vals=[10, 20, 16, 9, 21], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("then_cat", vals=[10, 20, 16, 9, 21, "cat"], expected_position=POSITION_UNKNOWN, expected_state=STATE_UNKNOWN),
    test.case("cat_then_21", vals=[10, 20, 16, 9, 21, "cat", 21], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("21_none", vals=[21, None], expected_position=POSITION_UNKNOWN, expected_state=STATE_UNKNOWN),
    test.case("upper_to_lower", vals=[20, 10], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("in_range_to_upper", vals=[15, 20], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("in_range_to_lower", vals=[15, 10], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("below_to_above", vals=[5, 25], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("above_to_below", vals=[25, 5], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("in_range_to_above", vals=[15, 25], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("in_range_to_below", vals=[15, 5], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
)
async def sensor_in_range_no_hysteresis_test(
    vals: list[float | str | None],
    expected_position: str,
    expected_state: str,
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test if source is within the range."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_LOWER: "10",
            CONF_UPPER: "20",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    expect(await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_ENTITY_ID]).to_equal("sensor.test_monitored")
    expect(state.attributes[ATTR_LOWER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_LOWER])
    )
    expect(state.attributes[ATTR_UPPER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_UPPER])
    )
    expect(state.attributes[ATTR_HYSTERESIS]).to_equal(0.0)
    expect(state.attributes[ATTR_TYPE]).to_equal(TYPE_RANGE)

    for val in vals:
        hass.states.async_set("sensor.test_monitored", val)
        await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_POSITION]).to_equal(expected_position)
    expect(state.state).to_equal(expected_state)


@test.cases(
    test.case("lower_plus_hyst", vals=[12], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("upper_plus_hyst", vals=[12, 22], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("upper_minus_hyst", vals=[12, 22, 18], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("then_16", vals=[12, 22, 18, 16], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("then_8", vals=[12, 22, 18, 16, 8], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("then_7", vals=[12, 22, 18, 16, 8, 7], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("then_12", vals=[12, 22, 18, 16, 8, 7, 12], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("then_13", vals=[12, 22, 18, 16, 8, 7, 12, 13], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("then_22", vals=[12, 22, 18, 16, 8, 7, 12, 13, 22], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("then_23", vals=[12, 22, 18, 16, 8, 7, 12, 13, 22, 23], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("then_18b", vals=[12, 22, 18, 16, 8, 7, 12, 13, 22, 23, 18], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("then_17", vals=[12, 22, 18, 16, 8, 7, 12, 13, 22, 23, 18, 17], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case(
        "then_cat",
        vals=[12, 22, 18, 16, 8, 7, 12, 13, 22, 23, 18, 17, "cat"],
        expected_position=POSITION_UNKNOWN,
        expected_state=STATE_UNKNOWN,
    ),
    test.case(
        "then_cat_17",
        vals=[12, 22, 18, 16, 8, 7, 12, 13, 22, 23, 18, 17, "cat", 17],
        expected_position=POSITION_IN_RANGE,
        expected_state=STATE_ON,
    ),
    test.case("17_none", vals=[17, None], expected_position=POSITION_UNKNOWN, expected_state=STATE_UNKNOWN),
    test.case("upper_to_lower", vals=[20, 10], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("in_range_to_upper", vals=[15, 20], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("in_range_to_lower", vals=[15, 10], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("below_to_above", vals=[5, 25], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("above_to_below", vals=[25, 5], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("in_range_to_above", vals=[15, 25], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("in_range_to_below", vals=[15, 5], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("below_to_lower", vals=[5, 10], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("below_in_range_lower", vals=[5, 15, 10], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("above_to_upper", vals=[25, 20], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("above_in_range_upper", vals=[25, 15, 20], expected_position=POSITION_IN_RANGE, expected_state=STATE_ON),
    test.case("in_range_to_above_hyst_edge", vals=[15, 22.1], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
    test.case("in_range_to_below_hyst_edge", vals=[15, 7.9], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("7_to_11_9", vals=[7, 11.9], expected_position=POSITION_BELOW, expected_state=STATE_OFF),
    test.case("23_to_18_1", vals=[23, 18.1], expected_position=POSITION_ABOVE, expected_state=STATE_OFF),
)
async def sensor_in_range_with_hysteresis_test(
    vals: list[float | str | None],
    expected_position: str,
    expected_state: str,
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test if source is within the range."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_LOWER: "10",
            CONF_UPPER: "20",
            CONF_HYSTERESIS: "2",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    expect(await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_ENTITY_ID]).to_equal("sensor.test_monitored")
    expect(state.attributes[ATTR_LOWER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_LOWER])
    )
    expect(state.attributes[ATTR_UPPER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_UPPER])
    )
    expect(state.attributes[ATTR_HYSTERESIS]).to_equal(2.0)
    expect(state.attributes[ATTR_TYPE]).to_equal(TYPE_RANGE)

    for val in vals:
        hass.states.async_set("sensor.test_monitored", val)
        await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_POSITION]).to_equal(expected_position)
    expect(state.state).to_equal(expected_state)


@test
async def sensor_in_range_unknown_state(
    hass: HomeAssistant = Depends(hass_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test if source is within the range."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_LOWER: "10",
            CONF_UPPER: "20",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    expect(await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set(
        "sensor.test_monitored",
        16,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.threshold")

    expect(state.attributes[ATTR_ENTITY_ID]).to_equal("sensor.test_monitored")
    expect(state.attributes[ATTR_SENSOR_VALUE]).to_equal(16)
    expect(state.attributes[ATTR_POSITION]).to_equal(POSITION_IN_RANGE)
    expect(state.attributes[ATTR_LOWER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_LOWER])
    )
    expect(state.attributes[ATTR_UPPER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_UPPER])
    )
    expect(state.attributes[ATTR_HYSTERESIS]).to_equal(0.0)
    expect(state.attributes[ATTR_TYPE]).to_equal(TYPE_RANGE)
    expect(state.state).to_equal(STATE_ON)

    hass.states.async_set("sensor.test_monitored", STATE_UNKNOWN)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_POSITION]).to_equal(POSITION_UNKNOWN)
    expect(state.state).to_equal(STATE_UNKNOWN)

    hass.states.async_set("sensor.test_monitored", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_POSITION]).to_equal(POSITION_UNKNOWN)
    expect(state.state).to_equal(STATE_UNKNOWN)

    expect("State is not numerical" not in caplog.text).to_be(True)


@test
async def sensor_lower_zero_threshold(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test if a lower threshold of zero is set."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_LOWER: "0",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    expect(await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.test_monitored", 16)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_TYPE]).to_equal(TYPE_LOWER)
    expect(state.attributes[ATTR_LOWER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_LOWER])
    )
    expect(state.state).to_equal(STATE_OFF)

    hass.states.async_set("sensor.test_monitored", -3)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.state).to_equal(STATE_ON)


@test
async def sensor_upper_zero_threshold(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test if an upper threshold of zero is set."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_UPPER: "0",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    expect(await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.test_monitored", -10)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.attributes[ATTR_TYPE]).to_equal(TYPE_UPPER)
    expect(state.attributes[ATTR_UPPER]).to_equal(
        float(config[Platform.BINARY_SENSOR][CONF_UPPER])
    )
    expect(state.state).to_equal(STATE_OFF)

    hass.states.async_set("sensor.test_monitored", 2)
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.threshold")
    expect(state.state).to_equal(STATE_ON)


@test
async def sensor_no_lower_upper(
    hass: HomeAssistant = Depends(hass_fx),
    caplog: LogCapture = Depends(caplog_fx),
) -> None:
    """Test if no lower or upper has been provided."""
    config = {
        Platform.BINARY_SENSOR: {
            CONF_PLATFORM: "threshold",
            CONF_ENTITY_ID: "sensor.test_monitored",
        }
    }

    await async_setup_component(hass, BINARY_SENSOR_DOMAIN, config)
    await hass.async_block_till_done()

    expect("Lower or Upper thresholds are not provided" in caplog.text).to_be(True)


@test
async def device_id(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test for source entity device for Threshold."""
    source_config_entry = MockConfigEntry()
    source_config_entry.add_to_hass(hass)
    source_device_entry = device_registry.async_get_or_create(
        config_entry_id=source_config_entry.entry_id,
        identifiers={("sensor", "identifier_test")},
        connections={("mac", "30:31:32:33:34:35")},
    )
    source_entity = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source",
        config_entry=source_config_entry,
        device_id=source_device_entry.id,
    )
    await hass.async_block_till_done()
    expect(entity_registry.async_get("sensor.test_source") is not None).to_be(True)

    utility_meter_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: "sensor.test_source",
            CONF_HYSTERESIS: 0.0,
            CONF_LOWER: -2.0,
            CONF_NAME: "Threshold",
            CONF_UPPER: None,
        },
        title="Threshold",
    )

    utility_meter_config_entry.add_to_hass(hass)

    expect(
        await hass.config_entries.async_setup(utility_meter_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    utility_meter_entity = entity_registry.async_get("binary_sensor.threshold")
    expect(utility_meter_entity is not None).to_be(True)
    expect(utility_meter_entity.device_id).to_equal(source_entity.device_id)
