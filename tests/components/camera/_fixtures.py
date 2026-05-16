"""Tryke fixtures for camera tests."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import Mock, patch

from tryke import Depends, fixture
from webrtc_models import RTCIceCandidateInit

from homeassistant.components import camera
from homeassistant.components.camera.webrtc import WebRTCAnswer, WebRTCSendMessage
from homeassistant.config_entries import ConfigEntry, ConfigFlow
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    MockModule,
    mock_config_flow,
    mock_integration,
    mock_platform,
    setup_test_component_platform,
)
from tests.hass_fixtures import hass as hass_fixture

from .common import STREAM_SOURCE, WEBRTC_ANSWER, SomeTestProvider


@fixture
async def setup_homeassistant(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up the homeassistant integration."""
    await async_setup_component(hass, "homeassistant", {})


@fixture
def camera_only() -> Generator[None]:
    """Enable only the camera platform on the demo integration."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.CAMERA],
    ):
        yield


@fixture
async def mock_camera(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_ha: None = Depends(setup_homeassistant),
    _camera_only: None = Depends(camera_only),
) -> AsyncGenerator[None]:
    """Initialize a demo camera platform."""
    assert await async_setup_component(
        hass, "camera", {camera.DOMAIN: {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    with patch(
        "homeassistant.components.demo.camera.Path.read_bytes",
        return_value=b"Test",
    ):
        yield


@fixture
def mock_stream_source() -> Generator[Mock]:
    """Fixture to create an RTSP stream source."""
    with patch(
        "homeassistant.components.camera.Camera.stream_source",
        return_value=STREAM_SOURCE,
    ) as mock_stream_source:
        yield mock_stream_source


@fixture
async def mock_test_webrtc_cameras(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_ha: None = Depends(setup_homeassistant),
    _camera_only: None = Depends(camera_only),
) -> None:
    """Initialize test WebRTC cameras with native RTC support."""

    class BaseCamera(camera.Camera):
        """Base Camera."""

        _attr_supported_features: camera.CameraEntityFeature = (
            camera.CameraEntityFeature.STREAM
        )

        async def stream_source(self) -> str | None:
            return STREAM_SOURCE

    class AsyncNoCandidateCamera(BaseCamera):
        """Mock Camera with native async WebRTC support but no candidate support."""

        _attr_name = "Async No Candidate"

        async def async_handle_async_webrtc_offer(
            self, offer_sdp: str, session_id: str, send_message: WebRTCSendMessage
        ) -> None:
            send_message(WebRTCAnswer(WEBRTC_ANSWER))

    class AsyncCamera(BaseCamera):
        """Mock Camera with native async WebRTC support."""

        _attr_name = "Async"

        async def async_handle_async_webrtc_offer(
            self, offer_sdp: str, session_id: str, send_message: WebRTCSendMessage
        ) -> None:
            send_message(WebRTCAnswer(WEBRTC_ANSWER))

        async def async_on_webrtc_candidate(
            self, session_id: str, candidate: RTCIceCandidateInit
        ) -> None:
            """Handle a WebRTC candidate."""

    domain = "test"

    entry = MockConfigEntry(domain=domain)
    entry.add_to_hass(hass)

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        await hass.config_entries.async_forward_entry_setups(
            config_entry, [Platform.CAMERA]
        )
        return True

    async def async_unload_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        await hass.config_entries.async_forward_entry_unload(
            config_entry, Platform.CAMERA
        )
        return True

    mock_integration(
        hass,
        MockModule(
            domain,
            async_setup_entry=async_setup_entry_init,
            async_unload_entry=async_unload_entry_init,
        ),
    )
    setup_test_component_platform(
        hass,
        camera.DOMAIN,
        [AsyncNoCandidateCamera(), AsyncCamera()],
        from_config_entry=True,
    )
    mock_platform(hass, f"{domain}.config_flow", Mock())

    with mock_config_flow(domain, ConfigFlow):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


@fixture
async def register_test_provider(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_ha: None = Depends(setup_homeassistant),
) -> AsyncGenerator[SomeTestProvider]:
    """Add WebRTC test provider."""
    await async_setup_component(hass, "camera", {})

    provider = SomeTestProvider()
    unsub = camera.async_register_webrtc_provider(hass, provider)
    await hass.async_block_till_done()
    yield provider
    unsub()
