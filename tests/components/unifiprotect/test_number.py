"""Test the UniFi Protect number platform."""

from datetime import timedelta
from unittest.mock import AsyncMock, Mock

from tryke import Depends, expect, fixture, test
from uiprotect.data import Camera, Chime, Doorlock, IRLEDMode, Light, RingSetting

from homeassistant.components.unifiprotect.const import DEFAULT_ATTRIBUTION
from homeassistant.components.unifiprotect.number import (
    CAMERA_NUMBERS,
    DOORLOCK_NUMBERS,
    LIGHT_NUMBERS,
)
from homeassistant.const import ATTR_ATTRIBUTION, ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import patch_ufp_method
from ._fixtures import (
    camera,
    camera_all_features,
    chime,
    doorbell,
    doorlock,
    light,
    ufp,
    unadopted_camera,
)
from .utils import (
    MockUFPFixture,
    adopt_devices,
    assert_entity_counts,
    ids_from_device_description,
    init_entry,
    remove_entities,
)

from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
)


@fixture
def _trigger_executor() -> int:
    """Force a HookExecutor for this module (tryke discovery quirk)."""
    return 0


def _configure_camera_all_features(camera_obj: Camera) -> None:
    """Configure a camera with all number-entity features enabled."""
    camera_obj.feature_flags.has_chime = True
    camera_obj.chime_duration = timedelta(seconds=1)
    camera_obj.feature_flags.has_led_ir = True
    camera_obj.isp_settings.icr_custom_value = 1
    camera_obj.isp_settings.ir_led_mode = IRLEDMode.CUSTOM
    camera_obj.feature_flags.has_speaker = True
    camera_obj.speaker_settings.volume = 1
    camera_obj.feature_flags.is_doorbell = True
    camera_obj.speaker_settings.ring_volume = 1


@test
async def number_sensor_camera_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    camera: Camera = Depends(camera),
    unadopted_camera: Camera = Depends(unadopted_camera),
) -> None:
    """Test removing and re-adding a camera device."""
    await init_entry(hass, ufp, [camera, unadopted_camera])
    assert_entity_counts(hass, Platform.NUMBER, 4, 4)
    await remove_entities(hass, ufp, [camera, unadopted_camera])
    assert_entity_counts(hass, Platform.NUMBER, 0, 0)
    await adopt_devices(hass, ufp, [camera, unadopted_camera])
    assert_entity_counts(hass, Platform.NUMBER, 4, 4)


@test
async def number_sensor_light_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    light: Light = Depends(light),
) -> None:
    """Test removing and re-adding a light device."""
    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.NUMBER, 2, 2)
    await remove_entities(hass, ufp, [light])
    assert_entity_counts(hass, Platform.NUMBER, 0, 0)
    await adopt_devices(hass, ufp, [light])
    assert_entity_counts(hass, Platform.NUMBER, 2, 2)


@test
async def number_lock_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
) -> None:
    """Test removing and re-adding a doorlock device."""
    await init_entry(hass, ufp, [doorlock])
    assert_entity_counts(hass, Platform.NUMBER, 1, 1)
    await remove_entities(hass, ufp, [doorlock])
    assert_entity_counts(hass, Platform.NUMBER, 0, 0)
    await adopt_devices(hass, ufp, [doorlock])
    assert_entity_counts(hass, Platform.NUMBER, 1, 1)


