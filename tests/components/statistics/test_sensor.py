"""The test for the statistics sensor platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import ATTR_STATE_CLASS, SensorStateClass
from homeassistant.components.statistics import DOMAIN
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import recorder_mock

from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)

VALUES_BINARY = ["on", "off", "on", "off", "on", "off", "on", "off", "on"]
VALUES_NUMERIC = [17, 20, 15.2, 5, 3.8, 9.2, 6.7, 14, 6]


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: object = Depends(recorder_mock),
) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test configuration defined unique_id."""
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test",
                        "unique_id": "uniqueid_sensor_test",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "sampling_size": 20,
                    },
                ]
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    entity_id = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, "uniqueid_sensor_test"
    )
    expect(entity_id).to_equal("sensor.test")


@test
async def sensor_defaults_numeric(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the general behavior of the sensor, with numeric source sensor."""
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "sampling_size": 20,
                    },
                ]
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    assert state is not None
    expect(state.state).to_equal(
        str(round(sum(VALUES_NUMERIC) / len(VALUES_NUMERIC), 2))
    )
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_be(
        UnitOfTemperature.CELSIUS
    )
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_be(SensorStateClass.MEASUREMENT)
    expect(state.attributes.get("buffer_usage_ratio")).to_equal(round(9 / 20, 2))
    expect(state.attributes.get("source_value_valid")).to_be(True)
    assert "age_coverage_ratio" not in state.attributes

    hass.states.async_set("sensor.test_monitored", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    new_state = hass.states.get("sensor.test")
    assert new_state is not None
    expect(new_state.state).to_equal(STATE_UNAVAILABLE)
    expect(new_state.attributes.get("source_value_valid")).to_be(None)
    hass.states.async_set(
        "sensor.test_monitored",
        "0",
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()
    new_state = hass.states.get("sensor.test")
    new_mean = round(sum(VALUES_NUMERIC) / (len(VALUES_NUMERIC) + 1), 2)
    assert new_state is not None
    expect(new_state.state).to_equal(str(new_mean))
    expect(new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfTemperature.CELSIUS
    )
    expect(new_state.attributes.get("buffer_usage_ratio")).to_equal(round(10 / 20, 2))
    expect(new_state.attributes.get("source_value_valid")).to_be(True)

    hass.states.async_set("sensor.test_monitored", "beer", {})
    await hass.async_block_till_done()
    new_state = hass.states.get("sensor.test")
    assert new_state is not None
    expect(new_state.state).to_equal(str(new_mean))
    expect(new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfTemperature.CELSIUS
    )
    expect(new_state.attributes.get("source_value_valid")).to_be(False)

    hass.states.async_set("sensor.test_monitored", STATE_UNKNOWN, {})
    await hass.async_block_till_done()
    new_state = hass.states.get("sensor.test")
    assert new_state is not None
    expect(new_state.state).to_equal(str(new_mean))
    expect(new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfTemperature.CELSIUS
    )
    expect(new_state.attributes.get("source_value_valid")).to_be(False)

    hass.states.async_remove("sensor.test_monitored")
    await hass.async_block_till_done()
    new_state = hass.states.get("sensor.test")
    assert new_state is not None
    expect(new_state.state).to_equal(str(new_mean))
    expect(new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfTemperature.CELSIUS
    )
    expect(new_state.attributes.get("source_value_valid")).to_be(False)


@test
async def sensor_defaults_binary(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the general behavior of the sensor, with binary source sensor."""
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test",
                        "entity_id": "binary_sensor.test_monitored",
                        "state_characteristic": "count",
                        "sampling_size": 20,
                    },
                ]
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    for value in VALUES_BINARY:
        hass.states.async_set(
            "binary_sensor.test_monitored",
            value,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    assert state is not None
    expect(state.state).to_equal(str(len(VALUES_BINARY)))
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_be(None)
    expect(state.attributes.get(ATTR_STATE_CLASS)).to_be(SensorStateClass.MEASUREMENT)
    expect(state.attributes.get("buffer_usage_ratio")).to_equal(round(9 / 20, 2))
    expect(state.attributes.get("source_value_valid")).to_be(True)
    assert "age_coverage_ratio" not in state.attributes


@test
async def sampling_boundaries_given(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if either sampling_size or max_age are given."""
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test_boundaries_none",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                    },
                    {
                        "platform": "statistics",
                        "name": "test_boundaries_size",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "sampling_size": 20,
                    },
                    {
                        "platform": "statistics",
                        "name": "test_boundaries_age",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "max_age": {"minutes": 4},
                    },
                    {
                        "platform": "statistics",
                        "name": "test_boundaries_both",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "sampling_size": 20,
                        "max_age": {"minutes": 4},
                    },
                ]
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set(
        "sensor.test_monitored",
        str(VALUES_NUMERIC[0]),
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()

    assert hass.states.get("sensor.test_boundaries_none") is None
    assert hass.states.get("sensor.test_boundaries_size") is not None
    assert hass.states.get("sensor.test_boundaries_age") is not None
    assert hass.states.get("sensor.test_boundaries_both") is not None


@test
async def keep_last_value_given(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if either sampling_size or max_age are given with keep_last_sample."""
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test_none",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "keep_last_sample": True,
                    },
                    {
                        "platform": "statistics",
                        "name": "test_sampling_size",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "sampling_size": 20,
                        "keep_last_sample": True,
                    },
                    {
                        "platform": "statistics",
                        "name": "test_max_age",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "max_age": {"minutes": 4},
                        "keep_last_sample": True,
                    },
                    {
                        "platform": "statistics",
                        "name": "test_both",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "sampling_size": 20,
                        "max_age": {"minutes": 4},
                        "keep_last_sample": True,
                    },
                ]
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set(
        "sensor.test_monitored",
        str(VALUES_NUMERIC[0]),
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()

    assert hass.states.get("sensor.test_none") is None
    assert hass.states.get("sensor.test_sampling_size") is None
    assert hass.states.get("sensor.test_max_age") is not None
    assert hass.states.get("sensor.test_both") is not None


@test
async def sampling_size_reduced(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test limited buffer size."""
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "sampling_size": 5,
                    },
                ]
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    new_mean = round(sum(VALUES_NUMERIC[-5:]) / len(VALUES_NUMERIC[-5:]), 2)
    assert state is not None
    expect(state.state).to_equal(str(new_mean))
    expect(state.attributes.get("buffer_usage_ratio")).to_equal(round(5 / 5, 2))


@test
async def sampling_size_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test validity of stats requiring only one sample."""
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "sampling_size": 1,
                    },
                ]
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test")
    new_mean = float(VALUES_NUMERIC[-1])
    assert state is not None
    expect(state.state).to_equal(str(new_mean))
    expect(state.attributes.get("buffer_usage_ratio")).to_equal(round(1 / 1, 2))


