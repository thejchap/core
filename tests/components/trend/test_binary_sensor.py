"""The test for the Trend sensor platform."""

from datetime import timedelta
import logging
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant import setup
from homeassistant.components.trend.const import DOMAIN
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import (
    ComponentSetup,
    config_entry as config_entry_fixture,
    setup_component as setup_component_fixture,
)

from tests.common import MockConfigEntry, assert_setup_component, mock_restore_cache
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
)


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


async def _setup_legacy_component(hass: HomeAssistant, params: dict[str, Any]) -> None:
    """Set up the trend component the legacy way."""
    assert await async_setup_component(
        hass,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "trend",
                "sensors": {
                    "test_trend_sensor": params,
                },
            }
        },
    )
    await hass.async_block_till_done()


@test.cases(
    test.case("up", states=["1", "2"], inverted=False, expected_state=STATE_ON),
    test.case("down", states=["2", "1"], inverted=False, expected_state=STATE_OFF),
    test.case("up_inverted", states=["1", "2"], inverted=True, expected_state=STATE_OFF),
    test.case("down_inverted", states=["2", "1"], inverted=True, expected_state=STATE_ON),
)
async def basic_trend_setup_from_yaml(
    states: list[str],
    inverted: bool,
    expected_state: str,
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test trend with a basic setup."""
    await _setup_legacy_component(
        hass,
        {
            "friendly_name": "Test state",
            "entity_id": "sensor.cpu_temp",
            "invert": inverted,
            "max_samples": 2.0,
            "min_gradient": 0.0,
            "sample_duration": 0.0,
        },
    )

    for state in states:
        hass.states.async_set("sensor.cpu_temp", state)
        await hass.async_block_till_done()

    sensor_state = hass.states.get("binary_sensor.test_trend_sensor")
    expect(sensor_state).to_be_truthy()
    expect(sensor_state.state).to_equal(expected_state)

    entity_entry = entity_registry.async_get("binary_sensor.test_trend_sensor")
    expect(entity_entry).to_be_none()


@test
async def trend_setup_from_yaml_with_unique_id(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test trend setup from YAML with unique_id."""
    await _setup_legacy_component(
        hass,
        {
            "friendly_name": "Test state with ID",
            "entity_id": "sensor.cpu_temp",
            "unique_id": "my_unique_trend_sensor",
            "max_samples": 2.0,
            "min_gradient": 0.0,
            "sample_duration": 0.0,
        },
    )

    hass.states.async_set("sensor.cpu_temp", "1")
    await hass.async_block_till_done()
    hass.states.async_set("sensor.cpu_temp", "2")
    await hass.async_block_till_done()

    sensor_state = hass.states.get("binary_sensor.test_trend_sensor")
    expect(sensor_state).to_be_truthy()
    expect(sensor_state.state).to_equal(STATE_ON)

    entity_entry = entity_registry.async_get("binary_sensor.test_trend_sensor")
    expect(entity_entry).to_be_truthy()
    expect(entity_entry.unique_id).to_equal("my_unique_trend_sensor")


@test.cases(
    test.case("up", states=["1", "2"], inverted=False, expected_state=STATE_ON),
    test.case("down", states=["2", "1"], inverted=False, expected_state=STATE_OFF),
    test.case("up_inverted", states=["1", "2"], inverted=True, expected_state=STATE_OFF),
    test.case("down_inverted", states=["2", "1"], inverted=True, expected_state=STATE_ON),
)
async def basic_trend(
    states: list[str],
    inverted: bool,
    expected_state: str,
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fixture),
) -> None:
    """Test trend with a basic setup."""
    await setup_component(
        {
            "invert": inverted,
        },
    )

    for state in states:
        hass.states.async_set("sensor.test_state", state)
        await hass.async_block_till_done()

    sensor_state = hass.states.get("binary_sensor.test_trend_sensor")
    expect(sensor_state).to_be_truthy()
    expect(sensor_state.state).to_equal(expected_state)


