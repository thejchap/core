"""Tryke fixtures for UniFi Protect tests."""

from collections.abc import Callable, Generator
from datetime import datetime, timedelta
from functools import partial
from ipaddress import IPv4Address
from pathlib import Path
from tempfile import gettempdir
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, fixture
from uiprotect import ProtectApiClient
from uiprotect.data import (
    NVR,
    AiPort,
    Bootstrap,
    Camera,
    Chime,
    CloudAccount,
    Doorlock,
    Light,
    Sensor,
    SmartDetectObjectType,
    VideoMode,
    WSSubscriptionMessage,
)
from uiprotect.websocket import WebsocketState

from homeassistant.components.unifiprotect.const import DOMAIN
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from . import _patch_discovery
from .utils import MockUFPFixture

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import hass as hass_fixture

DEFAULT_HOST = "1.1.1.1"
DEFAULT_PORT = 443
DEFAULT_VERIFY_SSL = False
DEFAULT_USERNAME = "test-username"
DEFAULT_PASSWORD = "test-password"
DEFAULT_API_KEY = "test-api-key"


@fixture
def mock_discovery() -> Generator[None]:
    """Prevent real network scanning in all unifiprotect tests."""
    with _patch_discovery(no_device=True):
        yield


@fixture
def nvr() -> Generator[NVR]:
    """Mock UniFi Protect NVR."""
    data = load_json_object_fixture("sample_nvr.json", DOMAIN)
    nvr = NVR.from_unifi_dict(**data)

    NVR.model_config["validate_assignment"] = False

    yield nvr

    NVR.model_config["validate_assignment"] = True


@fixture
def old_nvr() -> NVR:
    """Mock UniFi Protect NVR with old version."""
    data = load_json_object_fixture("sample_nvr.json", DOMAIN)
    data["version"] = "1.19.0"
    return NVR.from_unifi_dict(**data)


@fixture
def cloud_account() -> CloudAccount:
    """Return UI Cloud Account."""
    return CloudAccount(
        id="42",
        first_name="Test",
        last_name="User",
        email="test@example.com",
        user_id="42",
        name="Test User",
        location=None,
        profile_img=None,
    )


