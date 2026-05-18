"""Test the UniFi Protect binary_sensor platform."""

from datetime import datetime, timedelta
from unittest.mock import Mock

from tryke import Depends, expect, fixture, test
from uiprotect.data import (
    AiPort,
    Camera,
    Event,
    EventType,
    Light,
    ModelType,
    MountType,
    Sensor,
    SmartDetectObjectType,
)
from uiprotect.data.nvr import EventMetadata

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.unifiprotect.binary_sensor import (
    CAMERA_SENSORS,
    EVENT_SENSORS,
    LIGHT_SENSORS,
    MOUNTABLE_SENSE_SENSORS,
    SENSE_SENSORS,
)
from homeassistant.components.unifiprotect.const import (
    ATTR_EVENT_SCORE,
    DEFAULT_ATTRIBUTION,
)
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_DEVICE_CLASS,
    EVENT_STATE_CHANGED,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    Platform,
)
from homeassistant.core import Event as HAEvent, EventStateChangedData, HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import (
    aiport as aiport_fixture,
    camera as camera_fixture,
    doorbell as doorbell_fixture,
    fixed_now as fixed_now_fixture,
    light as light_fixture,
    sensor as sensor_fixture,
    sensor_all as sensor_all_fixture,
    ufp as ufp_fixture,
    unadopted_camera as unadopted_camera_fixture,
)
from .utils import (
    MockUFPFixture,
    adopt_devices,
    assert_entity_counts,
    ids_from_device_description,
    init_entry,
    remove_entities,
)

from tests.common import async_capture_events
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)
from tests.hass_tryke_helpers import (
    entity_registry_enabled_by_default as entity_registry_enabled_by_default_fixture,
)

LIGHT_SENSOR_WRITE = LIGHT_SENSORS[:2]
SENSE_SENSORS_WRITE = SENSE_SENSORS[:3]


@fixture
def _trigger_executor() -> int:
    """Force tryke to build a per-module HookExecutor for this file."""
    return 0


@test
async def binary_sensor_camera_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
    unadopted_camera: Camera = Depends(unadopted_camera_fixture),
) -> None:
    """Test removing and re-adding a camera device."""

    ufp.api.bootstrap.nvr.system_info.ustorage = None
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 9, 6)
    await remove_entities(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 0, 0)
    await adopt_devices(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 9, 6)


@test
async def binary_sensor_light_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    light: Light = Depends(light_fixture),
) -> None:
    """Test removing and re-adding a light device."""

    ufp.api.bootstrap.nvr.system_info.ustorage = None
    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 2, 2)
    await remove_entities(hass, ufp, [light])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 0, 0)
    await adopt_devices(hass, ufp, [light])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 2, 2)


@test
async def binary_sensor_sensor_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    sensor_all: Sensor = Depends(sensor_all_fixture),
) -> None:
    """Test removing and re-adding a light device."""

    ufp.api.bootstrap.nvr.system_info.ustorage = None
    await init_entry(hass, ufp, [sensor_all])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 5, 5)
    await remove_entities(hass, ufp, [sensor_all])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 0, 0)
    await adopt_devices(hass, ufp, [sensor_all])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 5, 5)


