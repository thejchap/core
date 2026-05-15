"""The tests for the integration sensor platform."""

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config as hass_config
from homeassistant.components.compensation.const import CONF_PRECISION, DOMAIN
from homeassistant.components.compensation.sensor import ATTR_COEFFICIENTS
from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    EVENT_HOMEASSISTANT_START,
    EVENT_STATE_CHANGED,
    SERVICE_RELOAD,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import assert_setup_component, get_fixture_path
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
)

TEST_OBJECT_ID = "test_compensation"
TEST_ENTITY_ID = "sensor.test_compensation"
TEST_SOURCE = "sensor.uncompensated"

TEST_BASE_CONFIG = {
    "source": TEST_SOURCE,
    "data_points": [
        [1.0, 2.0],
        [2.0, 3.0],
    ],
    "precision": 2,
}
TEST_CONFIG = {
    "name": TEST_OBJECT_ID,
    "unit_of_measurement": "a",
    **TEST_BASE_CONFIG,
}


async def async_setup_compensation(hass: HomeAssistant, config: dict[str, Any]) -> None:
    """Do setup of a compensation integration sensor."""
    with assert_setup_component(1, DOMAIN):
        expect(
            await async_setup_component(
                hass,
                DOMAIN,
                {DOMAIN: {"test": config}},
            )
        ).to_be(True)

    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def linear_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test compensation sensor state."""
    config = TEST_CONFIG
    await async_setup_compensation(hass, config)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.states.async_set(TEST_SOURCE, 4, {})
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    expect(state is not None).to_be(True)

    expect(round(float(state.state), config[CONF_PRECISION])).to_equal(5.0)
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal("a")

    coefs = [round(v, 1) for v in state.attributes.get(ATTR_COEFFICIENTS)]
    expect(coefs).to_equal([1.0, 1.0])

    hass.states.async_set(TEST_SOURCE, "foo", {})
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def attributes_come_from_source(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test compensation sensor state."""
    await async_setup_compensation(hass, {"name": TEST_OBJECT_ID, **TEST_BASE_CONFIG})
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.states.async_set(
        TEST_SOURCE,
        4,
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
            ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("5.0")
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(SensorDeviceClass.TEMPERATURE)
    expect(state.attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal(
        UnitOfTemperature.CELSIUS
    )
    expect(state.attributes[ATTR_STATE_CLASS]).to_equal(SensorStateClass.MEASUREMENT)


@test
async def linear_state_from_attribute(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test compensation sensor state that pulls from attribute."""
    config = {"attribute": "value", **TEST_CONFIG}
    await async_setup_compensation(hass, config)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    hass.states.async_set(TEST_SOURCE, 3, {"value": 4})
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    expect(state is not None).to_be(True)
    expect(round(float(state.state), config[CONF_PRECISION])).to_equal(5.0)

    coefs = [round(v, 1) for v in state.attributes.get(ATTR_COEFFICIENTS)]
    expect(coefs).to_equal([1.0, 1.0])

    hass.states.async_set(TEST_SOURCE, 3, {"value": "bar"})
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def quadratic_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test 3 degree polynominial compensation sensor."""
    config = {
        "name": TEST_OBJECT_ID,
        "source": TEST_SOURCE,
        "data_points": [
            [50, 3.3],
            [50, 2.8],
            [50, 2.9],
            [70, 2.3],
            [70, 2.6],
            [70, 2.1],
            [80, 2.5],
            [80, 2.9],
            [80, 2.4],
            [90, 3.0],
            [90, 3.1],
            [90, 2.8],
            [100, 3.3],
            [100, 3.5],
            [100, 3.0],
        ],
        "degree": 2,
        "precision": 3,
    }
    await async_setup_compensation(hass, config)
    hass.states.async_set(TEST_SOURCE, 43.2, {})
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    expect(state is not None).to_be(True)
    expect(round(float(state.state), config[CONF_PRECISION])).to_equal(3.327)


@test
async def numpy_errors(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Tests bad polyfits."""
    config = {
        "source": TEST_SOURCE,
        "data_points": [
            [0.0, 1.0],
            [0.0, 1.0],
        ],
    }
    await async_setup_compensation(hass, config)
    expect("invalid value encountered in divide" in caplog.text).to_be(True)


@test
async def datapoints_greater_than_degree(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Tests 3 bad data points."""
    config = {
        "compensation": {
            "test": {
                "source": TEST_SOURCE,
                "data_points": [
                    [1.0, 2.0],
                    [2.0, 3.0],
                ],
                "degree": 2,
            },
        }
    }
    await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    expect("data_points must have at least 3 data_points" in caplog.text).to_be(True)


@test
async def new_state_is_none(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Tests catch for empty new states."""
    await async_setup_compensation(hass, TEST_CONFIG)
    last_changed = hass.states.get(TEST_ENTITY_ID).last_changed
    hass.bus.async_fire(EVENT_STATE_CHANGED, event_data={"entity_id": TEST_SOURCE})
    expect(last_changed == hass.states.get(TEST_ENTITY_ID).last_changed).to_be(True)


_LIMITS_CONFIG = {
    "name": TEST_OBJECT_ID,
    "source": TEST_SOURCE,
    "data_points": [
        [1.0, 0.0],
        [3.0, 2.0],
        [2.0, 1.0],
    ],
    "precision": 2,
    "unit_of_measurement": "a",
}


@test.cases(
    test.case("lower_only", lower=True, upper=False),
    test.case("upper_only", lower=False, upper=True),
    test.case("both", lower=True, upper=True),
)
async def limits(
    lower: bool,
    upper: bool,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test compensation sensor state."""
    await async_setup_compensation(
        hass,
        {
            **_LIMITS_CONFIG,
            "lower_limit": lower,
            "upper_limit": upper,
        },
    )
    hass.states.async_set(TEST_SOURCE, 0, {})
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    value = 0.0 if lower else -1.0
    expect(float(state.state)).to_equal(value)

    hass.states.async_set(TEST_SOURCE, 5, {})
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    value = 2.0 if upper else 4.0
    expect(float(state.state)).to_equal(value)


@test.cases(
    test.case(
        "no_attribute",
        config=TEST_BASE_CONFIG,
        expected="sensor.compensation_sensor_uncompensated",
    ),
    test.case(
        "with_attribute",
        config={"attribute": "value", **TEST_BASE_CONFIG},
        expected="sensor.compensation_sensor_uncompensated_value",
    ),
)
async def default_name(
    config: dict[str, Any],
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test default configuration name."""
    await async_setup_compensation(hass, config)
    expect(hass.states.get(expected) is not None).to_be(True)


@test.cases(
    test.case("unknown", source_state=STATE_UNKNOWN, expected=STATE_UNKNOWN),
    test.case(
        "unavailable", source_state=STATE_UNAVAILABLE, expected=STATE_UNAVAILABLE
    ),
)
async def non_numerical_states_from_source_entity(
    source_state: str,
    expected: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test non-numerical states from source entity."""
    config = TEST_CONFIG
    await async_setup_compensation(hass, config)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    hass.states.async_set(TEST_SOURCE, source_state)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(expected)

    hass.states.async_set(TEST_SOURCE, 4)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    expect(state is not None).to_be(True)
    expect(round(float(state.state), config[CONF_PRECISION])).to_equal(5.0)

    hass.states.async_set(TEST_SOURCE, source_state)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(expected)


@test
async def source_state_none(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test is source sensor state is null and sets state to STATE_UNKNOWN."""
    config = {
        "sensor": [
            {
                "platform": "template",
                "sensors": {
                    "uncompensated": {
                        "value_template": "{{ states.sensor.test_state.state }}"
                    }
                },
            },
        ]
    }
    await async_setup_component(hass, "sensor", config)
    await async_setup_compensation(hass, TEST_CONFIG)

    hass.states.async_set("sensor.test_state", 4)

    await hass.async_block_till_done()
    state = hass.states.get(TEST_SOURCE)
    expect(state.state).to_equal("4")

    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal("5.0")

    # Force Template Reload
    yaml_path = get_fixture_path("sensor_configuration.yaml", "template")
    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            "template",
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    # Template state gets to None
    state = hass.states.get(TEST_SOURCE)
    expect(state is None).to_be(True)

    # Filter sensor ignores None state setting state to STATE_UNKNOWN
    state = hass.states.get(TEST_ENTITY_ID)
    expect(state.state).to_equal(STATE_UNKNOWN)
