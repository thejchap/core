"""The tests for the camera component (tryke port)."""

from collections.abc import Callable
from http import HTTPStatus
import io
from unittest.mock import ANY, AsyncMock, Mock, PropertyMock, mock_open, patch

from tryke import Depends, expect, fixture, test
from webrtc_models import RTCIceCandidateInit

from homeassistant.components import camera
from homeassistant.components.camera import (
    Camera,
    CameraWebRTCProvider,
    WebRTCAnswer,
    WebRTCSendMessage,
    async_register_webrtc_provider,
)
from homeassistant.components.camera.const import (
    DOMAIN,
    PREF_ORIENTATION,
    PREF_PRELOAD_STREAM,
    StreamType,
)
from homeassistant.components.camera.helper import get_camera_from_entity_id
from homeassistant.components.websocket_api import TYPE_RESULT
from homeassistant.const import (
    ATTR_ENTITY_ID,
    EVENT_HOMEASSISTANT_STARTED,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.core_config import async_process_ha_core_config
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import (
    image_mock_url,
    mock_camera,
    mock_create_stream,
    mock_stream,
    mock_stream_source,
    mock_test_webrtc_cameras,
    register_test_provider,
)
from .common import EMPTY_8_6_JPEG, STREAM_SOURCE, mock_turbo_jpeg

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    hass_read_only_access_token as hass_read_only_access_token_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import ClientSessionGenerator, WebSocketGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def get_image_from_camera(
    hass: HomeAssistant = Depends(hass_fixture),
    _image_mock_url: None = Depends(image_mock_url),
) -> None:
    """Grab an image from camera entity."""
    with patch(
        "homeassistant.components.demo.camera.Path.read_bytes",
        autospec=True,
        return_value=b"Test",
    ) as mock_camera:
        image = await camera.async_get_image(hass, "camera.demo_camera")

    expect(mock_camera.called).to_be_truthy()
    expect(image.content).to_equal(b"Test")


@test
async def get_image_from_camera_with_width_height(
    hass: HomeAssistant = Depends(hass_fixture),
    _image_mock_url: None = Depends(image_mock_url),
) -> None:
    """Grab an image from camera entity with width and height."""
    turbo_jpeg = mock_turbo_jpeg(
        first_width=16, first_height=12, second_width=300, second_height=200
    )
    with (
        patch(
            "homeassistant.components.camera.img_util.TurboJPEGSingleton.instance",
            return_value=turbo_jpeg,
        ),
        patch(
            "homeassistant.components.demo.camera.Path.read_bytes",
            autospec=True,
            return_value=b"Test",
        ) as mock_camera,
    ):
        image = await camera.async_get_image(
            hass, "camera.demo_camera", width=640, height=480
        )

    expect(mock_camera.called).to_be_truthy()
    expect(image.content).to_equal(b"Test")


@test
async def get_image_from_camera_with_width_height_scaled(
    hass: HomeAssistant = Depends(hass_fixture),
    _image_mock_url: None = Depends(image_mock_url),
) -> None:
    """Grab an image from camera entity with width and height and scale it."""
    turbo_jpeg = mock_turbo_jpeg(
        first_width=16, first_height=12, second_width=300, second_height=200
    )
    with (
        patch(
            "homeassistant.components.camera.img_util.TurboJPEGSingleton.instance",
            return_value=turbo_jpeg,
        ),
        patch(
            "homeassistant.components.demo.camera.Path.read_bytes",
            autospec=True,
            return_value=b"Valid jpeg",
        ) as mock_camera,
    ):
        image = await camera.async_get_image(
            hass, "camera.demo_camera", width=4, height=3
        )

    expect(mock_camera.called).to_be_truthy()
    expect(image.content_type).to_equal("image/jpg")
    expect(image.content).to_equal(EMPTY_8_6_JPEG)


@test
async def get_image_from_camera_not_jpeg(
    hass: HomeAssistant = Depends(hass_fixture),
    _image_mock_url: None = Depends(image_mock_url),
) -> None:
    """Grab an image from camera entity that we cannot scale."""
    turbo_jpeg = mock_turbo_jpeg(
        first_width=16, first_height=12, second_width=300, second_height=200
    )
    with (
        patch(
            "homeassistant.components.camera.img_util.TurboJPEGSingleton.instance",
            return_value=turbo_jpeg,
        ),
        patch(
            "homeassistant.components.demo.camera.Path.read_bytes",
            autospec=True,
            return_value=b"png",
        ) as mock_camera,
    ):
        image = await camera.async_get_image(
            hass, "camera.demo_camera_png", width=4, height=3
        )

    expect(mock_camera.called).to_be_truthy()
    expect(image.content_type).to_equal("image/png")
    expect(image.content).to_equal(b"png")


@test
async def get_stream_source_from_camera(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    mock_stream_source: AsyncMock = Depends(mock_stream_source),
) -> None:
    """Fetch stream source from camera entity."""
    stream_source = await camera.async_get_stream_source(hass, "camera.demo_camera")

    expect(mock_stream_source.called).to_be_truthy()
    expect(stream_source).to_equal(STREAM_SOURCE)


@test
async def get_image_without_exists_camera(
    hass: HomeAssistant = Depends(hass_fixture),
    _image_mock_url: None = Depends(image_mock_url),
) -> None:
    """Try to get image without exists camera."""
    with patch(
        "homeassistant.helpers.entity_component.EntityComponent.get_entity",
        return_value=None,
    ):
        async with expect_raises_async(HomeAssistantError):
            await camera.async_get_image(hass, "camera.demo_camera")


@test
async def get_image_with_timeout(
    hass: HomeAssistant = Depends(hass_fixture),
    _image_mock_url: None = Depends(image_mock_url),
) -> None:
    """Try to get image with timeout."""
    with patch(
        "homeassistant.components.demo.camera.DemoCamera.async_camera_image",
        side_effect=TimeoutError,
    ):
        async with expect_raises_async(HomeAssistantError):
            await camera.async_get_image(hass, "camera.demo_camera")


@test
async def get_image_fails(
    hass: HomeAssistant = Depends(hass_fixture),
    _image_mock_url: None = Depends(image_mock_url),
) -> None:
    """Try to get image when camera returns None."""
    with patch(
        "homeassistant.components.demo.camera.DemoCamera.async_camera_image",
        return_value=None,
    ):
        async with expect_raises_async(HomeAssistantError):
            await camera.async_get_image(hass, "camera.demo_camera")


@test
async def snapshot_service(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
) -> None:
    """Test snapshot service."""
    mopen = mock_open()

    with (
        patch("homeassistant.components.camera.open", mopen, create=True),
        patch("homeassistant.components.camera.os.makedirs"),
        patch.object(hass.config, "is_allowed_path", return_value=True),
    ):
        await hass.services.async_call(
            camera.DOMAIN,
            camera.SERVICE_SNAPSHOT,
            {
                ATTR_ENTITY_ID: "camera.demo_camera",
                camera.ATTR_FILENAME: "/test/snapshot.jpg",
            },
            blocking=True,
        )

        mopen.assert_called_once_with("/test/snapshot.jpg", "wb")

        mock_write = mopen().write

        expect(len(mock_write.mock_calls)).to_equal(1)
        expect(mock_write.mock_calls[0][1][0]).to_equal(b"Test")


@test.skip(
    "parametrized snapshot assertion - syrupy index does not match pytest .ambr keys"
)
async def snapshot_service_filename_template() -> None:
    """Test snapshot service with filename templates (snapshot port deferred)."""


@test
async def snapshot_service_not_allowed_path(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
) -> None:
    """Test snapshot service with a not allowed path."""
    mopen = mock_open()

    with (
        patch("homeassistant.components.camera.open", mopen, create=True),
        patch("homeassistant.components.camera.os.makedirs"),
    ):
        async with expect_raises_async(
            HomeAssistantError,
            match="Cannot write `/test/snapshot.jpg`, no access to path",
        ):
            await hass.services.async_call(
                camera.DOMAIN,
                camera.SERVICE_SNAPSHOT,
                {
                    ATTR_ENTITY_ID: "camera.demo_camera",
                    camera.ATTR_FILENAME: "/test/snapshot.jpg",
                },
                blocking=True,
            )


@test.cases(
    test.case(
        "makedirs_oserror",
        target="homeassistant.components.camera.os.makedirs",
        side_effect=OSError,
    ),
    test.case(
        "camera_image_timeout",
        target="homeassistant.components.demo.camera.DemoCamera.async_camera_image",
        side_effect=TimeoutError,
    ),
)
async def snapshot_service_error(
    target: str,
    side_effect: type[Exception],
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
) -> None:
    """Test snapshot service with error."""
    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch(target, side_effect=side_effect),
    ):
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                camera.DOMAIN,
                camera.SERVICE_SNAPSHOT,
                {
                    ATTR_ENTITY_ID: "camera.demo_camera",
                    camera.ATTR_FILENAME: "/test/snapshot.jpg",
                },
                blocking=True,
            )