@test
async def binary_sensor_setup_light(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    light: Light = Depends(light_fixture),
) -> None:
    """Test binary_sensor entity setup for light devices."""

    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 8, 8)

    for description in LIGHT_SENSOR_WRITE:
        unique_id, entity_id = await ids_from_device_description(
            hass, Platform.BINARY_SENSOR, light, description
        )

        entity = entity_registry.async_get(entity_id)
        expect(entity).not_.to_be(None)
        expect(entity.unique_id).to_equal(unique_id)

        state = hass.states.get(entity_id)
        expect(state).not_.to_be(None)
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def binary_sensor_setup_camera_all(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
    unadopted_camera: Camera = Depends(unadopted_camera_fixture),
) -> None:
    """Test binary_sensor entity setup for camera devices (all features)."""

    ufp.api.bootstrap.nvr.system_info.ustorage = None
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 9, 6)

    description = EVENT_SENSORS[0]
    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, doorbell, description
    )

    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)
    expect(entity.unique_id).to_equal(unique_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)

    # Is Dark
    description = CAMERA_SENSORS[0]
    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, doorbell, description
    )

    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)
    expect(entity.unique_id).to_equal(unique_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)

    # Motion
    description = EVENT_SENSORS[1]
    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, doorbell, description
    )

    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)
    expect(entity.unique_id).to_equal(unique_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def binary_sensor_setup_camera_none(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    camera: Camera = Depends(camera_fixture),
) -> None:
    """Test binary_sensor entity setup for camera devices (no features)."""

    ufp.api.bootstrap.nvr.system_info.ustorage = None
    await init_entry(hass, ufp, [camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 2, 2)

    description = CAMERA_SENSORS[0]

    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, camera, description
    )

    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)
    expect(entity.unique_id).to_equal(unique_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def binary_sensor_setup_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    sensor_all: Sensor = Depends(sensor_all_fixture),
) -> None:
    """Test binary_sensor entity setup for sensor devices."""

    await init_entry(hass, ufp, [sensor_all])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 11, 11)

    expected = [
        STATE_UNAVAILABLE,
        STATE_OFF,
        STATE_OFF,
        STATE_OFF,
    ]
    for index, description in enumerate(SENSE_SENSORS_WRITE):
        unique_id, entity_id = await ids_from_device_description(
            hass, Platform.BINARY_SENSOR, sensor_all, description
        )

        entity = entity_registry.async_get(entity_id)
        expect(entity).not_.to_be(None)
        expect(entity.unique_id).to_equal(unique_id)

        state = hass.states.get(entity_id)
        expect(state).not_.to_be(None)
        expect(state.state).to_equal(expected[index])
        expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def binary_sensor_setup_sensor_leak(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    sensor: Sensor = Depends(sensor_fixture),
) -> None:
    """Test binary_sensor entity setup for sensor with most leak mounting type."""

    sensor.mount_type = MountType.LEAK
    await init_entry(hass, ufp, [sensor])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 11, 11)

    expected = [
        STATE_OFF,
        STATE_OFF,
        STATE_UNAVAILABLE,
        STATE_OFF,
    ]
    for index, description in enumerate(SENSE_SENSORS_WRITE):
        unique_id, entity_id = await ids_from_device_description(
            hass, Platform.BINARY_SENSOR, sensor, description
        )

        entity = entity_registry.async_get(entity_id)
        expect(entity).not_.to_be(None)
        expect(entity.unique_id).to_equal(unique_id)

        state = hass.states.get(entity_id)
        expect(state).not_.to_be(None)
        expect(state.state).to_equal(expected[index])
        expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def binary_sensor_update_motion(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
    unadopted_camera: Camera = Depends(unadopted_camera_fixture),
    fixed_now: datetime = Depends(fixed_now_fixture),
) -> None:
    """Test binary_sensor motion entity."""

    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 15, 12)

    _, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, doorbell, EVENT_SENSORS[1]
    )

    event = Event(
        model=ModelType.EVENT,
        id="test_event_id",
        type=EventType.MOTION,
        start=fixed_now - timedelta(seconds=1),
        end=None,
        score=100,
        smart_detect_types=[],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_motion_detected = True
    new_camera.last_motion_event_id = event.id

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)
    expect(state.attributes[ATTR_EVENT_SCORE]).to_equal(100)


@test
async def binary_sensor_update_light_motion(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    light: Light = Depends(light_fixture),
    fixed_now: datetime = Depends(fixed_now_fixture),
) -> None:
    """Test binary_sensor motion entity."""

    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 8, 8)

    _, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, light, LIGHT_SENSOR_WRITE[1]
    )

    event_metadata = EventMetadata(light_id=light.id)
    event = Event(
        model=ModelType.EVENT,
        id="test_event_id",
        type=EventType.MOTION_LIGHT,
        start=fixed_now - timedelta(seconds=1),
        end=None,
        score=100,
        smart_detect_types=[],
        smart_detect_event_ids=[],
        metadata=event_metadata,
        api=ufp.api,
    )

    new_light = light.model_copy()
    new_light.is_pir_motion_detected = True
    new_light.last_motion_event_id = event.id

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event

    ufp.api.bootstrap.lights = {new_light.id: new_light}
    ufp.api.bootstrap.events = {event.id: event}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_ON)


