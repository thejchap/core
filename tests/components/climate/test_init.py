"""The tests for the climate component."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, Mock

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import (
    DOMAIN,
    SET_TEMPERATURE_SCHEMA,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_FAN_MODE,
    ATTR_HUMIDITY,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
    ATTR_PRESET_MODE,
    ATTR_SWING_HORIZONTAL_MODE,
    ATTR_SWING_MODE,
    ATTR_TARGET_HUMIDITY_STEP,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_SWING_HORIZONTAL_MODE,
    SERVICE_SET_SWING_MODE,
    SERVICE_SET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from ._fixtures import (
    MockClimateEntity,
    MockClimateEntityTestMethods,
    setup_test_integration,
)

from tests.common import async_mock_service
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-level anchor for tryke fixture resolution."""
    return 0


@test
async def set_temp_schema_no_req(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the set temperature schema with missing required data."""
    domain = "climate"
    service = "test_set_temperature"
    schema = SET_TEMPERATURE_SCHEMA
    calls = async_mock_service(hass, domain, service, schema)

    data = {"hvac_mode": "off", "entity_id": ["climate.test_id"]}
    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(domain, service, data)
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(0)


@test
async def set_temp_schema(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the set temperature schema with ok required data."""
    domain = "climate"
    service = "test_set_temperature"
    schema = SET_TEMPERATURE_SCHEMA
    calls = async_mock_service(hass, domain, service, schema)

    data = {"temperature": 20.0, "hvac_mode": "heat", "entity_id": ["climate.test_id"]}
    await hass.services.async_call(domain, service, data)
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[-1].data).to_equal(data)


