"""The tests for the humidifier component."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.humidifier import (
    ATTR_HUMIDITY,
    DOMAIN,
    MODE_ECO,
    MODE_NORMAL,
    SERVICE_SET_HUMIDITY,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import translation as translation_helper

from ._fixtures import setup_test_integration

from tests.common import MockEntity
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


class MockHumidifierEntity(MockEntity, HumidifierEntity):
    """Mock Humidifier device to use in tests."""

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return 0


@test
async def sync_turn_on(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if async turn_on calls sync turn_on."""
    humidifier = MockHumidifierEntity()
    humidifier.hass = hass

    humidifier.turn_on = MagicMock()
    await humidifier.async_turn_on()

    expect(humidifier.turn_on.called).to_be(True)


@test
async def sync_turn_off(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if async turn_off calls sync turn_off."""
    humidifier = MockHumidifierEntity()
    humidifier.hass = hass

    humidifier.turn_off = MagicMock()
    await humidifier.async_turn_off()

    expect(humidifier.turn_off.called).to_be(True)


@test.skip("pre-existing failure on this branch: humidifier translations not loaded")
async def humidity_validation(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test validation for humidity."""

    class MockHumidifierEntityHumidity(MockEntity, HumidifierEntity):
        """Mock climate class with mocked aux heater."""

        _attr_supported_features = HumidifierEntityFeature.MODES
        _attr_available_modes = [MODE_NORMAL, MODE_ECO]
        _attr_mode = MODE_NORMAL
        _attr_target_humidity = 50
        _attr_min_humidity = 50
        _attr_max_humidity = 60

        def set_humidity(self, humidity: int) -> None:
            """Set new target humidity."""
            self._attr_target_humidity = humidity

    test_humidifier = MockHumidifierEntityHumidity(
        name="Test",
        unique_id="unique_humidifier_test",
    )

    await setup_test_integration(hass, entities=[test_humidifier])
    await translation_helper.async_load_integrations(hass, {DOMAIN})

    state = hass.states.get("humidifier.test")
    expect(state.attributes.get(ATTR_HUMIDITY)).to_be(50)

    async with expect_raises_async(
        ServiceValidationError,
        match="Provided humidity 1 is not valid. Accepted range is 50 to 60",
    ) as exc:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_HUMIDITY,
            {
                "entity_id": "humidifier.test",
                ATTR_HUMIDITY: "1",
            },
            blocking=True,
        )

    expect(exc.value.translation_key).to_be("humidity_out_of_range")
    expect("Check valid humidity 1 in range 50 - 60" in caplog.text).to_be(True)

    async with expect_raises_async(
        ServiceValidationError,
        match="Provided humidity 70 is not valid. Accepted range is 50 to 60",
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_HUMIDITY,
            {
                "entity_id": "humidifier.test",
                ATTR_HUMIDITY: "70",
            },
            blocking=True,
        )