@fixture
def ufp_config_entry() -> MockConfigEntry:
    """Mock the unifiprotect config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: DEFAULT_HOST,
            CONF_USERNAME: DEFAULT_USERNAME,
            CONF_PASSWORD: DEFAULT_PASSWORD,
            CONF_API_KEY: DEFAULT_API_KEY,
            "id": "UnifiProtect",
            CONF_PORT: DEFAULT_PORT,
            CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
        },
        version=2,
        unique_id="A1E00C826924",
    )


@fixture
def bootstrap(nvr: NVR = Depends(nvr)) -> Bootstrap:
    """Mock Bootstrap fixture."""
    data = load_json_object_fixture("sample_bootstrap.json", DOMAIN)
    data["nvr"] = nvr
    data["cameras"] = []
    data["lights"] = []
    data["sensors"] = []
    data["viewers"] = []
    data["liveviews"] = []
    data["events"] = []
    data["doorlocks"] = []
    data["chimes"] = []
    data["aiports"] = []
    return Bootstrap.from_unifi_dict(**data)


@fixture
def ufp_client(bootstrap: Bootstrap = Depends(bootstrap)) -> Any:
    """Mock ProtectApiClient for testing."""
    client = Mock()
    client.bootstrap = bootstrap
    client._bootstrap = bootstrap
    client.api_path = "/api"
    client.cache_dir = Path(gettempdir()) / "ufp_cache"
    client._stream_response = partial(ProtectApiClient._stream_response, client)
    client.get_camera_video = partial(ProtectApiClient.get_camera_video, client)

    nvr_obj = client.bootstrap.nvr
    nvr_obj._api = client
    client.bootstrap._api = client

    client.base_url = "https://127.0.0.1"
    client.connection_host = IPv4Address("127.0.0.1")

    async def get_nvr(*args: Any, **kwargs: Any) -> NVR:
        return client.bootstrap.nvr

    client.get_nvr = get_nvr
    client.get_bootstrap = AsyncMock(return_value=bootstrap)
    client.update = AsyncMock(return_value=bootstrap)
    client.async_disconnect_ws = AsyncMock()
    client.has_public_bootstrap = False
    return client


@fixture
def ufp(
    _discovery: None = Depends(mock_discovery),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp_config_entry: MockConfigEntry = Depends(ufp_config_entry),
    ufp_client: Any = Depends(ufp_client),
) -> Generator[MockUFPFixture]:
    """Mock ProtectApiClient for testing."""
    with patch(
        "homeassistant.components.unifiprotect.utils.ProtectApiClient"
    ) as mock_api:
        ufp_config_entry.add_to_hass(hass)

        mock_api.return_value = ufp_client

        ufp = MockUFPFixture(ufp_config_entry, ufp_client)

        def subscribe(ws_callback: Callable[[WSSubscriptionMessage], None]) -> Any:
            ufp.ws_subscription = ws_callback
            return Mock()

        def subscribe_websocket_state(
            ws_state_subscription: Callable[[WebsocketState], None],
        ) -> Any:
            ufp.ws_state_subscription = ws_state_subscription
            return Mock()

        def subscribe_devices_websocket(
            ws_callback: Callable[[WSSubscriptionMessage], None],
        ) -> Any:
            ufp.devices_ws_subscription = ws_callback
            return Mock()

        ufp_client.subscribe_websocket = subscribe
        ufp_client.subscribe_websocket_state = subscribe_websocket_state
        ufp_client.subscribe_devices_websocket = subscribe_devices_websocket
        ufp_client.update_public = AsyncMock()
        ufp_client.has_public_bootstrap = False
        yield ufp


@fixture
def fixed_now() -> datetime:
    """Return datetime object that will be consistent throughout test."""
    return dt_util.utcnow()


@fixture
def camera(fixed_now: datetime = Depends(fixed_now)) -> Generator[Camera]:
    """Mock UniFi Protect Camera device."""
    Camera.model_config["validate_assignment"] = False

    data = load_json_object_fixture("sample_camera.json", DOMAIN)
    cam = Camera.from_unifi_dict(**data)
    cam.last_motion = fixed_now - timedelta(hours=1)

    yield cam

    Camera.model_config["validate_assignment"] = True


@fixture
def doorbell(
    camera: Camera = Depends(camera),
    fixed_now: datetime = Depends(fixed_now),
) -> Camera:
    """Mock UniFi Protect Camera device (with chime)."""
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
    doorbell.last_ring = fixed_now - timedelta(hours=1)
    return doorbell


@fixture
def unadopted_camera(camera: Camera = Depends(camera)) -> Camera:
    """Mock UniFi Protect Camera device (unadopted)."""
    no_camera = camera.model_copy()
    no_camera.channels = [c.model_copy() for c in no_camera.channels]
    no_camera.name = "Unadopted Camera"
    no_camera.is_adopted = False
    return no_camera


@fixture
def light() -> Generator[Light]:
    """Mock UniFi Protect Light device."""
    Light.model_config["validate_assignment"] = False

    data = load_json_object_fixture("sample_light.json", DOMAIN)
    yield Light.from_unifi_dict(**data)

    Light.model_config["validate_assignment"] = True


@fixture
def camera_all_features(
    fixed_now: datetime = Depends(fixed_now),
) -> Generator[Camera]:
    """Mock UniFi Protect Camera device with all features enabled."""
    Camera.model_config["validate_assignment"] = False

    data = load_json_object_fixture("sample_camera_all_features.json", DOMAIN)
    cam = Camera.from_unifi_dict(**data)
    cam.last_motion = fixed_now - timedelta(hours=1)

    yield cam

    Camera.model_config["validate_assignment"] = True


@fixture
def doorlock() -> Generator[Doorlock]:
    """Mock UniFi Protect Doorlock device."""
    Doorlock.model_config["validate_assignment"] = False

    data = load_json_object_fixture("sample_doorlock.json", DOMAIN)
    yield Doorlock.from_unifi_dict(**data)

    Doorlock.model_config["validate_assignment"] = True


@fixture
def chime() -> Generator[Chime]:
    """Mock UniFi Protect Chime device."""
    Chime.model_config["validate_assignment"] = False

    data = load_json_object_fixture("sample_chime.json", DOMAIN)
    yield Chime.from_unifi_dict(**data)

    Chime.model_config["validate_assignment"] = True


@fixture
def sensor(fixed_now: datetime = Depends(fixed_now)) -> Generator[Sensor]:
    """Mock UniFi Protect Sensor device."""
    Sensor.model_config["validate_assignment"] = False

    data = load_json_object_fixture("sample_sensor.json", DOMAIN)
    sensor_obj: Sensor = Sensor.from_unifi_dict(**data)
    sensor_obj.motion_detected_at = fixed_now - timedelta(hours=1)
    sensor_obj.open_status_changed_at = fixed_now - timedelta(hours=1)
    sensor_obj.alarm_triggered_at = fixed_now - timedelta(hours=1)
    yield sensor_obj

    Sensor.model_config["validate_assignment"] = True


@fixture
def sensor_all(sensor: Sensor = Depends(sensor)) -> Sensor:
    """Mock UniFi Protect Sensor device (all features enabled)."""
    all_sensor = sensor.model_copy()
    all_sensor.light_settings.is_enabled = True
    all_sensor.humidity_settings.is_enabled = True
    all_sensor.temperature_settings.is_enabled = True
    all_sensor.alarm_settings.is_enabled = True
    all_sensor.led_settings.is_enabled = True
    all_sensor.motion_settings.is_enabled = True
    return all_sensor


@fixture
def aiport() -> Generator[AiPort]:
    """Mock UniFi Protect AI Port device."""
    AiPort.model_config["validate_assignment"] = False

    data = load_json_object_fixture("sample_aiport.json", DOMAIN)
    yield AiPort.from_unifi_dict(**data)

    AiPort.model_config["validate_assignment"] = True
