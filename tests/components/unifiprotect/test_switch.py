"""Test the UniFi Protect switch platform."""

from unittest.mock import AsyncMock, Mock

from tryke import Depends, expect, fixture, test
from uiprotect.data import Camera, Light, Permission, RecordingMode, VideoMode
from uiprotect.exceptions import ClientError, NotAuthorized

from homeassistant.components.unifiprotect.const import DEFAULT_ATTRIBUTION
from homeassistant.components.unifiprotect.switch import (
    ATTR_PREV_MIC,
    ATTR_PREV_RECORD,
    CAMERA_SWITCHES,
    LIGHT_SWITCHES,
    PRIVACY_MODE_SWITCH,
    ProtectSwitchEntityDescription,
)
from homeassistant.const import ATTR_ATTRIBUTION, ATTR_ENTITY_ID, STATE_OFF, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from . import patch_ufp_method
from ._fixtures import (
    camera as camera_fixture,
    doorbell as doorbell_fixture,
    light as light_fixture,
    ufp as ufp_fixture,
    unadopted_camera as unadopted_camera_fixture,
)
from .utils import (
    MockUFPFixture,
    adopt_devices,
    assert_entity_counts,
    enable_entity,
    ids_from_device_description,
    init_entry,
    remove_entities,
)

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async

CAMERA_SWITCHES_BASIC = [
    d
    for d in CAMERA_SWITCHES
    if (
        not d.translation_key.startswith("detections_")
        and d.key not in {"ssh", "color_night_vision", "track_person", "hdr_mode"}
    )
    or d.key
    in {
        "detections_motion",
        "detections_person",
        "detections_vehicle",
        "detections_animal",
    }
]
CAMERA_SWITCHES_NO_EXTRA = [
    d
    for d in CAMERA_SWITCHES_BASIC
    if d.key not in ("high_fps", "privacy_mode", "hdr_mode")
]

@fixture
def _trigger_executor() -> int:
    """Force tryke to build a per-module HookExecutor for this file."""
    return 0


@test
async def switch_camera_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
    unadopted_camera: Camera = Depends(unadopted_camera_fixture),
) -> None:
    """Test removing and re-adding a camera device."""
    ufp.api.bootstrap.nvr.system_info.ustorage = None
    await init_entry(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.SWITCH, 17, 15)
    await remove_entities(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.SWITCH, 2, 2)
    await adopt_devices(hass, ufp, [doorbell, unadopted_camera])
    assert_entity_counts(hass, Platform.SWITCH, 17, 15)


@test
async def switch_light_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    light: Light = Depends(light_fixture),
) -> None:
    """Test removing and re-adding a light device."""
    ufp.api.bootstrap.nvr.system_info.ustorage = None
    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.SWITCH, 4, 3)
    await remove_entities(hass, ufp, [light])
    assert_entity_counts(hass, Platform.SWITCH, 2, 2)
    await adopt_devices(hass, ufp, [light])
    assert_entity_counts(hass, Platform.SWITCH, 4, 3)


