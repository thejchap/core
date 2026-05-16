"""Test the UniFi Protect global services."""

from datetime import timedelta
from unittest.mock import AsyncMock, Mock

from tryke import Depends, expect, fixture, test
from uiprotect.data import (
    Camera,
    Chime,
    Color,
    Light,
    ModelType,
    PTZPreset,
    SmartDetectObjectType,
    VideoMode,
)
from uiprotect.data.devices import CameraZone
from uiprotect.exceptions import BadRequest, ClientError

from homeassistant.components.unifiprotect.const import (
    ATTR_MESSAGE,
    DOMAIN,
    KEYRINGS_KEY_TYPE,
    KEYRINGS_KEY_TYPE_ID_FINGERPRINT,
    KEYRINGS_KEY_TYPE_ID_NFC,
    KEYRINGS_ULP_ID,
    KEYRINGS_USER_FULL_NAME,
    KEYRINGS_USER_STATUS,
)
from homeassistant.components.unifiprotect.services import (
    ATTR_PRESET,
    SERVICE_ADD_DOORBELL_TEXT,
    SERVICE_GET_USER_KEYRING_INFO,
    SERVICE_PTZ_GOTO_PRESET,
    SERVICE_REMOVE_DOORBELL_TEXT,
    SERVICE_REMOVE_PRIVACY_ZONE,
    SERVICE_SET_CHIME_PAIRED,
)
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.const import ATTR_DEVICE_ID, ATTR_ENTITY_ID, ATTR_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import dt as dt_util

from . import patch_ufp_method
from ._fixtures import ufp as ufp_fx
from .utils import MockUFPFixture, init_entry

from tests.common import load_json_object_fixture
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor() -> int:
    """Anchor fixture for tryke Depends() resolution."""
    return 0


def _make_light() -> Light:
    """Build a Light device for tests."""
    Light.model_config["validate_assignment"] = False
    data = load_json_object_fixture("sample_light.json", DOMAIN)
    return Light.from_unifi_dict(**data)


def _make_chime() -> Chime:
    """Build a Chime device for tests."""
    Chime.model_config["validate_assignment"] = False
    data = load_json_object_fixture("sample_chime.json", DOMAIN)
    return Chime.from_unifi_dict(**data)


def _make_camera() -> Camera:
    """Build a Camera device for tests."""
    Camera.model_config["validate_assignment"] = False
    data = load_json_object_fixture("sample_camera.json", DOMAIN)
    cam = Camera.from_unifi_dict(**data)
    cam.last_motion = dt_util.utcnow() - timedelta(hours=1)
    return cam


def _make_doorbell() -> Camera:
    """Build a doorbell (camera with chime features)."""
    camera = _make_camera()
    doorbell = camera.model_copy()
    doorbell.channels = [c.model_copy() for c in doorbell.channels]

    package_channel = doorbell.channels[0].model_copy()
    package_channel.name = "Package Camera"
    package_channel.id = 3
    package_channel.fps = 2
    package_channel.rtsp_alias = "test_package_alias"

    doorbell.channels.append(package_channel)
    doorbell.feature_flags.video_modes = [VideoMode.DEFAULT, VideoMode.HIGH_FPS]
    doorbell.feature_flags.smart_detect_types = [
        SmartDetectObjectType.PERSON,
        SmartDetectObjectType.VEHICLE,
        SmartDetectObjectType.ANIMAL,
        SmartDetectObjectType.PACKAGE,
    ]
    doorbell.has_speaker = True
    doorbell.feature_flags.has_hdr = True
    doorbell.feature_flags.has_lcd_screen = True
    doorbell.feature_flags.has_speaker = True
    doorbell.feature_flags.has_privacy_mask = True
    doorbell.feature_flags.is_doorbell = True
    doorbell.feature_flags.has_fingerprint_sensor = True
    doorbell.feature_flags.support_nfc = True
    doorbell.feature_flags.has_chime = True
    doorbell.feature_flags.has_smart_detect = True
    doorbell.feature_flags.has_package_camera = True
    doorbell.feature_flags.has_led_status = True
    doorbell.last_ring = dt_util.utcnow() - timedelta(hours=1)
    return doorbell