@test.cases(
    test.case(
        "up",
        state_series=[[10, 0, 20, 30], [100], [0, 30, 1, 0]],
        inverted=False,
        expected_states=[STATE_UNKNOWN, STATE_ON, STATE_OFF],
    ),
    test.case(
        "up_inverted",
        state_series=[[10, 0, 20, 30], [100], [0, 30, 1, 0]],
        inverted=True,
        expected_states=[STATE_UNKNOWN, STATE_OFF, STATE_ON],
    ),
    test.case(
        "down",
        state_series=[[30, 20, 30, 10], [5], [30, 0, 45, 60]],
        inverted=True,
        expected_states=[STATE_UNKNOWN, STATE_ON, STATE_OFF],
    ),
)
async def using_trendline(
    state_series: list[list[Any]],
    inverted: bool,
    expected_states: list[str],
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fixture),
) -> None:
    """Test uptrend using multiple samples and trendline calculation."""
    await setup_component(
        {
            "sample_duration": 10000,
            "min_gradient": 1,
            "max_samples": 25,
            "min_samples": 5,
            "invert": inverted,
        },
    )

    for idx, states in enumerate(state_series):
        for state in states:
            freezer.tick(timedelta(seconds=2))
            hass.states.async_set("sensor.test_state", state)
            await hass.async_block_till_done()

        sensor_state = hass.states.get("binary_sensor.test_trend_sensor")
        expect(sensor_state).to_be_truthy()
        expect(sensor_state.state).to_equal(expected_states[idx])


@test.cases(
    test.case("up", attr_values=["1", "2"], expected_state=STATE_ON),
    test.case("down", attr_values=["2", "1"], expected_state=STATE_OFF),
)
async def attribute_trend(
    attr_values: list[str],
    expected_state: str,
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fixture),
) -> None:
    """Test attribute uptrend."""
    await setup_component(
        {
            "entity_id": "sensor.test_state",
            "attribute": "attr",
        },
    )

    for attr in attr_values:
        hass.states.async_set("sensor.test_state", "State", {"attr": attr})
        await hass.async_block_till_done()

    sensor_state = hass.states.get("binary_sensor.test_trend_sensor")
    expect(sensor_state).to_be_truthy()
    expect(sensor_state.state).to_equal(expected_state)


@test
async def max_samples(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fixture),
) -> None:
    """Test that sample count is limited correctly."""
    await setup_component(
        {
            "max_samples": 3,
            "min_gradient": -1,
        },
    )

    for val in (0, 1, 2, 3, 2, 1):
        hass.states.async_set("sensor.test_state", val)
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_trend_sensor")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("on")
    expect(state.attributes["sample_count"]).to_equal(3)


@test
async def non_numeric(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fixture),
) -> None:
    """Test for non-numeric sensor."""
    await setup_component({"entity_id": "sensor.test_state"})

    for val in ("Non", "Numeric"):
        hass.states.async_set("sensor.test_state", val)
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_trend_sensor")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def missing_attribute(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fixture),
) -> None:
    """Test for missing attribute."""
    await setup_component(
        {
            "attribute": "missing",
        },
    )

    for val in (1, 2):
        hass.states.async_set("sensor.test_state", "State", {"attr": val})
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_trend_sensor")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def invalid_name_does_not_create(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for invalid name."""
    with assert_setup_component(0):
        expect(
            await setup.async_setup_component(
                hass,
                "binary_sensor",
                {
                    "binary_sensor": {
                        "platform": "trend",
                        "sensors": {
                            "test INVALID sensor": {"entity_id": "sensor.test_state"}
                        },
                    }
                },
            )
        ).to_be_truthy()
    expect(hass.states.async_all("binary_sensor")).to_equal([])