@test
async def number_setup_light(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp),
    light: Light = Depends(light),
) -> None:
    """Test number entity setup for light devices."""
    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.NUMBER, 2, 2)

    for description in LIGHT_NUMBERS:
        unique_id, entity_id = await ids_from_device_description(
            hass, Platform.NUMBER, light, description
        )

        entity = entity_registry.async_get(entity_id)
        expect(entity).to_be_truthy()
        expect(entity.unique_id).to_equal(unique_id)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("45")
        expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def number_setup_camera_all(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp),
    camera: Camera = Depends(camera),
) -> None:
    """Test number entity setup for camera devices (all features)."""
    _configure_camera_all_features(camera)
    await init_entry(hass, ufp, [camera])
    assert_entity_counts(hass, Platform.NUMBER, 7, 7)

    for description in CAMERA_NUMBERS:
        unique_id, entity_id = await ids_from_device_description(
            hass, Platform.NUMBER, camera, description
        )

        entity = entity_registry.async_get(entity_id)
        expect(entity).to_be_truthy()
        expect(entity.unique_id).to_equal(unique_id)

        state = hass.states.get(entity_id)
        expect(state).to_be_truthy()
        expect(state.state).to_equal("1")
        expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def number_setup_camera_none(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    camera: Camera = Depends(camera),
) -> None:
    """Test number entity setup for camera devices (no features)."""
    camera.feature_flags.can_optical_zoom = False
    camera.feature_flags.has_mic = False
    # has_wdr is the inverse of has HDR
    camera.feature_flags.has_hdr = True
    camera.feature_flags.has_led_ir = False

    await init_entry(hass, ufp, [camera])
    assert_entity_counts(hass, Platform.NUMBER, 0, 0)


@test
async def number_setup_camera_missing_attr(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    camera: Camera = Depends(camera),
) -> None:
    """Test number entity setup for camera devices (no features, bad attrs)."""
    camera.feature_flags = None

    await init_entry(hass, ufp, [camera])
    assert_entity_counts(hass, Platform.NUMBER, 0, 0)


@test
async def number_light_sensitivity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    light: Light = Depends(light),
) -> None:
    """Test sensitivity number entity for lights."""
    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.NUMBER, 2, 2)

    description = LIGHT_NUMBERS[0]
    expect(description.ufp_set_method).to_be_truthy()

    _, entity_id = await ids_from_device_description(
        hass, Platform.NUMBER, light, description
    )

    with patch_ufp_method(
        light, "set_sensitivity", new_callable=AsyncMock
    ) as mock_method:
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: entity_id, "value": 15.0},
            blocking=True,
        )

        mock_method.assert_called_once_with(15.0)


@test
async def number_light_duration(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    light: Light = Depends(light),
) -> None:
    """Test auto-shutoff duration number entity for lights."""
    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.NUMBER, 2, 2)

    description = LIGHT_NUMBERS[1]

    _, entity_id = await ids_from_device_description(
        hass, Platform.NUMBER, light, description
    )

    with patch_ufp_method(light, "set_duration", new_callable=AsyncMock) as mock_method:
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: entity_id, "value": 15.0},
            blocking=True,
        )

        mock_method.assert_called_once_with(timedelta(seconds=15.0))


@test.cases(
    test.case("wdr_value", index=0),
    test.case("mic_level", index=1),
    test.case("system_sounds_volume", index=2),
    test.case("doorbell_ring_volume", index=3),
    test.case("zoom_position", index=4),
    test.case("chime_duration", index=5),
    test.case("icr_lux", index=6),
)
async def number_camera_simple(
    index: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    camera_all_features: Camera = Depends(camera_all_features),
) -> None:
    """Tests simple numbers for cameras using the all features fixture."""
    description = CAMERA_NUMBERS[index]
    await init_entry(hass, ufp, [camera_all_features])
    assert_entity_counts(hass, Platform.NUMBER, 7, 7)

    expect(description.ufp_set_method).to_be_truthy()

    _, entity_id = await ids_from_device_description(
        hass, Platform.NUMBER, camera_all_features, description
    )

    with patch_ufp_method(
        camera_all_features, description.ufp_set_method, new_callable=AsyncMock
    ) as mock_method:
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: entity_id, "value": 1.0},
            blocking=True,
        )

        mock_method.assert_called_once_with(1.0)


@test
async def number_lock_auto_close(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
) -> None:
    """Test auto-lock timeout for locks."""
    await init_entry(hass, ufp, [doorlock])
    assert_entity_counts(hass, Platform.NUMBER, 1, 1)

    description = DOORLOCK_NUMBERS[0]

    _, entity_id = await ids_from_device_description(
        hass, Platform.NUMBER, doorlock, description
    )

    with patch_ufp_method(
        doorlock, "set_auto_close_time", new_callable=AsyncMock
    ) as mock_method:
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: entity_id, "value": 15.0},
            blocking=True,
        )

        mock_method.assert_called_once_with(timedelta(seconds=15.0))