def _make_ptz_camera() -> Camera:
    """Build a PTZ camera device."""
    camera = _make_camera()
    ptz_cam = camera.model_copy()
    ptz_cam.channels = [c.model_copy() for c in ptz_cam.channels]
    ptz_cam.name = "PTZ Camera"
    ptz_cam.feature_flags.is_ptz = True
    ptz_cam.active_patrol_slot = None

    object.__setattr__(ptz_cam, "get_ptz_presets", AsyncMock(return_value=[]))
    object.__setattr__(ptz_cam, "get_ptz_patrols", AsyncMock(return_value=[]))
    object.__setattr__(ptz_cam, "ptz_goto_preset_public", AsyncMock())
    object.__setattr__(ptz_cam, "ptz_patrol_start_public", AsyncMock())
    object.__setattr__(ptz_cam, "ptz_patrol_stop_public", AsyncMock())

    return ptz_cam


async def _init_with_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    ufp: MockUFPFixture,
) -> dr.DeviceEntry:
    """Set up entry with no devices and return NVR device entry."""
    await init_entry(hass, ufp, [])
    return next(iter(device_registry.devices.values()))


async def _init_with_subdevice(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    ufp: MockUFPFixture,
    light: Light,
) -> dr.DeviceEntry:
    """Set up entry with a Light device and return the Light device entry."""
    await init_entry(hass, ufp, [light])
    return next(
        d for d in device_registry.devices.values() if d.name != "UnifiProtect"
    )


@test
async def global_service_bad_device(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test global service, invalid device ID."""
    nvr = ufp.api.bootstrap.nvr

    with patch_ufp_method(
        nvr, "add_custom_doorbell_message", new_callable=AsyncMock
    ) as mock_method:
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_ADD_DOORBELL_TEXT,
                {ATTR_DEVICE_ID: "bad_device_id", ATTR_MESSAGE: "Test Message"},
                blocking=True,
            )
        expect(mock_method.called).to_be(False)


@test
async def global_service_exception(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test global service, unexpected error."""
    device = await _init_with_device(hass, device_registry, ufp)
    nvr = ufp.api.bootstrap.nvr

    with patch_ufp_method(
        nvr,
        "add_custom_doorbell_message",
        new_callable=AsyncMock,
        side_effect=BadRequest,
    ) as mock_method:
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_ADD_DOORBELL_TEXT,
                {ATTR_DEVICE_ID: device.id, ATTR_MESSAGE: "Test Message"},
                blocking=True,
            )
        expect(mock_method.called).to_be(True)