@test
async def binary_sensor_update_mount_type_window(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    sensor_all: Sensor = Depends(sensor_all_fixture),
) -> None:
    """Test binary_sensor motion entity."""

    await init_entry(hass, ufp, [sensor_all])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 11, 11)

    _, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, sensor_all, MOUNTABLE_SENSE_SENSORS[0]
    )

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(
        BinarySensorDeviceClass.DOOR.value
    )

    new_sensor = sensor_all.model_copy()
    new_sensor.mount_type = MountType.WINDOW

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_sensor

    ufp.api.bootstrap.sensors = {new_sensor.id: new_sensor}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(
        BinarySensorDeviceClass.WINDOW.value
    )


@test
async def binary_sensor_update_mount_type_garage(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    sensor_all: Sensor = Depends(sensor_all_fixture),
) -> None:
    """Test binary_sensor motion entity."""

    await init_entry(hass, ufp, [sensor_all])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 11, 11)

    _, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, sensor_all, MOUNTABLE_SENSE_SENSORS[0]
    )

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(
        BinarySensorDeviceClass.DOOR.value
    )

    new_sensor = sensor_all.model_copy()
    new_sensor.mount_type = MountType.GARAGE

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_sensor

    ufp.api.bootstrap.sensors = {new_sensor.id: new_sensor}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.attributes[ATTR_DEVICE_CLASS]).to_equal(
        BinarySensorDeviceClass.GARAGE_DOOR.value
    )


@test
async def binary_sensor_package_detected(
    _trigger: int = Depends(_trigger_executor),
    _entity_registry_enabled: object = Depends(
        entity_registry_enabled_by_default_fixture
    ),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
    unadopted_camera: Camera = Depends(unadopted_camera_fixture),
    fixed_now: datetime = Depends(fixed_now_fixture),
) -> None:
    """Test binary_sensor package detection entity."""

    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 15, 15)

    doorbell.smart_detect_settings.object_types.append(SmartDetectObjectType.PACKAGE)

    _, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, doorbell, EVENT_SENSORS[6]
    )

    event = Event(
        model=ModelType.EVENT,
        id="test_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=1),
        end=None,
        score=100,
        smart_detect_types=[SmartDetectObjectType.PACKAGE],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.PACKAGE] = event.id

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)
    expect(state.attributes[ATTR_EVENT_SCORE]).to_equal(100)

    event = Event(
        model=ModelType.EVENT,
        id="test_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=1),
        end=fixed_now + timedelta(seconds=1),
        score=50,
        smart_detect_types=[SmartDetectObjectType.PACKAGE],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.PACKAGE] = event.id

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    # Event is already seen and has end, should now be off
    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)

    # Now send an event that has an end right away
    event = Event(
        model=ModelType.EVENT,
        id="new_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=1),
        end=fixed_now + timedelta(seconds=1),
        score=80,
        smart_detect_types=[SmartDetectObjectType.PACKAGE],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.PACKAGE] = event.id

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event

    state_changes: list[HAEvent[EventStateChangedData]] = async_capture_events(
        hass, EVENT_STATE_CHANGED
    )
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)

    expect(len(state_changes)).to_equal(2)

    on_event = state_changes[0]
    state = on_event.data["new_state"]
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)
    expect(state.attributes[ATTR_EVENT_SCORE]).to_equal(80)

    off_event = state_changes[1]
    state = off_event.data["new_state"]
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(ATTR_EVENT_SCORE not in state.attributes).to_be(True)

    # replay and ensure ignored
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()
    expect(len(state_changes)).to_equal(2)


