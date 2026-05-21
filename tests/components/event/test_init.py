"""The tests for the event integration (tryke port)."""

from collections.abc import Generator
from typing import Any

from freezegun import freeze_time
import pytest
from tryke import Depends, fixture, test

from homeassistant import loader
from homeassistant.components.event import (
    ATTR_EVENT_TYPE,
    ATTR_EVENT_TYPES,
    DOMAIN,
    DoorbellEventType,
    EventDeviceClass,
    EventEntity,
    EventEntityDescription,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import CONF_PLATFORM, STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    AddEntitiesCallback,
)
from homeassistant.helpers.restore_state import STORAGE_KEY as RESTORE_STATE_KEY
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from .const import TEST_DOMAIN

from tests.common import (
    MockConfigEntry,
    MockEntity,
    MockModule,
    MockPlatform,
    async_mock_restore_state_shutdown_restart,
    mock_config_flow,
    mock_integration,
    mock_platform,
    mock_restore_cache,
    mock_restore_cache_with_extra_data,
    setup_test_component_platform,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)


@fixture
def _trigger_executor() -> int:
    """Opt into Tryke's HookExecutor path."""
    return 0


class MockEventEntity(MockEntity, EventEntity):
    """Mock EventEntity class."""

    @property
    def event_types(self) -> list[str]:
        """Return a list of possible events."""
        return self._handle("event_types")


@fixture
def enable_custom_integrations(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)
    yield


@fixture
def mock_event_platform(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Mock the event entity platform."""

    async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> None:
        """Set up test event platform."""
        async_add_entities(
            [
                MockEventEntity(
                    name="doorbell",
                    unique_id="unique_doorbell",
                    event_types=["short_press", "long_press"],
                ),
            ]
        )

    mock_platform(
        hass,
        f"{TEST_DOMAIN}.{DOMAIN}",
        MockPlatform(async_setup_platform=async_setup_platform),
    )


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
async def event(
    _executor: int = Depends(_trigger_executor),
) -> None:
    """Test the event entity."""
    event = EventEntity()
    event.entity_id = "event.doorbell"
    # Test event with no data at all
    assert event.state is None
    assert event.state_attributes == {ATTR_EVENT_TYPE: None}
    assert not event.extra_state_attributes
    assert event.device_class is None

    # No event types defined, should raise
    with pytest.raises(AttributeError):
        _ = event.event_types

    # Test retrieving data from entity description
    event.entity_description = EventEntityDescription(
        key="test_event",
        event_types=["short_press", "long_press"],
        device_class=EventDeviceClass.DOORBELL,
    )
    # Delete the cache since we changed the entity description at run time
    del event.device_class
    assert event.event_types == ["short_press", "long_press"]
    assert event.device_class == EventDeviceClass.DOORBELL

    # Test attrs win over entity description
    event._attr_event_types = ["short_press", "long_press", "double_press"]
    assert event.event_types == ["short_press", "long_press", "double_press"]
    event._attr_device_class = EventDeviceClass.BUTTON
    assert event.device_class == EventDeviceClass.BUTTON

    # Test triggering an event
    now = dt_util.utcnow()
    with freeze_time(now):
        event._trigger_event("long_press")

        assert event.state == now.isoformat(timespec="milliseconds")
        assert event.state_attributes == {ATTR_EVENT_TYPE: "long_press"}
        assert not event.extra_state_attributes

    # Test triggering an event, with extra attribute data
    now = dt_util.utcnow()
    with freeze_time(now):
        event._trigger_event("short_press", {"hello": "world"})

        assert event.state == now.isoformat(timespec="milliseconds")
        assert event.state_attributes == {
            ATTR_EVENT_TYPE: "short_press",
            "hello": "world",
        }

    # Test triggering an unknown event
    with pytest.raises(
        ValueError, match="^Invalid event type unknown_event for event.doorbell$"
    ):
        event._trigger_event("unknown_event")


@test
async def restore_state(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _custom: None = Depends(enable_custom_integrations),
    _platform: None = Depends(mock_event_platform),
) -> None:
    """Test we restore state integration."""
    mock_restore_cache_with_extra_data(
        hass,
        (
            (
                State(
                    "event.doorbell",
                    "2021-01-01T23:59:59.123+00:00",
                    attributes={
                        ATTR_EVENT_TYPE: "ignored",
                        ATTR_EVENT_TYPES: [
                            "single_press",
                            "double_press",
                            "do",
                            "not",
                            "restore",
                        ],
                        "hello": "worm",
                    },
                ),
                {
                    "last_event_type": "double_press",
                    "last_event_attributes": {
                        "hello": "world",
                    },
                },
            ),
        ),
    )

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    state = hass.states.get("event.doorbell")
    assert state
    assert state.state == "2021-01-01T23:59:59.123+00:00"
    assert state.attributes[ATTR_EVENT_TYPES] == ["short_press", "long_press"]
    assert state.attributes[ATTR_EVENT_TYPE] == "double_press"
    assert state.attributes["hello"] == "world"


@test
async def invalid_extra_restore_state(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _custom: None = Depends(enable_custom_integrations),
    _platform: None = Depends(mock_event_platform),
) -> None:
    """Test we restore state integration."""
    mock_restore_cache_with_extra_data(
        hass,
        (
            (
                State(
                    "event.doorbell",
                    "2021-01-01T23:59:59.123+00:00",
                ),
                {
                    "invalid_unexpected_key": "double_press",
                    "last_event_attributes": {
                        "hello": "world",
                    },
                },
            ),
        ),
    )

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    state = hass.states.get("event.doorbell")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_EVENT_TYPES] == ["short_press", "long_press"]
    assert state.attributes[ATTR_EVENT_TYPE] is None
    assert "hello" not in state.attributes


@test
async def no_extra_restore_state(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _custom: None = Depends(enable_custom_integrations),
    _platform: None = Depends(mock_event_platform),
) -> None:
    """Test we restore state integration."""
    mock_restore_cache(
        hass,
        (
            State(
                "event.doorbell",
                "2021-01-01T23:59:59.123+00:00",
                attributes={
                    ATTR_EVENT_TYPES: [
                        "single_press",
                        "double_press",
                    ],
                    ATTR_EVENT_TYPE: "double_press",
                    "hello": "world",
                },
            ),
        ),
    )

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    state = hass.states.get("event.doorbell")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_EVENT_TYPES] == ["short_press", "long_press"]
    assert state.attributes[ATTR_EVENT_TYPE] is None
    assert "hello" not in state.attributes


@test
async def saving_state(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    _custom: None = Depends(enable_custom_integrations),
    _platform: None = Depends(mock_event_platform),
) -> None:
    """Test we restore state integration."""
    restore_data = {"last_event_type": "double_press", "last_event_attributes": None}

    mock_restore_cache_with_extra_data(
        hass,
        (
            (
                State(
                    "event.doorbell",
                    "2021-01-01T23:59:59.123+00:00",
                ),
                restore_data,
            ),
        ),
    )

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    await async_mock_restore_state_shutdown_restart(hass)

    assert len(hass_storage[RESTORE_STATE_KEY]["data"]) == 1
    state = hass_storage[RESTORE_STATE_KEY]["data"][0]["state"]
    assert state["entity_id"] == "event.doorbell"
    extra_data = hass_storage[RESTORE_STATE_KEY]["data"][0]["extra_data"]
    assert extra_data == restore_data


@test
async def name(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _config_flow: None = Depends(config_flow_fixture),
) -> None:
    """Test event name."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.EVENT]
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

    # Unnamed event without device class -> no name
    entity1 = EventEntity()
    entity1._attr_event_types = ["ding"]
    entity1.entity_id = "event.test1"

    # Unnamed event with device class but has_entity_name False -> no name
    entity2 = EventEntity()
    entity2._attr_event_types = ["ding"]
    entity2.entity_id = "event.test2"
    entity2._attr_device_class = EventDeviceClass.DOORBELL

    # Unnamed event with device class and has_entity_name True -> named
    entity3 = EventEntity()
    entity3._attr_event_types = ["ding"]
    entity3.entity_id = "event.test3"
    entity3._attr_device_class = EventDeviceClass.DOORBELL
    entity3._attr_has_entity_name = True

    # Unnamed event with device class and has_entity_name True -> named
    entity4 = EventEntity()
    entity4._attr_event_types = ["ding"]
    entity4.entity_id = "event.test4"
    entity4.entity_description = EventEntityDescription(
        "test",
        EventDeviceClass.DOORBELL,
        has_entity_name=True,
    )

    async def async_setup_entry_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
    ) -> None:
        """Set up test event platform via config entry."""
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
    assert state.attributes == {"event_types": ["ding"], "event_type": None}

    state = hass.states.get(entity2.entity_id)
    assert state
    assert state.attributes == {
        "event_types": ["ding"],
        "event_type": None,
        "device_class": "doorbell",
    }

    state = hass.states.get(entity3.entity_id)
    assert state
    assert state.attributes == {
        "event_types": ["ding"],
        "event_type": None,
        "device_class": "doorbell",
        "friendly_name": "Doorbell",
    }

    state = hass.states.get(entity4.entity_id)
    assert state
    assert state.attributes == {
        "event_types": ["ding"],
        "event_type": None,
        "device_class": "doorbell",
        "friendly_name": "Doorbell",
    }