def _setup_chime_with_doorbell(
    chime: Chime, doorbell: Camera, volume: int = 50
) -> None:
    """Set up chime with paired doorbell for testing."""
    chime.camera_ids = [doorbell.id]
    chime.ring_settings = [
        RingSetting(
            camera_id=doorbell.id,
            repeat_times=1,
            ringtone_id="test-ringtone-id",
            volume=volume,
        )
    ]


@test
async def chime_ring_volume_setup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp),
    chime: Chime = Depends(chime),
    doorbell: Camera = Depends(doorbell),
) -> None:
    """Test chime ring volume number entity setup."""
    _setup_chime_with_doorbell(chime, doorbell, volume=75)

    await init_entry(hass, ufp, [chime, doorbell], regenerate_ids=False)

    entity_id = "number.test_chime_ring_volume_test_camera"
    entity = entity_registry.async_get(entity_id)
    expect(entity).to_be_truthy()
    expect(entity.unique_id).to_equal(f"{chime.mac}_ring_volume_{doorbell.id}")

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("75")
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def chime_ring_volume_set_value(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    chime: Chime = Depends(chime),
    doorbell: Camera = Depends(doorbell),
) -> None:
    """Test setting chime ring volume."""
    _setup_chime_with_doorbell(chime, doorbell)

    await init_entry(hass, ufp, [chime, doorbell], regenerate_ids=False)

    entity_id = "number.test_chime_ring_volume_test_camera"

    with patch_ufp_method(
        chime, "set_volume_for_camera_public", new_callable=AsyncMock
    ) as mock_method:
        await hass.services.async_call(
            "number",
            "set_value",
            {ATTR_ENTITY_ID: entity_id, "value": 80.0},
            blocking=True,
        )

        mock_method.assert_called_once_with(doorbell, 80)


@test
async def chime_ring_volume_multiple_cameras(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    chime: Chime = Depends(chime),
    doorbell: Camera = Depends(doorbell),
) -> None:
    """Test chime ring volume with multiple paired cameras."""
    doorbell2 = doorbell.model_copy()
    doorbell2.id = "test-doorbell-2"
    doorbell2.name = "Test Doorbell 2"
    doorbell2.mac = "aa:bb:cc:dd:ee:02"

    chime.camera_ids = [doorbell.id, doorbell2.id]
    chime.ring_settings = [
        RingSetting(
            camera_id=doorbell.id,
            repeat_times=1,
            ringtone_id="test-ringtone-id",
            volume=60,
        ),
        RingSetting(
            camera_id=doorbell2.id,
            repeat_times=2,
            ringtone_id="test-ringtone-id-2",
            volume=80,
        ),
    ]

    await init_entry(hass, ufp, [chime, doorbell, doorbell2], regenerate_ids=False)

    state1 = hass.states.get("number.test_chime_ring_volume_test_camera")
    expect(state1).to_be_truthy()
    expect(state1.state).to_equal("60")

    state2 = hass.states.get("number.test_chime_ring_volume_test_doorbell_2")
    expect(state2).to_be_truthy()
    expect(state2.state).to_equal("80")


@test
async def chime_ring_volume_unavailable_when_unpaired(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    chime: Chime = Depends(chime),
    doorbell: Camera = Depends(doorbell),
) -> None:
    """Test chime ring volume becomes unavailable when camera is unpaired."""
    _setup_chime_with_doorbell(chime, doorbell)

    await init_entry(hass, ufp, [chime, doorbell], regenerate_ids=False)

    entity_id = "number.test_chime_ring_volume_test_camera"
    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("50")

    # Simulate removing the camera pairing
    new_chime = chime.model_copy()
    new_chime.ring_settings = []

    ufp.api.bootstrap.chimes = {new_chime.id: new_chime}
    ufp.api.bootstrap.nvr.system_info.ustorage = None
    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_chime

    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(state).to_be_truthy()
    expect(state.state).to_equal("unavailable")
