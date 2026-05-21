"""The tests for the Number component (tryke port)."""

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from tryke import Depends, fixture, test

from homeassistant.components.number import (
    AMBIGUOUS_UNITS,
    ATTR_MAX,
    ATTR_MIN,
    ATTR_MODE,
    ATTR_STEP,
    ATTR_VALUE,
    DOMAIN,
    SERVICE_SET_VALUE,
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.components.number.const import (
    DEVICE_CLASS_UNITS as NUMBER_DEVICE_CLASS_UNITS,
)
from homeassistant.components.sensor import (
    DEVICE_CLASS_UNITS as SENSOR_DEVICE_CLASS_UNITS,
    NON_NUMERIC_DEVICE_CLASSES,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_PLATFORM,
    Platform,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import STORAGE_KEY as RESTORE_STATE_KEY
from homeassistant.setup import async_setup_component
from homeassistant.util.unit_system import METRIC_SYSTEM, US_CUSTOMARY_SYSTEM

from . import common

from tests.common import (
    MockConfigEntry,
    MockEntity,
    MockModule,
    MockPlatform,
    async_mock_restore_state_shutdown_restart,
    mock_config_flow,
    mock_integration,
    mock_platform,
    mock_restore_cache_with_extra_data,
    setup_test_component_platform,
)
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)

TEST_DOMAIN = "test"


@fixture
def _trigger_executor() -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_number_entities() -> list["common.MockNumberEntity"]:
    """Return a list of mock number entities."""
    return [
        common.MockNumberEntity(
            name="test",
            unique_id="unique_number",
            native_value=50.0,
        ),
    ]


class MockNumber(MockEntity, NumberEntity):
    """Mock NumberEntity class to test unit of measurement."""

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self._handle("device_class")

    @property
    def native_unit_of_measurement(self):
        """Return the native unit_of_measurement of this sensor."""
        return self._handle("native_unit_of_measurement")

    @property
    def native_value(self):
        """Return the native value of this sensor."""
        return self._handle("native_value")


class MockDefaultNumberEntity(NumberEntity):
    """Mock NumberEntity device to use in tests.

    This class falls back on defaults for min_value, max_value, step.
    """

    @property
    def native_value(self):
        """Return the current value."""
        return 0.5


class MockNumberEntity(NumberEntity):
    """Mock NumberEntity device to use in tests.

    This class customizes min_value, max_value as overridden methods.
    Step is calculated based on the smaller max_value and min_value.
    """

    @property
    def native_max_value(self) -> float:
        """Return the max value."""
        return 0.5

    @property
    def native_min_value(self) -> float:
        """Return the min value."""
        return -0.5

    @property
    def native_unit_of_measurement(self):
        """Return the current value."""
        return "native_cats"

    @property
    def native_value(self):
        """Return the current value."""
        return 0.5


class MockNumberEntityAttr(NumberEntity):
    """Mock NumberEntity device to use in tests.

    This class customizes min_value, max_value by setting _attr members.
    Step is calculated based on the smaller max_value and min_value.
    """

    _attr_native_max_value = 1000.0
    _attr_native_min_value = -1000.0
    _attr_native_step = 100.0
    _attr_native_unit_of_measurement = "native_dogs"
    _attr_native_value = 500.0


class MockNumberEntityDescr(NumberEntity):
    """Mock NumberEntity device to use in tests.

    This class customizes min_value, max_value by entity description.
    Step is calculated based on the smaller max_value and min_value.
    """

    def __init__(self) -> None:
        """Initialize the clas instance."""
        self.entity_description = NumberEntityDescription(
            "test",
            native_max_value=10.0,
            native_min_value=-10.0,
            native_step=2.0,
            native_unit_of_measurement="native_rabbits",
        )

    @property
    def native_value(self):
        """Return the current value."""
        return None


class MockNumberEntityAttrWithDescription(NumberEntity):
    """Mock NumberEntity device to use in tests.

    This class sets an entity description and overrides
    all the values with _attr members to ensure the _attr
    members take precedence over the entity description.
    """

    def __init__(self) -> None:
        """Initialize the clas instance."""
        self.entity_description = NumberEntityDescription(
            "test",
            native_max_value=10.0,
            native_min_value=-10.0,
            native_step=2.0,
            native_unit_of_measurement="native_rabbits",
        )

    _attr_native_max_value = 1000.0
    _attr_native_min_value = -1000.0
    _attr_native_step = 100.0
    _attr_native_unit_of_measurement = "native_dogs"
    _attr_native_value = 500.0


class MockDefaultNumberEntityDeprecated(NumberEntity):
    """Mock NumberEntity device to use in tests.

    This class falls back on defaults for min_value, max_value, step.
    """

    @property
    def native_value(self):
        """Return the current value."""
        return 0.5


class MockNumberEntityDeprecated(NumberEntity):
    """Mock NumberEntity device to use in tests.

    This class customizes min_value, max_value as overridden methods.
    Step is calculated based on the smaller max_value and min_value.
    """

    @property
    def max_value(self) -> float:
        """Return the max value."""
        return 0.5

    @property
    def min_value(self) -> float:
        """Return the min value."""
        return -0.5

    @property
    def unit_of_measurement(self):
        """Return the current value."""
        return "cats"

    @property
    def value(self):
        """Return the current value."""
        return 0.5


class MockNumberEntityAttrDeprecated(NumberEntity):
    """Mock NumberEntity device to use in tests.

    This class customizes min_value, max_value by setting _attr members.
    Step is calculated based on the smaller max_value and min_value.
    """

    _attr_max_value = 1000.0
    _attr_min_value = -1000.0
    _attr_step = 100.0
    _attr_unit_of_measurement = "dogs"
    _attr_value = 500.0


class MockNumberEntityDescrDeprecated(NumberEntity):
    """Mock NumberEntity device to use in tests.

    This class customizes min_value, max_value by entity description.
    Step is calculated based on the smaller max_value and min_value.
    """

    def __init__(self) -> None:
        """Initialize the clas instance."""
        self.entity_description = NumberEntityDescription(
            "test",
            max_value=10.0,
            min_value=-10.0,
            step=2.0,
            unit_of_measurement="rabbits",
        )

    @property
    def value(self):
        """Return the current value."""
        return 0.5


class MockFlow(ConfigFlow):
    """Test flow."""


@fixture
def config_flow_fixture(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Mock config flow."""
    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")

    with mock_config_flow(TEST_DOMAIN, MockFlow):
        yield


@test
async def step(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the step calculation."""
    number = MockDefaultNumberEntity()
    number.hass = hass
    assert number.step == 1.0

    number_2 = MockNumberEntity()
    number_2.hass = hass
    assert number_2.step == 0.1


@test
async def attributes(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the attributes."""
    number = MockDefaultNumberEntity()
    number.hass = hass
    assert number.max_value == 100.0
    assert number.min_value == 0.0
    assert number.step == 1.0
    assert number.unit_of_measurement is None
    assert number.value == 0.5
    assert number.capability_attributes == {
        ATTR_MAX: 100.0,
        ATTR_MIN: 0.0,
        ATTR_MODE: NumberMode.AUTO,
        ATTR_STEP: 1.0,
    }

    number_2 = MockNumberEntity()
    number_2.hass = hass
    assert number_2.max_value == 0.5
    assert number_2.min_value == -0.5
    assert number_2.step == 0.1
    assert number_2.unit_of_measurement == "native_cats"
    assert number_2.value == 0.5
    assert number_2.capability_attributes == {
        ATTR_MAX: 0.5,
        ATTR_MIN: -0.5,
        ATTR_MODE: NumberMode.AUTO,
        ATTR_STEP: 0.1,
    }

    number_3 = MockNumberEntityAttr()
    number_3.hass = hass
    assert number_3.max_value == 1000.0
    assert number_3.min_value == -1000.0
    assert number_3.step == 100.0
    assert number_3.unit_of_measurement == "native_dogs"
    assert number_3.value == 500.0
    assert number_3.capability_attributes == {
        ATTR_MAX: 1000.0,
        ATTR_MIN: -1000.0,
        ATTR_MODE: NumberMode.AUTO,
        ATTR_STEP: 100.0,
    }

    number_4 = MockNumberEntityDescr()
    number_4.hass = hass
    assert number_4.max_value == 10.0
    assert number_4.min_value == -10.0
    assert number_4.step == 2.0
    assert number_4.unit_of_measurement == "native_rabbits"
    assert number_4.value is None
    assert number_4.capability_attributes == {
        ATTR_MAX: 10.0,
        ATTR_MIN: -10.0,
        ATTR_MODE: NumberMode.AUTO,
        ATTR_STEP: 2.0,
    }

    number_5 = MockNumberEntityAttrWithDescription()
    number_5.hass = hass
    assert number_5.max_value == 1000.0
    assert number_5.min_value == -1000.0
    assert number_5.step == 100.0
    assert number_5.native_step == 100.0
    assert number_5.unit_of_measurement == "native_dogs"
    assert number_5.value == 500.0
    assert number_5.capability_attributes == {
        ATTR_MAX: 1000.0,
        ATTR_MIN: -1000.0,
        ATTR_MODE: NumberMode.AUTO,
        ATTR_STEP: 100.0,
    }


@test
async def sync_set_value(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if async set_value calls sync set_value."""
    number = MockDefaultNumberEntity()
    number.hass = hass

    number.set_value = MagicMock()
    await number.async_set_value(42)

    assert number.set_value.called
    assert number.set_value.call_args[0][0] == 42


@test
async def set_value(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_number_entities: list[common.MockNumberEntity] = Depends(mock_number_entities),
) -> None:
    """Test we can only set valid values."""
    setup_test_component_platform(hass, DOMAIN, mock_number_entities)

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    state = hass.states.get("number.test")
    assert state.state == "50.0"
    assert state.attributes.get(ATTR_STEP) == 1.0

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_VALUE: 60.0, ATTR_ENTITY_ID: "number.test"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("number.test")
    assert state.state == "60.0"

    # test range validation
    with pytest.raises(ServiceValidationError) as exc:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_VALUE: 110.0, ATTR_ENTITY_ID: "number.test"},
            blocking=True,
        )
    assert exc.value.translation_domain == DOMAIN
    assert exc.value.translation_key == "out_of_range"
    assert (
        str(exc.value)
        == "Value 110.0 for number.test is outside valid range 0.0 - 100.0"
    )

    await hass.async_block_till_done()
    state = hass.states.get("number.test")
    assert state.state == "60.0"


@test.cases(
    test.case(
        "us_fahrenheit",
        unit_system=US_CUSTOMARY_SYSTEM,
        native_unit=UnitOfTemperature.FAHRENHEIT,
        state_unit=UnitOfTemperature.FAHRENHEIT,
        initial_native_value=100,
        initial_state_value=100,
        updated_native_value=50,
        updated_state_value=50,
        native_max_value=140,
        state_max_value=140,
        native_min_value=-9,
        state_min_value=-9,
        native_step=3,
        state_step=3,
    ),
    test.case(
        "us_celsius_to_fahrenheit",
        unit_system=US_CUSTOMARY_SYSTEM,
        native_unit=UnitOfTemperature.CELSIUS,
        state_unit=UnitOfTemperature.FAHRENHEIT,
        initial_native_value=38,
        initial_state_value=100,
        updated_native_value=10,
        updated_state_value=50,
        native_max_value=60,
        state_max_value=140,
        native_min_value=-23,
        state_min_value=-10,
        native_step=3,
        state_step=3,
    ),
    test.case(
        "metric_fahrenheit_to_celsius",
        unit_system=METRIC_SYSTEM,
        native_unit=UnitOfTemperature.FAHRENHEIT,
        state_unit=UnitOfTemperature.CELSIUS,
        initial_native_value=100,
        initial_state_value=38,
        updated_native_value=50,
        updated_state_value=10,
        native_max_value=140,
        state_max_value=60,
        native_min_value=-9,
        state_min_value=-23,
        native_step=3,
        state_step=3,
    ),
    test.case(
        "metric_celsius",
        unit_system=METRIC_SYSTEM,
        native_unit=UnitOfTemperature.CELSIUS,
        state_unit=UnitOfTemperature.CELSIUS,
        initial_native_value=38,
        initial_state_value=38,
        updated_native_value=10,
        updated_state_value=10,
        native_max_value=60,
        state_max_value=60,
        native_min_value=-23,
        state_min_value=-23,
        native_step=3,
        state_step=3,
    ),
)
async def temperature_conversion(
    *,
    unit_system,
    native_unit,
    state_unit,
    initial_native_value,
    initial_state_value,
    updated_native_value,
    updated_state_value,
    native_max_value,
    state_max_value,
    native_min_value,
    state_min_value,
    native_step,
    state_step,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test temperature conversion."""
    hass.config.units = unit_system
    entity0 = common.MockNumberEntity(
        name="Test",
        native_max_value=native_max_value,
        native_min_value=native_min_value,
        native_step=native_step,
        native_unit_of_measurement=native_unit,
        native_value=initial_native_value,
        device_class=NumberDeviceClass.TEMPERATURE,
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(initial_state_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == state_unit
    assert state.attributes[ATTR_MAX] == state_max_value
    assert state.attributes[ATTR_MIN] == state_min_value
    assert state.attributes[ATTR_STEP] == state_step

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_VALUE: updated_state_value, ATTR_ENTITY_ID: entity0.entity_id},
        blocking=True,
    )

    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(updated_state_value))
    assert entity0._values["native_value"] == updated_native_value

    # Set to the minimum value
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_VALUE: state_min_value, ATTR_ENTITY_ID: entity0.entity_id},
        blocking=True,
    )

    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(state_min_value), rel=0.1)

    # Set to the maximum value
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_VALUE: state_max_value, ATTR_ENTITY_ID: entity0.entity_id},
        blocking=True,
    )

    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(state_max_value), rel=0.1)


RESTORE_DATA = {
    "native_max_value": 200.0,
    "native_min_value": -10.0,
    "native_step": 2.0,
    "native_unit_of_measurement": "°F",
    "native_value": 123.0,
}


@test
async def restore_number_save_state(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test RestoreNumber."""
    entity0 = common.MockRestoreNumber(
        name="Test",
        native_max_value=200.0,
        native_min_value=-10.0,
        native_step=2.0,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        native_value=123.0,
        device_class=NumberDeviceClass.TEMPERATURE,
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])

    assert await async_setup_component(hass, "number", {"number": {"platform": "test"}})
    await hass.async_block_till_done()

    # Trigger saving state
    await async_mock_restore_state_shutdown_restart(hass)

    assert len(hass_storage[RESTORE_STATE_KEY]["data"]) == 1
    state = hass_storage[RESTORE_STATE_KEY]["data"][0]["state"]
    assert state["entity_id"] == entity0.entity_id
    extra_data = hass_storage[RESTORE_STATE_KEY]["data"][0]["extra_data"]
    assert extra_data == RESTORE_DATA
    assert isinstance(extra_data["native_value"], float)


@test.cases(
    test.case(
        "full_restore",
        native_max_value=200.0,
        native_min_value=-10.0,
        native_step=2.0,
        native_value=123.0,
        native_value_type=float,
        extra_data=RESTORE_DATA,
        device_class=NumberDeviceClass.TEMPERATURE,
        uom="°F",
    ),
    test.case(
        "none_extra_data",
        native_max_value=100.0,
        native_min_value=0.0,
        native_step=None,
        native_value=None,
        native_value_type=type(None),
        extra_data=None,
        device_class=None,
        uom=None,
    ),
    test.case(
        "empty_extra_data",
        native_max_value=100.0,
        native_min_value=0.0,
        native_step=None,
        native_value=None,
        native_value_type=type(None),
        extra_data={},
        device_class=None,
        uom=None,
    ),
    test.case(
        "junk_extra_data",
        native_max_value=100.0,
        native_min_value=0.0,
        native_step=None,
        native_value=None,
        native_value_type=type(None),
        extra_data={"beer": 123},
        device_class=None,
        uom=None,
    ),
    test.case(
        "bad_native_value",
        native_max_value=100.0,
        native_min_value=0.0,
        native_step=None,
        native_value=None,
        native_value_type=type(None),
        extra_data={"native_unit_of_measurement": "°F", "native_value": {}},
        device_class=None,
        uom=None,
    ),
)
async def restore_number_restore_state(
    *,
    native_max_value,
    native_min_value,
    native_step,
    native_value,
    native_value_type,
    extra_data,
    device_class,
    uom,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test RestoreNumber."""
    mock_restore_cache_with_extra_data(hass, ((State("number.test", ""), extra_data),))

    entity0 = common.MockRestoreNumber(
        device_class=device_class,
        name="Test",
        native_value=None,
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])

    assert await async_setup_component(hass, "number", {"number": {"platform": "test"}})
    await hass.async_block_till_done()

    assert hass.states.get(entity0.entity_id)

    assert entity0.native_max_value == native_max_value
    assert entity0.native_min_value == native_min_value
    assert entity0.native_step == native_step
    assert entity0.native_value == native_value
    assert type(entity0.native_value) is native_value_type
    assert entity0.native_unit_of_measurement == uom


@test.cases(
    test.case(
        "temperature_unsupported_custom",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit=UnitOfTemperature.CELSIUS,
        custom_unit="my_temperature_unit",
        state_unit=UnitOfTemperature.CELSIUS,
        native_value=1000,
        custom_value=1000,
    ),
    test.case(
        "temperature_c_to_f",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit=UnitOfTemperature.CELSIUS,
        custom_unit=UnitOfTemperature.FAHRENHEIT,
        state_unit=UnitOfTemperature.FAHRENHEIT,
        native_value=37.5,
        custom_value=99.5,
    ),
    test.case(
        "temperature_f_to_c",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit=UnitOfTemperature.FAHRENHEIT,
        custom_unit=UnitOfTemperature.CELSIUS,
        state_unit=UnitOfTemperature.CELSIUS,
        native_value=100,
        custom_value=38.0,
    ),
    test.case(
        "volume_flow_l_to_gal",
        device_class=NumberDeviceClass.VOLUME_FLOW_RATE,
        native_unit=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        custom_unit=UnitOfVolumeFlowRate.GALLONS_PER_MINUTE,
        state_unit=UnitOfVolumeFlowRate.GALLONS_PER_MINUTE,
        native_value=50.0,
        custom_value="13.2",
    ),
    test.case(
        "volume_flow_gal_to_l",
        device_class=NumberDeviceClass.VOLUME_FLOW_RATE,
        native_unit=UnitOfVolumeFlowRate.GALLONS_PER_MINUTE,
        custom_unit=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        state_unit=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        native_value=13.0,
        custom_value="49.2",
    ),
)
async def custom_unit(
    *,
    device_class,
    native_unit,
    custom_unit,
    state_unit,
    native_value,
    custom_value,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test custom unit."""
    entry = entity_registry.async_get_or_create("number", "test", "very_unique")
    entity_registry.async_update_entity_options(
        entry.entity_id, "number", {"unit_of_measurement": custom_unit}
    )
    await hass.async_block_till_done()

    entity0 = common.MockNumberEntity(
        name="Test",
        native_value=native_value,
        native_unit_of_measurement=native_unit,
        device_class=device_class,
        unique_id="very_unique",
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])

    assert await async_setup_component(hass, "number", {"number": {"platform": "test"}})
    await hass.async_block_till_done()

    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(custom_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == state_unit


@test.cases(
    test.case(
        "c_to_f",
        native_unit=UnitOfTemperature.CELSIUS,
        custom_unit=UnitOfTemperature.FAHRENHEIT,
        used_custom_unit=UnitOfTemperature.FAHRENHEIT,
        default_unit=UnitOfTemperature.CELSIUS,
        native_value=37.5,
        custom_value=99.5,
        default_value=37.5,
    ),
    test.case(
        "f_default_c",
        native_unit=UnitOfTemperature.FAHRENHEIT,
        custom_unit=UnitOfTemperature.FAHRENHEIT,
        used_custom_unit=UnitOfTemperature.FAHRENHEIT,
        default_unit=UnitOfTemperature.CELSIUS,
        native_value=100,
        custom_value=100,
        default_value=38.0,
    ),
    test.case(
        "unsupported_unit_falls_back",
        native_unit=UnitOfTemperature.CELSIUS,
        custom_unit="no_unit",
        used_custom_unit=UnitOfTemperature.CELSIUS,
        default_unit=UnitOfTemperature.CELSIUS,
        native_value=1000,
        custom_value=1000,
        default_value=1000,
    ),
)
async def custom_unit_change(
    *,
    native_unit,
    custom_unit,
    used_custom_unit,
    default_unit,
    native_value,
    custom_value,
    default_value,
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test custom unit changes are picked up."""
    entity0 = common.MockNumberEntity(
        name="Test",
        native_value=native_value,
        native_unit_of_measurement=native_unit,
        device_class=NumberDeviceClass.TEMPERATURE,
        unique_id="very_unique",
    )
    setup_test_component_platform(hass, DOMAIN, [entity0])

    assert await async_setup_component(hass, "number", {"number": {"platform": "test"}})
    await hass.async_block_till_done()

    # Default unit conversion according to unit system
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(default_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == default_unit

    entity_registry.async_update_entity_options(
        "number.test", "number", {"unit_of_measurement": custom_unit}
    )
    await hass.async_block_till_done()

    # Unit conversion to the custom unit
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(custom_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == used_custom_unit

    entity_registry.async_update_entity_options(
        "number.test", "number", {"unit_of_measurement": native_unit}
    )
    await hass.async_block_till_done()

    # Unit conversion to another custom unit
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(native_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == native_unit

    entity_registry.async_update_entity_options("number.test", "number", None)
    await hass.async_block_till_done()

    # Default unit conversion according to unit system
    state = hass.states.get(entity0.entity_id)
    assert float(state.state) == pytest.approx(float(default_value))
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == default_unit


@test
async def translated_unit(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test translated unit."""

    with patch(
        "homeassistant.helpers.entity_platform.translation.async_get_translations",
        return_value={
            "component.test.entity.number.test_translation_key.unit_of_measurement": "Tests"
        },
    ):
        entity0 = common.MockNumberEntity(
            name="Test",
            native_value=123,
            unique_id="very_unique",
        )
        entity0.entity_description = NumberEntityDescription(
            "test",
            translation_key="test_translation_key",
        )
        setup_test_component_platform(hass, DOMAIN, [entity0])

        assert await async_setup_component(
            hass, "number", {"number": {"platform": "test"}}
        )
        await hass.async_block_till_done()

        entity_id = entity0.entity_id
        state = hass.states.get(entity_id)
        assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "Tests"


@test
async def translated_unit_with_native_unit_raises(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that translated unit."""

    with patch(
        "homeassistant.helpers.entity_platform.translation.async_get_translations",
        return_value={
            "component.test.entity.number.test_translation_key.unit_of_measurement": "Tests"
        },
    ):
        entity0 = common.MockNumberEntity(
            name="Test",
            native_value=123,
            unique_id="very_unique",
        )
        entity0.entity_description = NumberEntityDescription(
            "test",
            translation_key="test_translation_key",
            native_unit_of_measurement="bad_unit",
        )
        setup_test_component_platform(hass, DOMAIN, [entity0])

        assert await async_setup_component(
            hass, "number", {"number": {"platform": "test"}}
        )
        await hass.async_block_till_done()
        # Setup fails so entity_id is None
        assert entity0.entity_id is None


@test
async def ambiguous_unit_of_measurement_compat(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test ambiguous native_unit_of_measurement values are corrected."""
    entities = [
        MockNumber(
            name=f"Test_{idx}",
            native_value="0.0",
            native_unit_of_measurement=ambiguous_unit,
        )
        for idx, ambiguous_unit in enumerate(AMBIGUOUS_UNITS)
    ]
    setup_test_component_platform(hass, DOMAIN, entities)

    assert await async_setup_component(hass, "number", {"number": {"platform": "test"}})
    await hass.async_block_till_done()

    for entity, (_ambiguous_unit, normalized_unit) in zip(
        entities, AMBIGUOUS_UNITS.items(), strict=True
    ):
        state = hass.states.get(entity.entity_id)
        assert state is not None
        # Check compatible unit is applied
        assert state.state == "0.0"
        assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == normalized_unit


@test
def device_classes_aligned() -> None:
    """Make sure all sensor device classes are also available in NumberDeviceClass."""

    for device_class in SensorDeviceClass:
        if device_class in NON_NUMERIC_DEVICE_CLASSES:
            continue

        assert hasattr(NumberDeviceClass, device_class.name)
        assert getattr(NumberDeviceClass, device_class.name).value == device_class.value

    for device_class, unit in SENSOR_DEVICE_CLASS_UNITS.items():
        if device_class in NON_NUMERIC_DEVICE_CLASSES:
            continue
        assert unit == NUMBER_DEVICE_CLASS_UNITS[device_class]


@test
async def name(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture),
) -> None:
    """Test number name."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.NUMBER]
        )
        return True

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    mock_integration(
        hass,
        MockModule(
            TEST_DOMAIN,
            async_setup_entry=async_setup_entry_init,
        ),
    )

    # Unnamed number without device class -> no name
    entity1 = NumberEntity()
    entity1.entity_id = "number.test1"

    # Unnamed number with device class but has_entity_name False -> no name
    entity2 = NumberEntity()
    entity2.entity_id = "number.test2"
    entity2._attr_device_class = NumberDeviceClass.TEMPERATURE

    # Unnamed number with device class and has_entity_name True -> named
    entity3 = NumberEntity()
    entity3.entity_id = "number.test3"
    entity3._attr_device_class = NumberDeviceClass.TEMPERATURE
    entity3._attr_has_entity_name = True

    # Unnamed number with device class and has_entity_name True -> named
    entity4 = NumberEntity()
    entity4.entity_id = "number.test4"
    entity4.entity_description = NumberEntityDescription(
        "test",
        NumberDeviceClass.TEMPERATURE,
        has_entity_name=True,
    )

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test number platform via config entry."""
        async_add_entities([entity1, entity2, entity3, entity4])

    mock_platform(
        hass,
        f"{TEST_DOMAIN}.{DOMAIN}",
        MockPlatform(async_setup_entry=async_setup_entry_platform),
    )

    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity1.entity_id)
    assert state
    assert state.attributes == {
        "max": 100.0,
        "min": 0.0,
        "mode": NumberMode.AUTO,
        "step": 1.0,
    }

    state = hass.states.get(entity2.entity_id)
    assert state
    assert state.attributes == {
        "device_class": "temperature",
        "max": 100.0,
        "min": 0.0,
        "mode": NumberMode.AUTO,
        "step": 1.0,
    }

    state = hass.states.get(entity3.entity_id)
    assert state
    assert state.attributes == {
        "device_class": "temperature",
        "friendly_name": "Temperature",
        "max": 100.0,
        "min": 0.0,
        "mode": NumberMode.AUTO,
        "step": 1.0,
    }

    state = hass.states.get(entity4.entity_id)
    assert state
    assert state.attributes == {
        "device_class": "temperature",
        "friendly_name": "Temperature",
        "max": 100.0,
        "min": 0.0,
        "mode": NumberMode.AUTO,
        "step": 1.0,
    }


@test
def device_class_units(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test all numeric device classes have unit."""
    # DEVICE_CLASS_UNITS should include all device classes except:
    # - NumberDeviceClass.MONETARY
    # - Device classes enumerated in NON_NUMERIC_DEVICE_CLASSES
    assert set(NUMBER_DEVICE_CLASS_UNITS) == set(
        NumberDeviceClass
    ) - NON_NUMERIC_DEVICE_CLASSES - {NumberDeviceClass.MONETARY}