@test
async def switch_nvr(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
) -> None:
    """Test switch entity setup for light devices."""
    await init_entry(hass, ufp, [])

    assert_entity_counts(hass, Platform.SWITCH, 2, 2)

    nvr = ufp.api.bootstrap.nvr
    entity_id = "switch.unifiprotect_insights_enabled"

    with patch_ufp_method(nvr, "set_insights", new_callable=AsyncMock) as mock_method:
        await hass.services.async_call(
            "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_method.assert_called_once_with(True)

        await hass.services.async_call(
            "switch", "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_method.assert_called_with(False)


@test
async def switch_setup_no_perm(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    light: Light = Depends(light_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
) -> None:
    """Test switch entity setup for light devices."""
    ufp.api.bootstrap.auth_user.all_permissions = [
        Permission.unifi_dict_to_dict({"rawPermission": "light:read:*"})
    ]

    await init_entry(hass, ufp, [light, doorbell])

    assert_entity_counts(hass, Platform.SWITCH, 0, 0)


@test
async def switch_setup_light(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    light: Light = Depends(light_fixture),
) -> None:
    """Test switch entity setup for light devices."""
    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.SWITCH, 4, 3)

    description = LIGHT_SWITCHES[1]

    unique_id, entity_id = await ids_from_device_description(
        hass, Platform.SWITCH, light, description
    )

    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)
    expect(entity.unique_id).to_equal(unique_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)

    description = LIGHT_SWITCHES[0]

    unique_id = f"{light.mac}_{description.key}"
    entity_id = f"switch.test_light_{description.translation_key}"

    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)
    expect(entity.disabled).to_be(True)
    expect(entity.unique_id).to_equal(unique_id)

    await enable_entity(hass, ufp.entry.entry_id, entity_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def switch_setup_camera_all(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
) -> None:
    """Test switch entity setup for camera devices (all enabled feature flags)."""
    await init_entry(hass, ufp, [doorbell])
    assert_entity_counts(hass, Platform.SWITCH, 17, 15)

    for description in CAMERA_SWITCHES_BASIC:
        unique_id, entity_id = await ids_from_device_description(
            hass, Platform.SWITCH, doorbell, description
        )

        entity = entity_registry.async_get(entity_id)
        expect(entity).not_.to_be(None)
        expect(entity.unique_id).to_equal(unique_id)

        state = hass.states.get(entity_id)
        expect(state).not_.to_be(None)
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)

    description = CAMERA_SWITCHES[0]

    unique_id = f"{doorbell.mac}_{description.key}"
    entity_id = f"switch.test_camera_{description.translation_key}"

    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)
    expect(entity.disabled).to_be(True)
    expect(entity.unique_id).to_equal(unique_id)

    await enable_entity(hass, ufp.entry.entry_id, entity_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def switch_setup_camera_none(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    camera: Camera = Depends(camera_fixture),
) -> None:
    """Test switch entity setup for camera devices (no enabled feature flags)."""
    await init_entry(hass, ufp, [camera])
    assert_entity_counts(hass, Platform.SWITCH, 8, 7)

    for description in CAMERA_SWITCHES_BASIC:
        if description.ufp_required_field is not None:
            continue

        unique_id, entity_id = await ids_from_device_description(
            hass, Platform.SWITCH, camera, description
        )

        entity = entity_registry.async_get(entity_id)
        expect(entity).not_.to_be(None)
        expect(entity.unique_id).to_equal(unique_id)

        state = hass.states.get(entity_id)
        expect(state).not_.to_be(None)
        expect(state.state).to_equal(STATE_OFF)
        expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)

    description = CAMERA_SWITCHES[0]

    unique_id = f"{camera.mac}_{description.key}"
    entity_id = f"switch.test_camera_{description.translation_key}"

    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)
    expect(entity.disabled).to_be(True)
    expect(entity.unique_id).to_equal(unique_id)

    await enable_entity(hass, ufp.entry.entry_id, entity_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def switch_light_status(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    light: Light = Depends(light_fixture),
) -> None:
    """Tests status light switch for lights."""
    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.SWITCH, 4, 3)

    description = LIGHT_SWITCHES[1]

    _, entity_id = await ids_from_device_description(
        hass, Platform.SWITCH, light, description
    )

    with patch_ufp_method(
        light, "set_status_light", new_callable=AsyncMock
    ) as mock_method:
        await hass.services.async_call(
            "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_method.assert_called_once_with(True)

        await hass.services.async_call(
            "switch", "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_method.assert_called_with(False)


@test
async def switch_camera_ssh(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
) -> None:
    """Tests SSH switch for cameras."""
    await init_entry(hass, ufp, [doorbell])
    assert_entity_counts(hass, Platform.SWITCH, 17, 15)

    description = CAMERA_SWITCHES[0]

    _, entity_id = await ids_from_device_description(
        hass, Platform.SWITCH, doorbell, description
    )
    await enable_entity(hass, ufp.entry.entry_id, entity_id)

    with patch_ufp_method(doorbell, "set_ssh", new_callable=AsyncMock) as mock_method:
        await hass.services.async_call(
            "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_method.assert_called_once_with(True)

        await hass.services.async_call(
            "switch", "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_method.assert_called_with(False)


@test.cases(
    test.case("status_light", index=0),
    test.case("system_sounds", index=1),
    test.case("osd_name", index=2),
    test.case("osd_date", index=3),
    test.case("osd_logo", index=4),
    test.case("osd_bitrate", index=5),
    test.case("motion", index=6),
)
async def switch_camera_simple(
    *,
    index: int,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
) -> None:
    """Tests all simple switches for cameras."""
    description = CAMERA_SWITCHES_NO_EXTRA[index]
    await init_entry(hass, ufp, [doorbell])
    assert_entity_counts(hass, Platform.SWITCH, 17, 15)

    expect(description.ufp_set_method).not_.to_be(None)

    with patch_ufp_method(
        doorbell, description.ufp_set_method, new_callable=AsyncMock
    ) as mock_method:
        _, entity_id = await ids_from_device_description(
            hass, Platform.SWITCH, doorbell, description
        )

        await hass.services.async_call(
            "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_method.assert_called_once_with(True)

        await hass.services.async_call(
            "switch", "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_method.assert_called_with(False)


@test
async def switch_camera_highfps(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
) -> None:
    """Tests High FPS switch for cameras."""
    await init_entry(hass, ufp, [doorbell])
    assert_entity_counts(hass, Platform.SWITCH, 17, 15)

    description = CAMERA_SWITCHES[3]

    _, entity_id = await ids_from_device_description(
        hass, Platform.SWITCH, doorbell, description
    )

    with patch_ufp_method(
        doorbell, "set_video_mode", new_callable=AsyncMock
    ) as mock_method:
        await hass.services.async_call(
            "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_method.assert_called_once_with(VideoMode.HIGH_FPS)

        await hass.services.async_call(
            "switch", "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_method.assert_called_with(VideoMode.DEFAULT)


@test
async def switch_camera_privacy(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
) -> None:
    """Tests Privacy Mode switch for cameras with privacy mode defaulted on."""
    previous_mic = doorbell.mic_volume = 53
    previous_record = doorbell.recording_settings.mode = RecordingMode.DETECTIONS

    await init_entry(hass, ufp, [doorbell])
    assert_entity_counts(hass, Platform.SWITCH, 17, 15)

    description = PRIVACY_MODE_SWITCH

    _, entity_id = await ids_from_device_description(
        hass, Platform.SWITCH, doorbell, description
    )

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal("off")
    expect(state.attributes).not_.to_contain(ATTR_PREV_MIC)
    expect(state.attributes).not_.to_contain(ATTR_PREV_RECORD)

    with patch_ufp_method(
        doorbell, "set_privacy", new_callable=AsyncMock
    ) as mock_set_privacy:
        await hass.services.async_call(
            "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_set_privacy.assert_called_with(True, 0, RecordingMode.NEVER)

        new_doorbell = doorbell.model_copy()
        new_doorbell.add_privacy_zone()
        new_doorbell.mic_volume = 0
        new_doorbell.recording_settings.mode = RecordingMode.NEVER
        ufp.api.bootstrap.cameras = {new_doorbell.id: new_doorbell}

        mock_msg = Mock()
        mock_msg.changed_data = {}
        mock_msg.new_obj = new_doorbell
        ufp.ws_msg(mock_msg)

        state = hass.states.get(entity_id)
        expect(state).not_.to_be(None)
        expect(state.state).to_equal("on")
        expect(state.attributes[ATTR_PREV_MIC]).to_equal(previous_mic)
        expect(state.attributes[ATTR_PREV_RECORD]).to_equal(previous_record.value)

        mock_set_privacy.reset_mock()

        await hass.services.async_call(
            "switch", "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_set_privacy.assert_called_with(False, previous_mic, previous_record)


@test
async def switch_camera_privacy_already_on(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    doorbell: Camera = Depends(doorbell_fixture),
) -> None:
    """Tests Privacy Mode switch for cameras with privacy mode defaulted on."""
    doorbell.add_privacy_zone()
    await init_entry(hass, ufp, [doorbell])
    assert_entity_counts(hass, Platform.SWITCH, 17, 15)

    description = PRIVACY_MODE_SWITCH

    _, entity_id = await ids_from_device_description(
        hass, Platform.SWITCH, doorbell, description
    )

    with patch_ufp_method(
        doorbell, "set_privacy", new_callable=AsyncMock
    ) as mock_set_privacy:
        await hass.services.async_call(
            "switch", "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        mock_set_privacy.assert_called_once_with(False, 100, RecordingMode.ALWAYS)


@test
async def switch_turn_on_client_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    light: Light = Depends(light_fixture),
) -> None:
    """Test switch turn on with ClientError raises HomeAssistantError."""
    await init_entry(hass, ufp, [light])

    description = LIGHT_SWITCHES[1]

    _, entity_id = await ids_from_device_description(
        hass, Platform.SWITCH, light, description
    )

    with patch_ufp_method(
        light,
        "set_status_light",
        new_callable=AsyncMock,
        side_effect=ClientError("Test error"),
    ):
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
            )


@test
async def switch_turn_on_not_authorized(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fixture),
    light: Light = Depends(light_fixture),
) -> None:
    """Test switch turn on with NotAuthorized raises HomeAssistantError."""
    await init_entry(hass, ufp, [light])

    description = LIGHT_SWITCHES[1]

    _, entity_id = await ids_from_device_description(
        hass, Platform.SWITCH, light, description
    )

    with patch_ufp_method(
        light,
        "set_status_light",
        new_callable=AsyncMock,
        side_effect=NotAuthorized("Not authorized"),
    ):
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                "switch", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
            )