@test
async def binary_sensor_person_detected(
    _trigger: int = Depends(_trigger_executor),
    _entity_registry_enabled: object = Depends(
        entity_registry_enabled_by_default_fixture
    ),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
    unadopted_camera: Camera = Depends(unadopted_camera_fixture),
    fixed_now: datetime = Depends(fixed_now_fixture),
) -> None:
    """Test binary_sensor person detected detection entity."""

    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 15, 15)

    doorbell.smart_detect_settings.object_types.append(SmartDetectObjectType.PERSON)

    _, entity_id = await ids_from_device_description(
        hass, Platform.BINARY_SENSOR, doorbell, EVENT_SENSORS[3]
    )

    events = async_capture_events(hass, EVENT_STATE_CHANGED)

    event = Event(
        model=ModelType.EVENT,
        id="test_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=1),
        end=None,
        score=50,
        smart_detect_types=[],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)

    event = Event(
        model=ModelType.EVENT,
        id="test_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=1),
        end=fixed_now + timedelta(seconds=1),
        score=65,
        smart_detect_types=[SmartDetectObjectType.PERSON],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.PERSON] = event.id

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    entity_events = [event for event in events if event.data["entity_id"] == entity_id]
    expect(len(entity_events)).to_equal(3)
    expect(entity_events[0].data["new_state"].state).to_equal(STATE_OFF)
    expect(entity_events[1].data["new_state"].state).to_equal(STATE_ON)
    expect(entity_events[2].data["new_state"].state).to_equal(STATE_OFF)

    # Event is already seen and has end, should now be off
    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)

    # Now send an event that has an end right away
    event = Event(
        model=ModelType.EVENT,
        id="new_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=1),
        end=fixed_now + timedelta(seconds=1),
        score=80,
        smart_detect_types=[SmartDetectObjectType.PERSON],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.PERSON] = event.id

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event

    state_changes: list[HAEvent[EventStateChangedData]] = async_capture_events(
        hass, EVENT_STATE_CHANGED
    )
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)

    expect(len(state_changes)).to_equal(2)

    on_event = state_changes[0]
    state = on_event.data["new_state"]
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)
    expect(state.attributes[ATTR_EVENT_SCORE]).to_equal(80)

    off_event = state_changes[1]
    state = off_event.data["new_state"]
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(ATTR_EVENT_SCORE not in state.attributes).to_be(True)

    # replay and ensure ignored
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()
    expect(len(state_changes)).to_equal(2)


@test
async def aiport_no_binary_sensor_entities(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    aiport: AiPort = Depends(aiport_fixture),
) -> None:
    """Test that AI Port devices do not create camera-specific binary sensor entities."""
    await init_entry(hass, ufp, [aiport])

    # AI Port should not create any camera-specific binary sensors (motion, smart detection, etc.)
    # NVR HDD sensors will still be created, but no AI Port-specific entities
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_registry, ufp.entry.entry_id)

    for entity in entities:
        if entity.domain == Platform.BINARY_SENSOR:
            # No entities should contain the AI Port's device id
            expect(aiport.id not in entity.unique_id).to_be(True)