@test
async def precision(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test correct results with precision set."""
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test_precision_0",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "sampling_size": 20,
                        "precision": 0,
                    },
                    {
                        "platform": "statistics",
                        "name": "test_precision_3",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "mean",
                        "sampling_size": 20,
                        "precision": 3,
                    },
                ]
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        )
    await hass.async_block_till_done()

    mean = sum(VALUES_NUMERIC) / len(VALUES_NUMERIC)
    state = hass.states.get("sensor.test_precision_0")
    assert state is not None
    expect(state.state).to_equal(str(int(round(mean, 0))))
    state = hass.states.get("sensor.test_precision_3")
    assert state is not None
    expect(state.state).to_equal(str(round(mean, 3)))


@test
async def percentile(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test correct results for percentile characteristic."""
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test_percentile_omitted",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "percentile",
                        "sampling_size": 20,
                    },
                    {
                        "platform": "statistics",
                        "name": "test_percentile_default",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "percentile",
                        "sampling_size": 20,
                        "percentile": 50,
                    },
                    {
                        "platform": "statistics",
                        "name": "test_percentile_min",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "percentile",
                        "sampling_size": 20,
                        "percentile": 1,
                    },
                ]
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_percentile_omitted")
    assert state is not None
    expect(state.state).to_equal(str(9.2))
    state = hass.states.get("sensor.test_percentile_default")
    assert state is not None
    expect(state.state).to_equal(str(9.2))
    state = hass.states.get("sensor.test_percentile_min")
    assert state is not None
    expect(state.state).to_equal(str(2.72))