@test
async def add_doorbell_text(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test add_doorbell_text service."""
    device = await _init_with_device(hass, device_registry, ufp)
    nvr = ufp.api.bootstrap.nvr

    with patch_ufp_method(
        nvr, "add_custom_doorbell_message", new_callable=AsyncMock
    ) as mock_method:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_ADD_DOORBELL_TEXT,
            {ATTR_DEVICE_ID: device.id, ATTR_MESSAGE: "Test Message"},
            blocking=True,
        )
        mock_method.assert_called_once_with("Test Message")


@test
async def remove_doorbell_text(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test remove_doorbell_text service."""
    light = _make_light()
    try:
        subdevice = await _init_with_subdevice(hass, device_registry, ufp, light)
        nvr = ufp.api.bootstrap.nvr

        with patch_ufp_method(
            nvr, "remove_custom_doorbell_message", new_callable=AsyncMock
        ) as mock_method:
            await hass.services.async_call(
                DOMAIN,
                SERVICE_REMOVE_DOORBELL_TEXT,
                {ATTR_DEVICE_ID: subdevice.id, ATTR_MESSAGE: "Test Message"},
                blocking=True,
            )
            mock_method.assert_called_once_with("Test Message")
    finally:
        Light.model_config["validate_assignment"] = True


@test
async def add_doorbell_text_disabled_config_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test add_doorbell_text service."""
    device = await _init_with_device(hass, device_registry, ufp)
    nvr = ufp.api.bootstrap.nvr

    await hass.config_entries.async_set_disabled_by(
        ufp.entry.entry_id, ConfigEntryDisabler.USER
    )
    await hass.async_block_till_done()

    with patch_ufp_method(
        nvr, "add_custom_doorbell_message", new_callable=AsyncMock
    ) as mock_method:
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_ADD_DOORBELL_TEXT,
                {ATTR_DEVICE_ID: device.id, ATTR_MESSAGE: "Test Message"},
                blocking=True,
            )
        expect(mock_method.called).to_be(False)


@test
async def set_chime_paired_doorbells(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test set_chime_paired_doorbells."""
    chime = _make_chime()
    doorbell = _make_doorbell()
    try:
        ufp.api.update_device = AsyncMock()

        camera1 = doorbell.model_copy()
        camera1.name = "Test Camera 1"

        camera2 = doorbell.model_copy()
        camera2.name = "Test Camera 2"

        await init_entry(hass, ufp, [camera1, camera2, chime])

        chime_entry = entity_registry.async_get("button.test_chime_play_chime")
        camera_entry = entity_registry.async_get(
            "binary_sensor.test_camera_2_doorbell"
        )
        expect(chime_entry).not_.to_be_none()
        expect(camera_entry).not_.to_be_none()

        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_CHIME_PAIRED,
            {
                ATTR_DEVICE_ID: chime_entry.device_id,
                "doorbells": {
                    ATTR_ENTITY_ID: ["binary_sensor.test_camera_1_doorbell"],
                    ATTR_DEVICE_ID: [camera_entry.device_id],
                },
            },
            blocking=True,
        )

        ufp.api.update_device.assert_called_once_with(
            ModelType.CHIME,
            chime.id,
            {"cameraIds": sorted([camera1.id, camera2.id])},
        )
    finally:
        Chime.model_config["validate_assignment"] = True
        Camera.model_config["validate_assignment"] = True