@test
async def doorbell_missing_ring_event_type(
    _executor: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    _config_flow: None = Depends(config_flow_fixture),
) -> None:
    """Test warning when a doorbell entity does not include the standard ring event type."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.EVENT]
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

    # Doorbell entity WITHOUT the standard "ring" event type
    entity_without_ring = EventEntity()
    entity_without_ring._attr_event_types = ["ding"]
    entity_without_ring._attr_device_class = EventDeviceClass.DOORBELL
    entity_without_ring._attr_has_entity_name = True
    entity_without_ring.entity_id = "event.doorbell_without_ring"

    # Doorbell entity WITH the standard "ring" event type
    entity_with_ring = EventEntity()
    entity_with_ring._attr_event_types = [DoorbellEventType.RING, "ding"]
    entity_with_ring._attr_device_class = EventDeviceClass.DOORBELL
    entity_with_ring._attr_has_entity_name = True
    entity_with_ring.entity_id = "event.doorbell_with_ring"

    # Non-doorbell entity should not warn
    entity_button = EventEntity()
    entity_button._attr_event_types = ["press"]
    entity_button._attr_device_class = EventDeviceClass.BUTTON
    entity_button._attr_has_entity_name = True
    entity_button.entity_id = "event.button"

    setup_test_component_platform(
        hass,
        DOMAIN,
        [entity_without_ring, entity_with_ring, entity_button],
        from_config_entry=True,
    )
    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    def get_error_message(entity_id: str) -> str:
        return (
            f"Entity {entity_id} is a doorbell event entity but does not support "
            "the 'ring' event type"
        )

    assert get_error_message("event.doorbell_without_ring") in caplog.text
    assert get_error_message("event.doorbell_with_ring") not in caplog.text
    assert get_error_message("event.button") not in caplog.text