@test
async def binary_sensor_simultaneous_person_and_vehicle_detection(
    _trigger: int = Depends(_trigger_executor),
    _entity_registry_enabled: object = Depends(
        entity_registry_enabled_by_default_fixture
    ),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
    unadopted_camera: Camera = Depends(unadopted_camera_fixture),
    fixed_now: datetime = Depends(fixed_now_fixture),
) -> None:
    """Test that when an event is updated with additional detection types, both trigger.

    This is a regression test for https://github.com/home-assistant/core/issues/152133
    where an event starting with vehicle detection gets updated to also include person
    detection (e.g., someone getting out of a car). Both sensors should be ON
    simultaneously, not queued.
    """

    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.BINARY_SENSOR, 15, 15)

    doorbell.smart_detect_settings.object_types.append(SmartDetectObjectType.PERSON)
    doorbell.smart_detect_settings.object_types.append(SmartDetectObjectType.VEHICLE)

    # Get entity IDs for both person and vehicle detection
    _, person_entity_id = await ids_from_device_description(
        hass,
        Platform.BINARY_SENSOR,
        doorbell,
        EVENT_SENSORS[3],  # person detected
    )
    _, vehicle_entity_id = await ids_from_device_description(
        hass,
        Platform.BINARY_SENSOR,
        doorbell,
        EVENT_SENSORS[4],  # vehicle detected
    )

    # Step 1: Initial event with only VEHICLE detection (car arriving)
    event = Event(
        model=ModelType.EVENT,
        id="combined_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=5),
        end=None,  # Event is ongoing
        score=90,
        smart_detect_types=[SmartDetectObjectType.VEHICLE],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.VEHICLE] = event.id

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {event.id: event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    # Vehicle sensor should be ON
    vehicle_state = hass.states.get(vehicle_entity_id)
    expect(vehicle_state).not_.to_be(None)
    expect(vehicle_state.state).to_equal(STATE_ON)

    # Person sensor should still be OFF (no person detected yet)
    person_state = hass.states.get(person_entity_id)
    expect(person_state).not_.to_be(None)
    expect(person_state.state).to_equal(STATE_OFF)

    # Step 2: Same event gets updated to include PERSON detection
    # (someone gets out of the car - Protect adds PERSON to the same event)
    #
    # BUG SCENARIO: UniFi Protect updates the event to include PERSON in
    # smart_detect_types, BUT does NOT update last_smart_detect_event_ids[PERSON]
    # until the event ends. This is the core issue reported in #152133.
    updated_event = Event(
        model=ModelType.EVENT,
        id="combined_event_id",  # Same event ID!
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=5),
        end=None,  # Event still ongoing
        score=90,
        smart_detect_types=[
            SmartDetectObjectType.VEHICLE,
            SmartDetectObjectType.PERSON,
        ],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    # IMPORTANT: The camera's last_smart_detect_event_ids is NOT updated for PERSON!
    # This simulates the real bug where UniFi Protect doesn't immediately update
    # the camera's last_smart_detect_event_ids when a new detection type is added
    # to an ongoing event.
    new_camera = doorbell.model_copy()
    new_camera.is_smart_detected = True
    # Only VEHICLE has the event ID - PERSON does not (simulating the bug)
    new_camera.last_smart_detect_event_ids[SmartDetectObjectType.VEHICLE] = (
        updated_event.id
    )
    # NOTE: We're NOT setting last_smart_detect_event_ids[PERSON] to simulate the bug!

    ufp.api.bootstrap.cameras = {new_camera.id: new_camera}
    ufp.api.bootstrap.events = {updated_event.id: updated_event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = updated_event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    # CRITICAL: Both sensors should now be ON simultaneously
    vehicle_state = hass.states.get(vehicle_entity_id)
    expect(vehicle_state).not_.to_be(None)
    expect(vehicle_state.state).to_equal(STATE_ON)

    person_state = hass.states.get(person_entity_id)
    expect(person_state).not_.to_be(None)
    expect(person_state.state).to_equal(STATE_ON)

    # Verify both have correct attributes
    expect(vehicle_state.attributes[ATTR_EVENT_SCORE]).to_equal(90)
    expect(person_state.attributes[ATTR_EVENT_SCORE]).to_equal(90)

    # Step 3: Event ends - both sensors should turn OFF
    ended_event = Event(
        model=ModelType.EVENT,
        id="combined_event_id",
        type=EventType.SMART_DETECT,
        start=fixed_now - timedelta(seconds=5),
        end=fixed_now,  # Event ended now
        score=90,
        smart_detect_types=[
            SmartDetectObjectType.VEHICLE,
            SmartDetectObjectType.PERSON,
        ],
        smart_detect_event_ids=[],
        camera_id=doorbell.id,
        api=ufp.api,
    )

    ufp.api.bootstrap.events = {ended_event.id: ended_event}

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = ended_event
    ufp.ws_msg(mock_msg)

    await hass.async_block_till_done()

    # Both should be OFF now
    vehicle_state = hass.states.get(vehicle_entity_id)
    expect(vehicle_state).not_.to_be(None)
    expect(vehicle_state.state).to_equal(STATE_OFF)

    person_state = hass.states.get(person_entity_id)
    expect(person_state).not_.to_be(None)
    expect(person_state.state).to_equal(STATE_OFF)