@test
async def sync_turn_on(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if async turn_on calls sync turn_on."""
    climate = MockClimateEntityTestMethods()
    climate.hass = hass

    climate.turn_on = MagicMock()
    await climate.async_turn_on()

    expect(climate.turn_on.called).to_be(True)


@test
async def sync_turn_off(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if async turn_off calls sync turn_off."""
    climate = MockClimateEntityTestMethods()
    climate.hass = hass

    climate.turn_off = MagicMock()
    await climate.async_turn_off()

    expect(climate.turn_off.called).to_be(True)


@test
async def temperature_features_is_valid(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test correct features for setting temperature."""

    class MockClimateTempEntity(MockClimateEntity):
        @property
        def supported_features(self) -> int:
            """Return supported features."""
            return ClimateEntityFeature.TARGET_TEMPERATURE_RANGE

    class MockClimateTempRangeEntity(MockClimateEntity):
        @property
        def supported_features(self) -> int:
            """Return supported features."""
            return ClimateEntityFeature.TARGET_TEMPERATURE

    climate_temp_entity = MockClimateTempEntity(
        name="test", entity_id="climate.test_temp"
    )
    climate_temp_range_entity = MockClimateTempRangeEntity(
        name="test", entity_id="climate.test_range"
    )

    await setup_test_integration(
        hass, entities=[climate_temp_entity, climate_temp_range_entity]
    )

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                "entity_id": "climate.test_temp",
                "temperature": 20,
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal(
        "missing_target_temperature_entity_feature"
    )

    raised = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                "entity_id": "climate.test_range",
                "target_temp_low": 20,
                "target_temp_high": 25,
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal(
        "missing_target_temperature_range_entity_feature"
    )


@test
async def mode_validation(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test mode validation for hvac_mode, fan, swing and preset."""
    climate_entity = MockClimateEntity(name="test", entity_id="climate.test")

    await setup_test_integration(hass, entities=[climate_entity])

    state = hass.states.get("climate.test")
    expect(state.state).to_equal("heat")
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal("home")
    expect(state.attributes.get(ATTR_FAN_MODE)).to_equal("auto")
    expect(state.attributes.get(ATTR_SWING_MODE)).to_equal("auto")
    expect(state.attributes.get(ATTR_SWING_HORIZONTAL_MODE)).to_equal("on")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            "entity_id": "climate.test",
            "preset_mode": "away",
        },
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_SWING_MODE,
        {
            "entity_id": "climate.test",
            "swing_mode": "off",
        },
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_SWING_HORIZONTAL_MODE,
        {
            "entity_id": "climate.test",
            "swing_horizontal_mode": "off",
        },
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_FAN_MODE,
        {
            "entity_id": "climate.test",
            "fan_mode": "off",
        },
        blocking=True,
    )
    state = hass.states.get("climate.test")
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal("away")
    expect(state.attributes.get(ATTR_FAN_MODE)).to_equal("off")
    expect(state.attributes.get(ATTR_SWING_MODE)).to_equal("off")
    expect(state.attributes.get(ATTR_SWING_HORIZONTAL_MODE)).to_equal("off")

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                "entity_id": "climate.test",
                "hvac_mode": "auto",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("not_valid_hvac_mode")

    raised = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {
                "entity_id": "climate.test",
                "preset_mode": "invalid",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("not_valid_preset_mode")

    raised = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_SWING_MODE,
            {
                "entity_id": "climate.test",
                "swing_mode": "invalid",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("not_valid_swing_mode")

    raised = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_SWING_HORIZONTAL_MODE,
            {
                "entity_id": "climate.test",
                "swing_horizontal_mode": "invalid",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("not_valid_horizontal_swing_mode")

    raised = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_FAN_MODE,
            {
                "entity_id": "climate.test",
                "fan_mode": "invalid",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("not_valid_fan_mode")


@test
async def turn_on_off_toggle(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test turn_on/turn_off/toggle methods."""

    class MockClimateEntityTest(MockClimateEntity):
        """Mock Climate device."""

        _attr_hvac_mode = HVACMode.OFF

        @property
        def hvac_mode(self) -> HVACMode:
            """Return hvac mode."""
            return self._attr_hvac_mode

        async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
            """Set new target hvac mode."""
            self._attr_hvac_mode = hvac_mode

    climate = MockClimateEntityTest()
    climate.hass = hass

    await climate.async_turn_on()
    expect(climate.hvac_mode).to_equal(HVACMode.HEAT)

    await climate.async_turn_off()
    expect(climate.hvac_mode).to_equal(HVACMode.OFF)

    await climate.async_toggle()
    expect(climate.hvac_mode).to_equal(HVACMode.HEAT)
    await climate.async_toggle()
    expect(climate.hvac_mode).to_equal(HVACMode.OFF)


@test
async def sync_toggle(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if async toggle calls sync toggle."""

    class MockClimateEntityTest(MockClimateEntity):
        """Mock Climate device."""

        _attr_supported_features = (
            ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
        )

        @property
        def hvac_mode(self) -> HVACMode:
            """Return hvac operation ie. heat, cool mode.

            Need to be one of HVACMode.*.
            """
            return HVACMode.HEAT

        @property
        def hvac_modes(self) -> list[HVACMode]:
            """Return the list of available hvac operation modes.

            Need to be a subset of HVAC_MODES.
            """
            return [HVACMode.OFF, HVACMode.HEAT]

        def turn_on(self) -> None:
            """Turn on."""

        def turn_off(self) -> None:
            """Turn off."""

        def toggle(self) -> None:
            """Toggle."""

    climate = MockClimateEntityTest()
    climate.hass = hass

    climate.toggle = Mock()
    await climate.async_toggle()

    expect(climate.toggle.called).to_be(True)


@test
async def humidity_validation(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test validation for humidity."""

    class MockClimateEntityHumidity(MockClimateEntity):
        """Mock climate class with mocked aux heater."""

        _attr_supported_features = ClimateEntityFeature.TARGET_HUMIDITY
        _attr_target_humidity = 50
        _attr_min_humidity = 50
        _attr_max_humidity = 60
        _attr_target_humidity_step = 5

        def set_humidity(self, humidity: int) -> None:
            """Set new target humidity."""
            self._attr_target_humidity = humidity

    test_climate = MockClimateEntityHumidity(
        name="Test",
        unique_id="unique_climate_test",
    )

    await setup_test_integration(hass, entities=[test_climate])

    state = hass.states.get("climate.test")
    expect(state.attributes.get(ATTR_HUMIDITY)).to_equal(50)
    expect(state.attributes.get(ATTR_TARGET_HUMIDITY_STEP)).to_equal(5)

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_HUMIDITY,
            {
                "entity_id": "climate.test",
                ATTR_HUMIDITY: "1",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("humidity_out_of_range")
    expect("Check valid humidity 1 in range 50 - 60" in caplog.text).to_be(True)

    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_HUMIDITY,
            {
                "entity_id": "climate.test",
                ATTR_HUMIDITY: "70",
            },
            blocking=True,
        )


@test
async def temperature_validation(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test validation for temperatures."""

    class MockClimateEntityTemp(MockClimateEntity):
        """Mock climate class with mocked aux heater."""

        _attr_supported_features = (
            ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.SWING_MODE
            | ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        )
        _attr_target_temperature = 15
        _attr_target_temperature_high = 18
        _attr_target_temperature_low = 10
        _attr_target_temperature_step = PRECISION_WHOLE

        def set_temperature(self, **kwargs: Any) -> None:
            """Set new target temperature."""
            if ATTR_TEMPERATURE in kwargs:
                self._attr_target_temperature = kwargs[ATTR_TEMPERATURE]
            if ATTR_TARGET_TEMP_HIGH in kwargs:
                self._attr_target_temperature_high = kwargs[ATTR_TARGET_TEMP_HIGH]
                self._attr_target_temperature_low = kwargs[ATTR_TARGET_TEMP_LOW]

    test_climate = MockClimateEntityTemp(
        name="Test",
        unique_id="unique_climate_test",
    )

    await setup_test_integration(hass, entities=[test_climate])

    state = hass.states.get("climate.test")
    expect(state.attributes.get(ATTR_CURRENT_TEMPERATURE)).to_be(None)
    expect(state.attributes.get(ATTR_MIN_TEMP)).to_equal(7)
    expect(state.attributes.get(ATTR_MAX_TEMP)).to_equal(35)

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                "entity_id": "climate.test",
                ATTR_TEMPERATURE: "40",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("temp_out_of_range")

    raised = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                "entity_id": "climate.test",
                ATTR_TARGET_TEMP_HIGH: "25",
                ATTR_TARGET_TEMP_LOW: "0",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("temp_out_of_range")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            "entity_id": "climate.test",
            ATTR_TARGET_TEMP_HIGH: "25",
            ATTR_TARGET_TEMP_LOW: "10",
        },
        blocking=True,
    )

    state = hass.states.get("climate.test")
    expect(state.attributes.get(ATTR_TARGET_TEMP_LOW)).to_equal(10)
    expect(state.attributes.get(ATTR_TARGET_TEMP_HIGH)).to_equal(25)


@test
async def target_temp_high_higher_than_low(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that target high is higher than target low."""

    class MockClimateEntityTemp(MockClimateEntity):
        """Mock climate class with mocked aux heater."""

        _attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        )
        _attr_current_temperature = 15
        _attr_target_temperature = 15
        _attr_target_temperature_high = 18
        _attr_target_temperature_low = 10
        _attr_target_temperature_step = PRECISION_WHOLE

        def set_temperature(self, **kwargs: Any) -> None:
            """Set new target temperature."""
            if ATTR_TEMPERATURE in kwargs:
                self._attr_target_temperature = kwargs[ATTR_TEMPERATURE]
            if ATTR_TARGET_TEMP_HIGH in kwargs:
                self._attr_target_temperature_high = kwargs[ATTR_TARGET_TEMP_HIGH]
                self._attr_target_temperature_low = kwargs[ATTR_TARGET_TEMP_LOW]

    test_climate = MockClimateEntityTemp(
        name="Test",
        unique_id="unique_climate_test",
    )

    await setup_test_integration(hass, entities=[test_climate])

    state = hass.states.get("climate.test")
    expect(state.attributes.get(ATTR_CURRENT_TEMPERATURE)).to_equal(15)
    expect(state.attributes.get(ATTR_MIN_TEMP)).to_equal(7)
    expect(state.attributes.get(ATTR_MAX_TEMP)).to_equal(35)

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                "entity_id": "climate.test",
                ATTR_TARGET_TEMP_HIGH: "15",
                ATTR_TARGET_TEMP_LOW: "20",
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("low_temp_higher_than_high_temp")
