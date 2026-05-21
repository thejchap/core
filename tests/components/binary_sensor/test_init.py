"""The tests for the Binary sensor component."""

from collections.abc import Generator
from unittest import mock

from tryke import Depends, expect, fixture, test

from homeassistant.components import binary_sensor
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import STATE_OFF, STATE_ON, EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .common import MockBinarySensor

from tests.common import (
    MockConfigEntry,
    MockModule,
    MockPlatform,
    mock_config_flow,
    mock_integration,
    mock_platform,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)

TEST_DOMAIN = "test"


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> int:
    return 0


class MockFlow(ConfigFlow):
    """Test flow."""


@fixture
def config_flow_fixture(hass: HomeAssistant = Depends(hass_fixture)) -> Generator[None]:
    """Mock config flow."""
    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")

    with mock_config_flow(TEST_DOMAIN, MockFlow):
        yield


@test
async def state(_executor: int = Depends(_trigger_executor)) -> None:
    """Test binary sensor state."""
    sensor = binary_sensor.BinarySensorEntity()
    expect(sensor.state).to_be_none()
    with mock.patch(
        "homeassistant.components.binary_sensor.BinarySensorEntity.is_on",
        new=False,
    ):
        expect(binary_sensor.BinarySensorEntity().state).to_equal(STATE_OFF)
    with mock.patch(
        "homeassistant.components.binary_sensor.BinarySensorEntity.is_on",
        new=True,
    ):
        expect(binary_sensor.BinarySensorEntity().state).to_equal(STATE_ON)


@test
async def name(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture),
) -> None:
    """Test binary sensor name."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.BINARY_SENSOR]
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

    # Unnamed binary sensor without device class -> no name
    entity1 = binary_sensor.BinarySensorEntity()
    entity1.entity_id = "binary_sensor.test1"

    # Unnamed binary sensor with device class but has_entity_name False -> no name
    entity2 = binary_sensor.BinarySensorEntity()
    entity2.entity_id = "binary_sensor.test2"
    entity2._attr_device_class = binary_sensor.BinarySensorDeviceClass.BATTERY

    # Unnamed binary sensor with device class and has_entity_name True -> named
    entity3 = binary_sensor.BinarySensorEntity()
    entity3.entity_id = "binary_sensor.test3"
    entity3._attr_device_class = binary_sensor.BinarySensorDeviceClass.BATTERY
    entity3._attr_has_entity_name = True

    # Unnamed binary sensor with device class and has_entity_name True -> named
    entity4 = binary_sensor.BinarySensorEntity()
    entity4.entity_id = "binary_sensor.test4"
    entity4.entity_description = binary_sensor.BinarySensorEntityDescription(
        "test",
        binary_sensor.BinarySensorDeviceClass.BATTERY,
        has_entity_name=True,
    )

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test binary_sensor platform via config entry."""
        async_add_entities([entity1, entity2, entity3, entity4])

    mock_platform(
        hass,
        f"{TEST_DOMAIN}.{binary_sensor.DOMAIN}",
        MockPlatform(async_setup_entry=async_setup_entry_platform),
    )

    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get(entity1.entity_id)
    expect(state.attributes).to_equal({})

    state = hass.states.get(entity2.entity_id)
    expect(state.attributes).to_equal({"device_class": "battery"})

    state = hass.states.get(entity3.entity_id)
    expect(state.attributes).to_equal(
        {"device_class": "battery", "friendly_name": "Battery"}
    )

    state = hass.states.get(entity4.entity_id)
    expect(state.attributes).to_equal(
        {"device_class": "battery", "friendly_name": "Battery"}
    )


@test
async def entity_category_config_raises_error(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    _config_flow: None = Depends(config_flow_fixture),
) -> None:
    """Test error is raised when entity category is set to config."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.BINARY_SENSOR]
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

    description1 = binary_sensor.BinarySensorEntityDescription(
        "diagnostic", entity_category=EntityCategory.DIAGNOSTIC
    )
    entity1 = MockBinarySensor()
    entity1.entity_description = description1
    entity1.entity_id = "binary_sensor.test1"

    description2 = binary_sensor.BinarySensorEntityDescription(
        "config", entity_category=EntityCategory.CONFIG
    )
    entity2 = MockBinarySensor()
    entity2.entity_description = description2
    entity2.entity_id = "binary_sensor.test2"

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test binary_sensor platform via config entry."""
        async_add_entities([entity1, entity2])

    mock_platform(
        hass,
        f"{TEST_DOMAIN}.{binary_sensor.DOMAIN}",
        MockPlatform(async_setup_entry=async_setup_entry_platform),
    )

    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    state1 = hass.states.get("binary_sensor.test1")
    expect(state1).not_.to_be_none()
    state2 = hass.states.get("binary_sensor.test2")
    expect(state2).to_be_none()
    expect(
        "Entity binary_sensor.test2 cannot be added as the entity category is set to config"
        in caplog.text
    ).to_be_truthy()