@test
async def remove_privacy_zone_no_zone(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test remove_privacy_zone service."""
    doorbell = _make_doorbell()
    try:
        ufp.api.update_device = AsyncMock()
        doorbell.privacy_zones = []

        await init_entry(hass, ufp, [doorbell])

        camera_entry = entity_registry.async_get("binary_sensor.test_camera_doorbell")

        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_REMOVE_PRIVACY_ZONE,
                {ATTR_DEVICE_ID: camera_entry.device_id, ATTR_NAME: "Testing"},
                blocking=True,
            )
        ufp.api.update_device.assert_not_called()
    finally:
        Camera.model_config["validate_assignment"] = True


@test
async def remove_privacy_zone(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test remove_privacy_zone service."""
    doorbell = _make_doorbell()
    try:
        ufp.api.update_device = AsyncMock()
        doorbell.privacy_zones = [
            CameraZone(
                id=0, name="Testing", color=Color("red"), points=[(0, 0), (1, 1)]
            )
        ]

        await init_entry(hass, ufp, [doorbell])

        camera_entry = entity_registry.async_get("binary_sensor.test_camera_doorbell")

        await hass.services.async_call(
            DOMAIN,
            SERVICE_REMOVE_PRIVACY_ZONE,
            {ATTR_DEVICE_ID: camera_entry.device_id, ATTR_NAME: "Testing"},
            blocking=True,
        )
        ufp.api.update_device.assert_called()
        expect(bool(doorbell.privacy_zones)).to_be(False)
    finally:
        Camera.model_config["validate_assignment"] = True


@test
async def get_user_keyring_info(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test get_user_keyring_info service."""
    doorbell = _make_doorbell()
    try:
        ulp_user = Mock(full_name="Test User", status="active", ulp_id="user_ulp_id")
        keyring = Mock(
            registry_type="nfc",
            registry_id="123456",
            ulp_user="user_ulp_id",
        )
        keyring_2 = Mock(
            registry_type="fingerprint",
            registry_id="2",
            ulp_user="user_ulp_id",
        )
        ufp.api.bootstrap.ulp_users.as_list = Mock(return_value=[ulp_user])
        ufp.api.bootstrap.keyrings.as_list = Mock(return_value=[keyring, keyring_2])

        await init_entry(hass, ufp, [doorbell])

        camera_entry = entity_registry.async_get("binary_sensor.test_camera_doorbell")

        response = await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_USER_KEYRING_INFO,
            {ATTR_DEVICE_ID: camera_entry.device_id},
            blocking=True,
            return_response=True,
        )

        expect(response).to_equal(
            {
                "users": [
                    {
                        KEYRINGS_USER_FULL_NAME: "Test User",
                        "keys": [
                            {
                                KEYRINGS_KEY_TYPE: "nfc",
                                KEYRINGS_KEY_TYPE_ID_NFC: "123456",
                            },
                            {
                                KEYRINGS_KEY_TYPE_ID_FINGERPRINT: "2",
                                KEYRINGS_KEY_TYPE: "fingerprint",
                            },
                        ],
                        KEYRINGS_USER_STATUS: "active",
                        KEYRINGS_ULP_ID: "user_ulp_id",
                    },
                ],
            }
        )
    finally:
        Camera.model_config["validate_assignment"] = True


@test
async def get_user_keyring_info_no_users(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test get_user_keyring_info service with no users."""
    doorbell = _make_doorbell()
    try:
        ufp.api.bootstrap.ulp_users.as_list = Mock(return_value=[])
        ufp.api.bootstrap.keyrings.as_list = Mock(return_value=[])

        await init_entry(hass, ufp, [doorbell])

        camera_entry = entity_registry.async_get("binary_sensor.test_camera_doorbell")

        async with expect_raises_async(
            HomeAssistantError,
            match="No users found, please check Protect permissions",
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_GET_USER_KEYRING_INFO,
                {ATTR_DEVICE_ID: camera_entry.device_id},
                blocking=True,
                return_response=True,
            )
    finally:
        Camera.model_config["validate_assignment"] = True


# --- PTZ Preset Service Tests ---


def _make_presets() -> list[PTZPreset]:
    """Create mock PTZ presets."""
    return [
        PTZPreset(
            id="preset1",
            name="Preset 1",
            slot=0,
            ptz={"pan": 100, "tilt": 50, "zoom": 0},
        ),
        PTZPreset(
            id="preset2",
            name="Preset 2",
            slot=1,
            ptz={"pan": 200, "tilt": 100, "zoom": 50},
        ),
    ]


@test
async def ptz_goto_preset(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test ptz_goto_preset service with a named preset."""
    ptz_camera = _make_ptz_camera()
    try:
        ptz_camera.get_ptz_presets.return_value = _make_presets()
        ptz_camera.get_ptz_patrols.return_value = []
        await init_entry(hass, ufp, [ptz_camera])

        camera_entry = entity_registry.async_get(
            "camera.ptz_camera_high_resolution_channel"
        )

        with patch_ufp_method(
            ptz_camera, "ptz_goto_preset_public", new_callable=AsyncMock
        ) as mock_method:
            await hass.services.async_call(
                DOMAIN,
                SERVICE_PTZ_GOTO_PRESET,
                {ATTR_DEVICE_ID: camera_entry.device_id, ATTR_PRESET: "Preset 1"},
                blocking=True,
            )
            mock_method.assert_called_once_with(slot=0)
    finally:
        Camera.model_config["validate_assignment"] = True


@test
async def ptz_goto_preset_home(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test ptz_goto_preset service with home preset."""
    ptz_camera = _make_ptz_camera()
    try:
        ptz_camera.get_ptz_patrols.return_value = []
        await init_entry(hass, ufp, [ptz_camera])

        camera_entry = entity_registry.async_get(
            "camera.ptz_camera_high_resolution_channel"
        )

        with patch_ufp_method(
            ptz_camera, "ptz_goto_preset_public", new_callable=AsyncMock
        ) as mock_method:
            await hass.services.async_call(
                DOMAIN,
                SERVICE_PTZ_GOTO_PRESET,
                {ATTR_DEVICE_ID: camera_entry.device_id, ATTR_PRESET: "Home"},
                blocking=True,
            )
            mock_method.assert_called_once_with(slot=-1)
    finally:
        Camera.model_config["validate_assignment"] = True


@test
async def ptz_goto_preset_not_found(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test ptz_goto_preset service with non-existent preset."""
    ptz_camera = _make_ptz_camera()
    try:
        ptz_camera.get_ptz_presets.return_value = []
        ptz_camera.get_ptz_patrols.return_value = []
        await init_entry(hass, ufp, [ptz_camera])

        camera_entry = entity_registry.async_get(
            "camera.ptz_camera_high_resolution_channel"
        )

        async with expect_raises_async(ServiceValidationError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_PTZ_GOTO_PRESET,
                {
                    ATTR_DEVICE_ID: camera_entry.device_id,
                    ATTR_PRESET: "Does Not Exist",
                },
                blocking=True,
            )
    finally:
        Camera.model_config["validate_assignment"] = True


@test
async def ptz_goto_preset_not_ptz_camera(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test ptz_goto_preset service on a non-PTZ camera."""
    doorbell = _make_doorbell()
    try:
        await init_entry(hass, ufp, [doorbell])

        camera_entry = entity_registry.async_get("binary_sensor.test_camera_doorbell")

        async with expect_raises_async(
            ServiceValidationError, match="does not support PTZ"
        ):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_PTZ_GOTO_PRESET,
                {ATTR_DEVICE_ID: camera_entry.device_id, ATTR_PRESET: "Home"},
                blocking=True,
            )
    finally:
        Camera.model_config["validate_assignment"] = True


@test
async def ptz_goto_preset_client_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test ptz_goto_preset service when get_ptz_presets raises ClientError."""
    ptz_camera = _make_ptz_camera()
    try:
        ptz_camera.get_ptz_presets.side_effect = ClientError("Connection failed")
        ptz_camera.get_ptz_patrols.return_value = []
        await init_entry(hass, ufp, [ptz_camera])

        camera_entry = entity_registry.async_get(
            "camera.ptz_camera_high_resolution_channel"
        )

        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_PTZ_GOTO_PRESET,
                {ATTR_DEVICE_ID: camera_entry.device_id, ATTR_PRESET: "Preset 1"},
                blocking=True,
            )
    finally:
        Camera.model_config["validate_assignment"] = True


@test
async def ptz_goto_preset_public_client_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test ptz_goto_preset service when ptz_goto_preset_public raises ClientError."""
    ptz_camera = _make_ptz_camera()
    try:
        ptz_camera.get_ptz_presets.return_value = _make_presets()
        ptz_camera.get_ptz_patrols.return_value = []
        await init_entry(hass, ufp, [ptz_camera])

        camera_entry = entity_registry.async_get(
            "camera.ptz_camera_high_resolution_channel"
        )

        with patch_ufp_method(
            ptz_camera,
            "ptz_goto_preset_public",
            new_callable=AsyncMock,
            side_effect=ClientError("Connection failed"),
        ):
            async with expect_raises_async(HomeAssistantError):
                await hass.services.async_call(
                    DOMAIN,
                    SERVICE_PTZ_GOTO_PRESET,
                    {ATTR_DEVICE_ID: camera_entry.device_id, ATTR_PRESET: "Preset 1"},
                    blocking=True,
                )
    finally:
        Camera.model_config["validate_assignment"] = True


@test
async def ptz_goto_home_preset_client_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp_fx),
) -> None:
    """Test ptz_goto_preset service with home preset when ptz_goto_preset_public raises ClientError."""
    ptz_camera = _make_ptz_camera()
    try:
        ptz_camera.get_ptz_patrols.return_value = []
        await init_entry(hass, ufp, [ptz_camera])

        camera_entry = entity_registry.async_get(
            "camera.ptz_camera_high_resolution_channel"
        )

        with patch_ufp_method(
            ptz_camera,
            "ptz_goto_preset_public",
            new_callable=AsyncMock,
            side_effect=ClientError("Connection failed"),
        ):
            async with expect_raises_async(HomeAssistantError):
                await hass.services.async_call(
                    DOMAIN,
                    SERVICE_PTZ_GOTO_PRESET,
                    {ATTR_DEVICE_ID: camera_entry.device_id, ATTR_PRESET: "Home"},
                    blocking=True,
                )
    finally:
        Camera.model_config["validate_assignment"] = True