@test.skip("requires stream component (no 'av' module in this environment)")
async def websocket_stream_no_source(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    _mock_stream: None = Depends(mock_stream),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test camera/stream websocket command with camera with no source."""
    await async_setup_component(hass, "camera", {})

    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 6, "type": "camera/stream", "entity_id": "camera.demo_camera"}
    )
    msg = await client.receive_json()

    expect(msg["id"]).to_equal(6)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_falsy()


@test.skip("requires stream component (no 'av' module in this environment)")
async def websocket_camera_stream(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    _mock_stream: None = Depends(mock_stream),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    mock_create_stream: Mock = Depends(mock_create_stream),
) -> None:
    """Test camera/stream websocket command."""
    await async_setup_component(hass, "camera", {})

    with patch(
        "homeassistant.components.demo.camera.DemoCamera.stream_source",
        return_value="http://example.com",
    ):
        client = await hass_ws_client(hass)
        await client.send_json(
            {"id": 6, "type": "camera/stream", "entity_id": "camera.demo_camera"}
        )
        msg = await client.receive_json()

        expect(mock_create_stream.endpoint_url.called).to_be_truthy()
        expect(msg["id"]).to_equal(6)
        expect(msg["type"]).to_equal(TYPE_RESULT)
        expect(msg["success"]).to_be_truthy()
        expect(msg["result"]["url"][-13:]).to_equal("playlist.m3u8")


@test
async def websocket_get_prefs(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test get camera preferences websocket command."""
    await async_setup_component(hass, "camera", {})

    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 7, "type": "camera/get_prefs", "entity_id": "camera.demo_camera"}
    )
    msg = await client.receive_json()

    expect(msg["success"]).to_be_truthy()