@test
async def invalid_sensor_does_not_create(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalid sensor."""
    with assert_setup_component(0):
        expect(
            await setup.async_setup_component(
                hass,
                "binary_sensor",
                {
                    "binary_sensor": {
                        "platform": "trend",
                        "sensors": {
                            "test_trend_sensor": {"not_entity_id": "sensor.test_state"}
                        },
                    }
                },
            )
        ).to_be_truthy()
    expect(hass.states.async_all("binary_sensor")).to_equal([])


@test
async def no_sensors_does_not_create(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test no sensors."""
    with assert_setup_component(0):
        expect(
            await setup.async_setup_component(
                hass, "binary_sensor", {"binary_sensor": {"platform": "trend"}}
            )
        ).to_be_truthy()
    expect(hass.states.async_all("binary_sensor")).to_equal([])


@test.cases(
    test.case("on", saved_state="on", restored_state="on"),
    test.case("off", saved_state="off", restored_state="off"),
    test.case("unknown", saved_state="unknown", restored_state="unknown"),
)
async def restore_state(
    saved_state: str,
    restored_state: str,
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fixture),
) -> None:
    """Test we restore the trend state."""
    mock_restore_cache(hass, (State("binary_sensor.test_trend_sensor", saved_state),))

    await setup_component(
        {
            "sample_duration": 10000,
            "min_gradient": 1,
            "max_samples": 25,
            "min_samples": 5,
        },
    )

    expect(hass.states.get("binary_sensor.test_trend_sensor").state).to_equal(
        restored_state
    )

    for val in (10, 20, 30, 40):
        freezer.tick(timedelta(seconds=2))
        hass.states.async_set("sensor.test_state", val)
        await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.test_trend_sensor").state).to_equal(
        restored_state
    )

    for val in (50, 60, 70, 80):
        freezer.tick(timedelta(seconds=2))
        hass.states.async_set("sensor.test_state", val)
        await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.test_trend_sensor").state).to_equal("on")


@test
async def invalid_min_sample(
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test if error is logged when min_sample is larger than max_samples."""
    with caplog.at_level(logging.ERROR):
        await _setup_legacy_component(
            hass,
            {
                "entity_id": "sensor.test_state",
                "max_samples": 25,
                "min_samples": 30,
            },
        )

    record = caplog.records[0]
    expect(record.levelname).to_equal("ERROR")
    expect(
        "Invalid config for 'binary_sensor' from integration 'trend': min_samples must "
        "be smaller than or equal to max_samples" in record.getMessage()
    ).to_be(True)


@test
async def device_id(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test for source entity device for Trend."""
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
    expect(entity_registry.async_get("sensor.test_source")).to_be_truthy()

    trend_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "Trend",
            "entity_id": "sensor.test_source",
            "invert": False,
        },
        title="Trend",
    )
    trend_config_entry.add_to_hass(hass)

    expect(
        await hass.config_entries.async_setup(trend_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    trend_entity = entity_registry.async_get("binary_sensor.trend")
    expect(trend_entity).to_be_truthy()
    expect(trend_entity.device_id).to_equal(source_entity.device_id)


@test.cases(
    test.case("unknown", error_state=STATE_UNKNOWN),
    test.case("unavailable", error_state=STATE_UNAVAILABLE),
)
async def unavailable_source(
    error_state: str,
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fixture),
) -> None:
    """Test for unavailable source."""
    await setup_component(
        {
            "sample_duration": 10000,
            "min_gradient": 1,
            "max_samples": 25,
            "min_samples": 5,
        },
    )

    for val in (10, 20, 30, 40, 50, 60):
        freezer.tick(timedelta(seconds=2))
        hass.states.async_set("sensor.test_state", val)
        await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.test_trend_sensor").state).to_equal("on")

    hass.states.async_set("sensor.test_state", error_state)
    await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.test_trend_sensor").state).to_equal(
        STATE_UNAVAILABLE
    )

    hass.states.async_set("sensor.test_state", 50)
    await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.test_trend_sensor").state).to_equal("on")


@test
async def invalid_state_handling(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling of invalid states in trend sensor."""
    await setup_component(
        {
            "sample_duration": 10000,
            "min_gradient": 1,
            "max_samples": 25,
            "min_samples": 5,
        },
    )

    for val in (10, 20, 30, 40, 50, 60):
        freezer.tick(timedelta(seconds=2))
        hass.states.async_set("sensor.test_state", val)
        await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.test_trend_sensor").state).to_equal(STATE_ON)

    hass.states.async_set("sensor.test_state", "invalid")
    await hass.async_block_till_done()

    sensor_state = hass.states.get("binary_sensor.test_trend_sensor")
    expect(sensor_state).to_be_truthy()
    expect(sensor_state.state).to_equal(STATE_ON)

    expect(
        "Error processing sensor state change for entity_id=sensor.test_state, "
        "attribute=None, state=invalid: could not convert string to float: 'invalid'"
        in caplog.text
    ).to_be(True)

    hass.states.async_set("sensor.test_state", 50)
    await hass.async_block_till_done()

    sensor_state = hass.states.get("binary_sensor.test_trend_sensor")
    expect(sensor_state).to_be_truthy()
    expect(sensor_state.state).to_equal("on")