@test
async def invalid_state_characteristic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the detection of wrong state_characteristics selected."""
    expect(
        await async_setup_component(
            hass,
            "sensor",
            {
                "sensor": [
                    {
                        "platform": "statistics",
                        "name": "test_numeric",
                        "entity_id": "sensor.test_monitored",
                        "state_characteristic": "invalid",
                        "sampling_size": 20,
                    },
                    {
                        "platform": "statistics",
                        "name": "test_binary",
                        "entity_id": "binary_sensor.test_monitored",
                        "state_characteristic": "variance",
                        "sampling_size": 20,
                    },
                ]
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set(
        "sensor.test_monitored",
        str(VALUES_NUMERIC[0]),
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    await hass.async_block_till_done()

    assert hass.states.get("sensor.test_numeric") is None
    assert hass.states.get("sensor.test_binary") is None


@test.skip("requires @pytest.mark.parametrize port")
async def sensor_loaded_from_config_entry() -> None:
    """Stub for test_sensor_loaded_from_config_entry (port deferred)."""


@test.skip("requires @pytest.mark.parametrize port")
async def sensor_state_updated_reported() -> None:
    """Stub for test_sensor_state_updated_reported (port deferred)."""


@test.skip("requires freezegun port")
async def age_limit_expiry() -> None:
    """Stub for test_age_limit_expiry (port deferred)."""


@test.skip("requires freezegun port")
async def age_limit_expiry_with_keep_last_sample() -> None:
    """Stub for test_age_limit_expiry_with_keep_last_sample (port deferred)."""


@test.skip("port deferred")
async def device_class() -> None:
    """Stub for test_device_class (port deferred)."""


@test.skip("port deferred")
async def state_class() -> None:
    """Stub for test_state_class (port deferred)."""


@test.skip("port deferred")
async def unitless_source_sensor() -> None:
    """Stub for test_unitless_source_sensor (port deferred)."""


@test.skip("port deferred")
async def state_characteristics() -> None:
    """Stub for test_state_characteristics (port deferred)."""


@test.skip("port deferred")
async def state_characteristic_mean_circular() -> None:
    """Stub for test_state_characteristic_mean_circular (port deferred)."""


@test.skip("requires get_fixture_path + recorder data")
async def initialize_from_database() -> None:
    """Stub for test_initialize_from_database (port deferred)."""


@test.skip("requires get_fixture_path + freezegun + recorder data")
async def initialize_from_database_with_maxage() -> None:
    """Stub for test_initialize_from_database_with_maxage (port deferred)."""


@test.skip("requires hass_config + recorder reload")
async def reload() -> None:
    """Stub for test_reload (port deferred)."""


@test.skip("requires @pytest.mark.parametrize port")
async def device_id() -> None:
    """Stub for test_device_id (port deferred)."""


@test.skip("requires recorder state injection")
async def update_before_load() -> None:
    """Stub for test_update_before_load (port deferred)."""


@test.skip("requires @pytest.mark.parametrize + freezegun port")
async def average_linear_unevenly_timed() -> None:
    """Stub for test_average_linear_unevenly_timed (port deferred)."""


@test.skip("port deferred")
async def sensor_unit_gets_removed() -> None:
    """Stub for test_sensor_unit_gets_removed (port deferred)."""


@test.skip("port deferred")
async def sensor_device_class_gets_removed() -> None:
    """Stub for test_sensor_device_class_gets_removed (port deferred)."""


@test.skip("port deferred")
async def not_valid_device_class() -> None:
    """Stub for test_not_valid_device_class (port deferred)."""


@test.skip("port deferred")
async def attributes_remains() -> None:
    """Stub for test_attributes_remains (port deferred)."""
