"""The tests for the water heater component."""

from collections.abc import Generator
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components.water_heater import (
    DOMAIN,
    SERVICE_SET_OPERATION_MODE,
    SET_TEMPERATURE_SCHEMA,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from tests.common import (
    MockConfigEntry,
    MockModule,
    MockPlatform,
    async_mock_service,
    mock_config_flow,
    mock_integration,
    mock_platform,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


class _MockFlow(ConfigFlow):
    """Test flow."""


@fixture
def config_flow_fixture(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Mock config flow."""
    mock_platform(hass, "test.config_flow")

    with mock_config_flow("test", _MockFlow):
        yield


@test
async def set_temp_schema_no_req(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the set temperature schema with missing required data."""
    domain = "climate"
    service = "test_set_temperature"
    schema = cv.make_entity_service_schema(SET_TEMPERATURE_SCHEMA)
    calls = async_mock_service(hass, domain, service, schema)

    data = {"hvac_mode": "off", "entity_id": ["climate.test_id"]}
    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(domain, service, data)
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(0)


@test
async def set_temp_schema(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the set temperature schema with ok required data."""
    domain = "water_heater"
    service = "test_set_temperature"
    schema = cv.make_entity_service_schema(SET_TEMPERATURE_SCHEMA)
    calls = async_mock_service(hass, domain, service, schema)

    data = {
        "temperature": 20.0,
        "operation_mode": "gas",
        "entity_id": ["water_heater.test_id"],
    }
    await hass.services.async_call(domain, service, data)
    await hass.async_block_till_done()

    expect(len(calls)).to_equal(1)
    expect(calls[-1].data).to_equal(data)


class MockWaterHeaterEntity(WaterHeaterEntity):
    """Mock water heater device to use in tests."""

    _attr_operation_list: list[str] | None = ["off", "heat_pump", "gas"]
    _attr_operation = "heat_pump"
    _attr_supported_features = WaterHeaterEntityFeature.ON_OFF
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    set_operation_mode: MagicMock = MagicMock()


@test
async def sync_turn_on(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if async turn_on calls sync turn_on."""
    water_heater = MockWaterHeaterEntity()
    water_heater.hass = hass

    setattr(water_heater, "turn_on", MagicMock())
    await water_heater.async_turn_on()

    expect(water_heater.turn_on.call_count).to_equal(1)

    setattr(water_heater, "async_turn_on", AsyncMock())
    await water_heater.async_turn_on()

    expect(water_heater.async_turn_on.call_count).to_equal(1)


@test
async def sync_turn_off(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if async turn_off calls sync turn_off."""
    water_heater = MockWaterHeaterEntity()
    water_heater.hass = hass

    setattr(water_heater, "turn_off", MagicMock())
    await water_heater.async_turn_off()

    expect(water_heater.turn_off.call_count).to_equal(1)

    setattr(water_heater, "async_turn_off", AsyncMock())
    await water_heater.async_turn_off()

    expect(water_heater.async_turn_off.call_count).to_equal(1)


@test
async def operation_mode_validation(
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture),
) -> None:
    """Test operation mode validation."""
    water_heater_entity = MockWaterHeaterEntity()
    water_heater_entity.hass = hass
    water_heater_entity._attr_name = "test"
    water_heater_entity._attr_unique_id = "test"
    water_heater_entity._attr_supported_features = (
        WaterHeaterEntityFeature.OPERATION_MODE
    )
    water_heater_entity._attr_current_operation = None
    water_heater_entity._attr_operation_list = None

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.WATER_HEATER]
        )
        return True

    async def async_setup_entry_water_heater_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test water_heater platform via config entry."""
        async_add_entities([water_heater_entity])

    mock_integration(
        hass,
        MockModule(
            "test",
            async_setup_entry=async_setup_entry_init,
        ),
        built_in=False,
    )
    mock_platform(
        hass,
        "test.water_heater",
        MockPlatform(async_setup_entry=async_setup_entry_water_heater_platform),
    )

    config_entry = MockConfigEntry(domain="test")
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_equal(True)

    data = {"entity_id": "water_heater.test", "operation_mode": "test"}

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_OPERATION_MODE, data, blocking=True
        )
    except ServiceValidationError as exc:
        raised = exc
    expect(raised is not None).to_equal(True)
    assert raised is not None
    expect(str(raised)).to_equal(
        "Operation mode test is not valid for water_heater.test. "
        "The operation list is not defined"
    )
    expect(raised.translation_domain).to_equal(DOMAIN)
    expect(raised.translation_key).to_equal("operation_list_not_defined")
    expect(raised.translation_placeholders).to_equal(
        {
            "entity_id": "water_heater.test",
            "operation_mode": "test",
        }
    )

    water_heater_entity._attr_operation_list = ["gas", "eco"]
    raised2: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN, SERVICE_SET_OPERATION_MODE, data, blocking=True
        )
    except ServiceValidationError as exc:
        raised2 = exc
    expect(raised2 is not None).to_equal(True)
    assert raised2 is not None
    expect(str(raised2)).to_equal(
        "Operation mode test is not valid for water_heater.test. "
        "Valid operation modes are: gas, eco"
    )
    expect(raised2.translation_domain).to_equal(DOMAIN)
    expect(raised2.translation_key).to_equal("not_valid_operation_mode")
    expect(raised2.translation_placeholders).to_equal(
        {
            "entity_id": "water_heater.test",
            "operation_mode": "test",
            "operation_list": "gas, eco",
        }
    )

    data = {"entity_id": "water_heater.test", "operation_mode": "eco"}
    await hass.services.async_call(
        DOMAIN, SERVICE_SET_OPERATION_MODE, data, blocking=True
    )
    await hass.async_block_till_done()
    water_heater_entity.set_operation_mode.assert_has_calls([mock.call("eco")])
