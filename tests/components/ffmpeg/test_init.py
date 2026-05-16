"""The tests for Home Assistant ffmpeg."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import ffmpeg
from homeassistant.components.ffmpeg import DOMAIN, get_ffmpeg_manager
from homeassistant.components.ffmpeg.services import (
    SERVICE_RESTART,
    SERVICE_START,
    SERVICE_STOP,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.setup import async_setup_component

from tests.common import assert_setup_component
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor() -> int:
    return 0


@callback
def async_start(hass: HomeAssistant, entity_id: str | None = None) -> None:
    """Start a FFmpeg process on entity.

    This is a legacy helper method. Do not use it for new tests.
    """
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    hass.async_create_task(hass.services.async_call(DOMAIN, SERVICE_START, data))


@callback
def async_stop(hass: HomeAssistant, entity_id: str | None = None) -> None:
    """Stop a FFmpeg process on entity.

    This is a legacy helper method. Do not use it for new tests.
    """
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    hass.async_create_task(hass.services.async_call(DOMAIN, SERVICE_STOP, data))


@callback
def async_restart(hass: HomeAssistant, entity_id: str | None = None) -> None:
    """Restart a FFmpeg process on entity.

    This is a legacy helper method. Do not use it for new tests.
    """
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
    hass.async_create_task(hass.services.async_call(DOMAIN, SERVICE_RESTART, data))


class MockFFmpegDev(ffmpeg.FFmpegBase):
    """FFmpeg device mock."""

    def __init__(
        self,
        hass: HomeAssistant,
        initial_state: bool = True,
        entity_id: str = "test.ffmpeg_device",
    ) -> None:
        """Initialize mock."""
        super().__init__(None, initial_state)

        self.hass = hass
        self.entity_id = entity_id
        self.ffmpeg = MagicMock()
        self.called_stop = False
        self.called_start = False
        self.called_restart = False
        self.called_entities = None

    async def _async_start_ffmpeg(self, entity_ids):
        """Mock start."""
        self.called_start = True
        self.called_entities = entity_ids

    async def _async_stop_ffmpeg(self, entity_ids):
        """Mock stop."""
        self.called_stop = True
        self.called_entities = entity_ids


@test
async def setup_component(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up ffmpeg component."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    expect(hass.data[ffmpeg.DATA_FFMPEG].binary).to_equal("ffmpeg")


@test
async def setup_component_test_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up ffmpeg component test services."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    expect(hass.services.has_service(DOMAIN, "start")).to_be(True)
    expect(hass.services.has_service(DOMAIN, "stop")).to_be(True)
    expect(hass.services.has_service(DOMAIN, "restart")).to_be(True)


@test
async def setup_component_test_register(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up ffmpeg component test register."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    ffmpeg_dev = MockFFmpegDev(hass)
    ffmpeg_dev._async_stop_ffmpeg = AsyncMock()
    ffmpeg_dev._async_start_ffmpeg = AsyncMock()
    await ffmpeg_dev.async_added_to_hass()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    expect(len(ffmpeg_dev._async_start_ffmpeg.mock_calls)).to_equal(2)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    expect(len(ffmpeg_dev._async_stop_ffmpeg.mock_calls)).to_equal(2)


@test
async def setup_component_test_register_no_startup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up ffmpeg component test register without startup."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    ffmpeg_dev = MockFFmpegDev(hass, False)
    ffmpeg_dev._async_stop_ffmpeg = AsyncMock()
    ffmpeg_dev._async_start_ffmpeg = AsyncMock()
    await ffmpeg_dev.async_added_to_hass()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    expect(len(ffmpeg_dev._async_start_ffmpeg.mock_calls)).to_equal(1)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    expect(len(ffmpeg_dev._async_stop_ffmpeg.mock_calls)).to_equal(2)


@test
async def setup_component_test_service_start(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up ffmpeg component test service start."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    ffmpeg_dev = MockFFmpegDev(hass, False)
    await ffmpeg_dev.async_added_to_hass()

    async_start(hass)
    await hass.async_block_till_done()

    expect(ffmpeg_dev.called_start).to_be(True)


@test
async def setup_component_test_service_stop(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up ffmpeg component test service stop."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    ffmpeg_dev = MockFFmpegDev(hass, False)
    await ffmpeg_dev.async_added_to_hass()

    async_stop(hass)
    await hass.async_block_till_done()

    expect(ffmpeg_dev.called_stop).to_be(True)


@test
async def setup_component_test_service_restart(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up ffmpeg component test service restart."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    ffmpeg_dev = MockFFmpegDev(hass, False)
    await ffmpeg_dev.async_added_to_hass()

    async_restart(hass)
    await hass.async_block_till_done()

    expect(ffmpeg_dev.called_stop).to_be(True)
    expect(ffmpeg_dev.called_start).to_be(True)


@test
async def setup_component_test_service_start_with_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up ffmpeg component test service start."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    ffmpeg_dev = MockFFmpegDev(hass, False)
    await ffmpeg_dev.async_added_to_hass()

    async_start(hass, "test.ffmpeg_device")
    await hass.async_block_till_done()

    expect(ffmpeg_dev.called_start).to_be(True)
    expect(ffmpeg_dev.called_entities).to_equal(["test.ffmpeg_device"])


@test
async def async_get_image_with_width_height(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test fetching an image with a specific width and height."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    get_image_mock = AsyncMock()
    with patch(
        "homeassistant.components.ffmpeg.ImageFrame",
        return_value=Mock(get_image=get_image_mock),
    ):
        await ffmpeg.async_get_image(hass, "rtsp://fake", width=640, height=480)

    expect(get_image_mock.call_args_list).to_equal(
        [call("rtsp://fake", output_format="mjpeg", extra_cmd="-s 640x480")]
    )


@test
async def async_get_image_with_extra_cmd_overlapping_width_height(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test fetching an image with extra_cmd width/height plus specific width/height."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    get_image_mock = AsyncMock()
    with patch(
        "homeassistant.components.ffmpeg.ImageFrame",
        return_value=Mock(get_image=get_image_mock),
    ):
        await ffmpeg.async_get_image(
            hass, "rtsp://fake", extra_cmd="-s 1024x768", width=640, height=480
        )

    expect(get_image_mock.call_args_list).to_equal(
        [call("rtsp://fake", output_format="mjpeg", extra_cmd="-s 1024x768")]
    )


@test
async def async_get_image_with_extra_cmd_width_height(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test fetching an image with extra_cmd and a specific width and height."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    get_image_mock = AsyncMock()
    with patch(
        "homeassistant.components.ffmpeg.ImageFrame",
        return_value=Mock(get_image=get_image_mock),
    ):
        await ffmpeg.async_get_image(
            hass, "rtsp://fake", extra_cmd="-vf any", width=640, height=480
        )

    expect(get_image_mock.call_args_list).to_equal(
        [call("rtsp://fake", output_format="mjpeg", extra_cmd="-vf any -s 640x480")]
    )


@test
async def modern_ffmpeg(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test modern ffmpeg uses the new ffmpeg content type."""
    with assert_setup_component(1):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    manager = get_ffmpeg_manager(hass)
    expect("ffmpeg" in manager.ffmpeg_stream_content_type).to_be(True)


@test
async def legacy_ffmpeg(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test legacy ffmpeg uses the old ffserver content type."""
    with (
        assert_setup_component(1),
        patch(
            "homeassistant.components.ffmpeg.FFVersion.get_version", return_value="3.0"
        ),
        patch("homeassistant.components.ffmpeg.is_official_image", return_value=False),
    ):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    manager = get_ffmpeg_manager(hass)
    expect("ffserver" in manager.ffmpeg_stream_content_type).to_be(True)


@test
async def ffmpeg_using_official_image(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test ffmpeg using official image is the new ffmpeg content type."""
    with (
        assert_setup_component(1),
        patch("homeassistant.components.ffmpeg.is_official_image", return_value=True),
    ):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})

    manager = get_ffmpeg_manager(hass)
    expect("ffmpeg" in manager.ffmpeg_stream_content_type).to_be(True)