@test
async def websocket_update_prefs_requires_admin(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fixture),
) -> None:
    """Test updating camera preferences requires admin."""
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json(
        {
            "id": 7,
            "type": "camera/update_prefs",
            "entity_id": "camera.demo_camera",
            "preload_stream": True,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_falsy()
    expect(msg["error"]["code"]).to_equal("unauthorized")


@test
async def websocket_update_preload_prefs(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test updating camera preferences."""
    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 7, "type": "camera/get_prefs", "entity_id": "camera.demo_camera"}
    )
    msg = await client.receive_json()

    expect(msg["success"]).to_be_truthy()
    expect(msg["result"][PREF_PRELOAD_STREAM]).to_be(False)

    await client.send_json(
        {
            "id": 8,
            "type": "camera/update_prefs",
            "entity_id": "camera.demo_camera",
            "preload_stream": True,
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be_truthy()
    expect(msg["result"][PREF_PRELOAD_STREAM]).to_be(True)

    await client.send_json(
        {"id": 9, "type": "camera/get_prefs", "entity_id": "camera.demo_camera"}
    )
    msg = await client.receive_json()
    expect(msg["result"][PREF_PRELOAD_STREAM]).to_be(True)


@test
async def websocket_update_orientation_prefs(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test updating camera preferences."""
    await async_setup_component(hass, "homeassistant", {})

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 10,
            "type": "camera/update_prefs",
            "entity_id": "camera.demo_uniquecamera",
            "orientation": 3,
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be_falsy()
    expect(response["error"]["code"]).to_equal("update_failed")

    expect(entity_registry.async_get("camera.demo_uniquecamera")).to_be_falsy()
    entity_registry.async_get_or_create(DOMAIN, "demo", "uniquecamera")
    entity_registry.async_update_entity_options(
        "camera.demo_uniquecamera",
        DOMAIN,
        {},
    )

    await client.send_json(
        {
            "id": 11,
            "type": "camera/update_prefs",
            "entity_id": "camera.demo_uniquecamera",
            "orientation": 3,
        }
    )
    response = await client.receive_json()
    expect(response["success"]).to_be_truthy()

    er_camera_prefs = entity_registry.async_get("camera.demo_uniquecamera").options[
        DOMAIN
    ]
    expect(er_camera_prefs[PREF_ORIENTATION]).to_equal(camera.Orientation.ROTATE_180)
    expect(response["result"][PREF_ORIENTATION]).to_equal(
        er_camera_prefs[PREF_ORIENTATION]
    )
    await client.send_json(
        {"id": 12, "type": "camera/get_prefs", "entity_id": "camera.demo_uniquecamera"}
    )
    msg = await client.receive_json()
    expect(msg["result"]["orientation"]).to_equal(camera.Orientation.ROTATE_180)


@test.skip("requires stream component (no 'av' module in this environment)")
async def play_stream_service_no_source(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    _mock_stream: None = Depends(mock_stream),
) -> None:
    """Test camera play_stream service."""
    data = {
        ATTR_ENTITY_ID: "camera.demo_camera",
        camera.ATTR_MEDIA_PLAYER: "media_player.test",
    }
    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            camera.DOMAIN, camera.SERVICE_PLAY_STREAM, data, blocking=True
        )


@test.skip("requires stream component (no 'av' module in this environment)")
async def handle_play_stream_service(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    _mock_stream: None = Depends(mock_stream),
    mock_create_stream: Mock = Depends(mock_create_stream),
) -> None:
    """Test camera play_stream service."""
    await async_process_ha_core_config(
        hass,
        {"external_url": "https://example.com"},
    )
    await async_setup_component(hass, "media_player", {})
    with patch(
        "homeassistant.components.demo.camera.DemoCamera.stream_source",
        return_value="http://example.com",
    ):
        await hass.services.async_call(
            camera.DOMAIN,
            camera.SERVICE_PLAY_STREAM,
            {
                ATTR_ENTITY_ID: "camera.demo_camera",
                camera.ATTR_MEDIA_PLAYER: "media_player.test",
            },
            blocking=True,
        )
        expect(mock_create_stream.endpoint_url.called).to_be_truthy()


@test.skip("requires stream component (no 'av' module in this environment)")
async def no_preload_stream(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stream: None = Depends(mock_stream),
    mock_create_stream: Mock = Depends(mock_create_stream),
) -> None:
    """Test camera preload preference."""
    demo_settings = camera.DynamicStreamSettings()
    with (
        patch(
            "homeassistant.components.camera.prefs.CameraPreferences.get_dynamic_stream_settings",
            return_value=demo_settings,
        ),
        patch(
            "homeassistant.components.demo.camera.DemoCamera.stream_source",
            new_callable=PropertyMock,
        ) as mock_stream_source,
    ):
        mock_stream_source.return_value = io.BytesIO()
        await async_setup_component(hass, "camera", {DOMAIN: {"platform": "demo"}})
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()
        expect(mock_create_stream.endpoint_url.called).to_be_falsy()


@test.skip("requires stream component (no 'av' module in this environment)")
async def preload_stream(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_stream: None = Depends(mock_stream),
    mock_create_stream: Mock = Depends(mock_create_stream),
) -> None:
    """Test camera preload preference."""
    demo_settings = camera.DynamicStreamSettings(preload_stream=True)
    with (
        patch(
            "homeassistant.components.camera.prefs.CameraPreferences.get_dynamic_stream_settings",
            return_value=demo_settings,
        ),
        patch(
            "homeassistant.components.demo.camera.DemoCamera.stream_source",
            return_value="http://example.com",
        ),
    ):
        assert await async_setup_component(
            hass, "camera", {DOMAIN: {"platform": "demo"}}
        )
        await hass.async_block_till_done()
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()
        expect(mock_create_stream.start.called).to_be_truthy()


@test
async def record_service_invalid_path(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
) -> None:
    """Test record service with invalid path."""
    with patch.object(hass.config, "is_allowed_path", return_value=False):
        async with expect_raises_async(HomeAssistantError):
            await hass.services.async_call(
                camera.DOMAIN,
                camera.SERVICE_RECORD,
                {
                    ATTR_ENTITY_ID: "camera.demo_camera",
                    camera.CONF_FILENAME: "/my/invalid/path",
                },
                blocking=True,
            )


@test.skip("requires stream component (no 'av' module in this environment)")
async def record_service() -> None:
    """Test record service (requires stream component)."""


@test
async def camera_proxy_stream(
    _mock_camera: None = Depends(mock_camera),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test camera proxy stream."""
    client = await hass_client()

    async with client.get("/api/camera_proxy_stream/camera.demo_camera") as response:
        expect(response.status).to_equal(HTTPStatus.OK)

    with patch(
        "homeassistant.components.demo.camera.DemoCamera.handle_async_mjpeg_stream",
        return_value=None,
    ):
        async with await client.get(
            "/api/camera_proxy_stream/camera.demo_camera"
        ) as response:
            expect(response.status).to_equal(HTTPStatus.BAD_GATEWAY)


@test
async def state_streaming(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
) -> None:
    """Camera state."""
    demo_camera = hass.states.get("camera.demo_camera")
    expect(demo_camera).not_.to_be_none()
    expect(demo_camera.state).to_equal(camera.CameraState.STREAMING)


@test.skip("requires stream component (no 'av' module in this environment)")
async def stream_unavailable(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    _mock_stream: None = Depends(mock_stream),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    mock_create_stream: Mock = Depends(mock_create_stream),
) -> None:
    """Camera state."""
    await async_setup_component(hass, "camera", {})

    with patch(
        "homeassistant.components.demo.camera.DemoCamera.stream_source",
        return_value="http://example.com",
    ):
        client = await hass_ws_client(hass)
        await client.send_json(
            {"id": 10, "type": "camera/stream", "entity_id": "camera.demo_camera"}
        )
        await client.receive_json()
        expect(mock_create_stream.set_update_callback.called).to_be_truthy()

    callback_fn = mock_create_stream.set_update_callback.call_args.args[0]
    mock_create_stream.available = False
    callback_fn()
    await hass.async_block_till_done()

    demo_camera = hass.states.get("camera.demo_camera")
    expect(demo_camera).not_.to_be_none()
    expect(demo_camera.state).to_equal(STATE_UNAVAILABLE)

    mock_create_stream.available = True
    callback_fn()
    await hass.async_block_till_done()

    demo_camera = hass.states.get("camera.demo_camera")
    expect(demo_camera).not_.to_be_none()
    expect(demo_camera.state).to_equal(camera.CameraState.STREAMING)


@test
async def use_stream_for_stills(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> None:
    """Test that the component can grab images from stream."""
    client = await hass_client()

    with (
        patch(
            "homeassistant.components.demo.camera.DemoCamera.stream_source",
            return_value=None,
        ) as mock_stream_source,
        patch(
            "homeassistant.components.demo.camera.DemoCamera.use_stream_for_stills",
            return_value=True,
        ),
    ):
        resp = await client.get("/api/camera_proxy/camera.demo_camera_without_stream")
        await hass.async_block_till_done()
        mock_stream_source.assert_not_called()
        expect(resp.status).to_equal(HTTPStatus.INTERNAL_SERVER_ERROR)

        resp = await client.get("/api/camera_proxy/camera.demo_camera")
        await hass.async_block_till_done()
        mock_stream_source.assert_called_once()
        expect(resp.status).to_equal(HTTPStatus.INTERNAL_SERVER_ERROR)

    with (
        patch(
            "homeassistant.components.demo.camera.DemoCamera.stream_source",
            return_value="rtsp://some_source",
        ) as mock_stream_source,
        patch("homeassistant.components.camera.create_stream") as mock_create_stream,
        patch(
            "homeassistant.components.demo.camera.DemoCamera.use_stream_for_stills",
            return_value=True,
        ),
    ):
        mock_stream = Mock()
        mock_stream.async_get_image = AsyncMock()
        mock_stream.async_get_image.return_value = b"stream_keyframe_image"
        mock_create_stream.return_value = mock_stream

        resp = await client.get("/api/camera_proxy/camera.demo_camera")
        await hass.async_block_till_done()
        mock_create_stream.assert_called_once()
        mock_stream.async_get_image.assert_called_once()
        expect(resp.status).to_equal(HTTPStatus.OK)
        expect(await resp.read()).to_equal(b"stream_keyframe_image")


@test
async def entity_picture_url_changes_on_token_update(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
) -> None:
    """Test the token is rotated and entity entity picture cache is cleared."""
    await async_setup_component(hass, "camera", {})
    await hass.async_block_till_done()

    camera_state = hass.states.get("camera.demo_camera")
    original_picture = camera_state.attributes["entity_picture"]
    expect("token=" in original_picture).to_be(True)

    async_fire_time_changed(hass, dt_util.utcnow() + camera.TOKEN_CHANGE_INTERVAL)
    await hass.async_block_till_done(wait_background_tasks=True)

    camera_state = hass.states.get("camera.demo_camera")
    new_entity_picture = camera_state.attributes["entity_picture"]
    expect(new_entity_picture != original_picture).to_be(True)
    expect("token=" in new_entity_picture).to_be(True)


async def _register_test_webrtc_provider(hass: HomeAssistant) -> Callable[[], None]:
    class SomeTestProvider(CameraWebRTCProvider):
        """Test provider."""

        @property
        def domain(self) -> str:
            """Return domain."""
            return "test"

        @callback
        def async_is_supported(self, stream_source: str) -> bool:
            """Determine if the provider supports the stream source."""
            return True

        async def async_handle_async_webrtc_offer(
            self,
            camera: Camera,
            offer_sdp: str,
            session_id: str,
            send_message: WebRTCSendMessage,
        ) -> None:
            """Handle the WebRTC offer and return the answer via the callback."""
            send_message(WebRTCAnswer("answer"))

        async def async_on_webrtc_candidate(
            self, session_id: str, candidate: RTCIceCandidateInit
        ) -> None:
            """Handle the WebRTC candidate."""

    provider = SomeTestProvider()
    unsub = async_register_webrtc_provider(hass, provider)
    await hass.async_block_till_done()
    return unsub


async def _test_capabilities(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entity_id: str,
    expected_stream_types: set[StreamType],
    expected_stream_types_with_webrtc_provider: set[StreamType],
) -> None:
    """Test camera capabilities."""
    await async_setup_component(hass, "camera", {})
    await hass.async_block_till_done()

    async def test(expected_types: set[StreamType]) -> None:
        camera_obj = get_camera_from_entity_id(hass, entity_id)
        capabilities = camera_obj.camera_capabilities
        expect(capabilities).to_equal(camera.CameraCapabilities(expected_types))

        client = await hass_ws_client(hass)
        await client.send_json_auto_id(
            {"type": "camera/capabilities", "entity_id": entity_id}
        )
        msg = await client.receive_json()

        expect(msg["type"]).to_equal(TYPE_RESULT)
        expect(msg["success"]).to_be_truthy()
        expect(msg["result"]).to_equal({"frontend_stream_types": ANY})
        expect(sorted(msg["result"]["frontend_stream_types"])).to_equal(
            sorted(expected_types)
        )

    await test(expected_stream_types)

    await _register_test_webrtc_provider(hass)
    await test(expected_stream_types_with_webrtc_provider)


@test
async def camera_capabilities_hls(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    _mock_stream_source: Mock = Depends(mock_stream_source),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test HLS camera capabilities."""
    await _test_capabilities(
        hass,
        hass_ws_client,
        "camera.demo_camera",
        {StreamType.HLS},
        {StreamType.HLS, StreamType.WEB_RTC},
    )


@test
async def camera_capabilities_webrtc(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test WebRTC camera capabilities."""
    await _test_capabilities(
        hass, hass_ws_client, "camera.async", {StreamType.WEB_RTC}, {StreamType.WEB_RTC}
    )


@test
async def webrtc_provider_not_added_for_native_webrtc(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    register_test_provider: object = Depends(register_test_provider),
) -> None:
    """Test no WebRTC provider added when camera has native WebRTC support."""
    camera_obj = get_camera_from_entity_id(hass, "camera.async")
    expect(camera_obj).to_be_truthy()
    expect(camera_obj._webrtc_provider).to_be_none()
    expect(camera_obj._supports_native_async_webrtc).to_be(True)


@test
async def camera_capabilities_changing_non_native_support(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    _mock_stream_source: Mock = Depends(mock_stream_source),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test WebRTC camera capabilities."""
    cam = get_camera_from_entity_id(hass, "camera.demo_camera")
    expect(cam.supported_features).to_equal(
        camera.CameraEntityFeature.ON_OFF | camera.CameraEntityFeature.STREAM
    )

    await _test_capabilities(
        hass,
        hass_ws_client,
        cam.entity_id,
        {StreamType.HLS},
        {StreamType.HLS, StreamType.WEB_RTC},
    )

    cam._attr_supported_features = camera.CameraEntityFeature(0)
    cam.async_write_ha_state()
    await hass.async_block_till_done()

    await _test_capabilities(hass, hass_ws_client, cam.entity_id, set(), set())


@test
async def camera_capabilities_changing_native_support(
    hass: HomeAssistant = Depends(hass_fixture),
    _cameras: None = Depends(mock_test_webrtc_cameras),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test WebRTC camera capabilities."""
    cam = get_camera_from_entity_id(hass, "camera.async")
    expect(cam.supported_features).to_equal(camera.CameraEntityFeature.STREAM)

    await _test_capabilities(
        hass, hass_ws_client, cam.entity_id, {StreamType.WEB_RTC}, {StreamType.WEB_RTC}
    )

    cam._attr_supported_features = camera.CameraEntityFeature(0)
    cam.async_write_ha_state()
    await hass.async_block_till_done()

    await _test_capabilities(hass, hass_ws_client, cam.entity_id, set(), set())


@test
async def snapshot_service_webrtc_provider(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_camera: None = Depends(mock_camera),
    _mock_stream_source: Mock = Depends(mock_stream_source),
) -> None:
    """Test snapshot service with the webrtc provider."""
    await async_setup_component(hass, "camera", {})
    await hass.async_block_till_done()
    unsub = await _register_test_webrtc_provider(hass)
    camera_obj = get_camera_from_entity_id(hass, "camera.demo_camera")
    expect(camera_obj._webrtc_provider).to_be_truthy()

    with (
        patch.object(camera_obj, "use_stream_for_stills", return_value=True),
        patch("homeassistant.components.camera.open"),
        patch.object(
            camera_obj._webrtc_provider,
            "async_get_image",
            wraps=camera_obj._webrtc_provider.async_get_image,
        ) as webrtc_get_image_mock,
        patch.object(camera_obj, "stream", AsyncMock()) as stream_mock,
        patch("homeassistant.components.camera.os.makedirs"),
        patch.object(hass.config, "is_allowed_path", return_value=True),
    ):
        await hass.services.async_call(
            camera.DOMAIN,
            camera.SERVICE_SNAPSHOT,
            {
                ATTR_ENTITY_ID: camera_obj.entity_id,
                camera.ATTR_FILENAME: "/test/snapshot.jpg",
            },
            blocking=True,
        )
        stream_mock.async_get_image.assert_called_once()
        webrtc_get_image_mock.assert_called_once_with(
            camera_obj, width=None, height=None
        )

        webrtc_get_image_mock.reset_mock()
        stream_mock.reset_mock()

        webrtc_get_image_mock.return_value = b"Images bytes"
        await hass.services.async_call(
            camera.DOMAIN,
            camera.SERVICE_SNAPSHOT,
            {
                ATTR_ENTITY_ID: camera_obj.entity_id,
                camera.ATTR_FILENAME: "/test/snapshot.jpg",
            },
            blocking=True,
        )
        stream_mock.async_get_image.assert_not_called()
        webrtc_get_image_mock.assert_called_once_with(
            camera_obj, width=None, height=None
        )

        unsub()
        await hass.async_block_till_done()
        expect(camera_obj._webrtc_provider).to_be_none()
        webrtc_get_image_mock.reset_mock()
        stream_mock.reset_mock()

        await hass.services.async_call(
            camera.DOMAIN,
            camera.SERVICE_SNAPSHOT,
            {
                ATTR_ENTITY_ID: camera_obj.entity_id,
                camera.ATTR_FILENAME: "/test/snapshot.jpg",
            },
            blocking=True,
        )
        stream_mock.async_get_image.assert_called_once()
        webrtc_get_image_mock.assert_not_called()
