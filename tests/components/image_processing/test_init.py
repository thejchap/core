"""The tests for the image_processing component."""

from collections.abc import Generator
import socket
from unittest.mock import PropertyMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import loader
from homeassistant.components import http, image_processing as ip
from homeassistant.const import ATTR_ENTITY_PICTURE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component

from . import common

from tests.common import assert_setup_component, async_capture_events
from tests.hass_fixtures import (
    LogCapture,
    aioclient_mock as aioclient_mock_fixture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async  # noqa: F401
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> int:
    """Anchor fixture: ensure mocks are active and homeassistant component is loaded."""
    await async_setup_component(hass, "homeassistant", {})
    return 0


@fixture
def enable_custom_integrations(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)
    yield


def _unused_tcp_port() -> int:
    """Return a free TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def get_url(hass: HomeAssistant) -> str:
    """Return camera url."""
    state = hass.states.get("camera.demo_camera")
    return f"{hass.config.internal_url}{state.attributes.get(ATTR_ENTITY_PICTURE)}"


async def setup_image_processing(hass: HomeAssistant) -> None:
    """Set up things to be run when tests are started."""
    await async_setup_component(
        hass,
        http.DOMAIN,
        {http.DOMAIN: {http.CONF_SERVER_PORT: _unused_tcp_port()}},
    )

    config = {ip.DOMAIN: {"platform": "test"}, "camera": {"platform": "demo"}}

    await async_setup_component(hass, ip.DOMAIN, config)
    await hass.async_block_till_done()


async def setup_image_processing_face(hass: HomeAssistant):
    """Set up things to be run when tests are started."""
    config = {ip.DOMAIN: {"platform": "demo"}, "camera": {"platform": "demo"}}

    await async_setup_component(hass, ip.DOMAIN, config)
    await hass.async_block_till_done()

    return async_capture_events(hass, "image_processing.detect_face")


@test
async def setup_component(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up demo platform on image_process component."""
    config = {ip.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, ip.DOMAIN):
        expect(await async_setup_component(hass, ip.DOMAIN, config)).to_be_truthy()
        await hass.async_block_till_done()


@test
async def setup_component_with_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Set up demo platform on image_process component test service."""
    config = {ip.DOMAIN: {"platform": "demo"}}

    with assert_setup_component(1, ip.DOMAIN):
        expect(await async_setup_component(hass, ip.DOMAIN, config)).to_be_truthy()
        await hass.async_block_till_done()

    expect(hass.services.has_service(ip.DOMAIN, "scan")).to_be_truthy()


@test
async def get_image_from_camera(
    _custom: None = Depends(enable_custom_integrations),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Grab an image from camera entity."""
    with patch(
        "homeassistant.components.demo.camera.Path.read_bytes",
        return_value=b"Test",
    ) as mock_camera_read:
        await setup_image_processing(hass)

        common.async_scan(hass, entity_id="image_processing.test")
        await hass.async_block_till_done()

        state = hass.states.get("image_processing.test")

        expect(mock_camera_read.called).to_be_truthy()
        expect(state.state).to_equal("1")
        expect(state.attributes["image"]).to_equal(b"Test")


@test
async def get_image_without_exists_camera(
    _custom: None = Depends(enable_custom_integrations),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Try to get image without exists camera."""
    with patch(
        "homeassistant.components.image_processing.async_get_image",
        side_effect=HomeAssistantError(),
    ) as mock_image:
        await setup_image_processing(hass)

        hass.states.async_remove("camera.demo_camera")

        common.async_scan(hass, entity_id="image_processing.test")
        await hass.async_block_till_done()

        state = hass.states.get("image_processing.test")

        expect(mock_image.called).to_be_truthy()
        expect(state.state).to_equal("0")


@test
async def face_event_call(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up and scan a picture and test faces from event."""
    face_events = await setup_image_processing_face(hass)
    aioclient_mock.get(get_url(hass), content=b"image")

    common.async_scan(hass, entity_id="image_processing.demo_face")
    await hass.async_block_till_done()

    state = hass.states.get("image_processing.demo_face")

    expect(len(face_events)).to_equal(2)
    expect(state.state).to_equal("Hans")
    expect(state.attributes["total_faces"]).to_equal(4)

    event_data = [
        event.data for event in face_events if event.data.get("name") == "Hans"
    ]
    expect(len(event_data)).to_equal(1)
    expect(event_data[0]["name"]).to_equal("Hans")
    expect(event_data[0]["confidence"]).to_equal(98.34)
    expect(event_data[0]["gender"]).to_equal("male")
    expect(event_data[0]["entity_id"]).to_equal("image_processing.demo_face")


@test
async def face_event_call_no_confidence(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up and scan a picture and test faces from event."""
    with patch(
        "homeassistant.components.demo.image_processing.DemoImageProcessingFace.confidence",
        new_callable=PropertyMock(return_value=None),
    ):
        face_events = await setup_image_processing_face(hass)
        aioclient_mock.get(get_url(hass), content=b"image")

        common.async_scan(hass, entity_id="image_processing.demo_face")
        await hass.async_block_till_done()

        state = hass.states.get("image_processing.demo_face")

        expect(len(face_events)).to_equal(3)
        expect(state.state).to_equal("4")
        expect(state.attributes["total_faces"]).to_equal(4)

        event_data = [
            event.data for event in face_events if event.data.get("name") == "Hans"
        ]
        expect(len(event_data)).to_equal(1)
        expect(event_data[0]["name"]).to_equal("Hans")
        expect(event_data[0]["confidence"]).to_equal(98.34)
        expect(event_data[0]["gender"]).to_equal("male")
        expect(event_data[0]["entity_id"]).to_equal("image_processing.demo_face")


@test
async def update_missing_camera(
    _custom: None = Depends(enable_custom_integrations),
    hass: HomeAssistant = Depends(hass_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test when entity does not set camera."""
    await setup_image_processing(hass)

    with patch(
        "custom_components.test.image_processing.TestImageProcessing.camera_entity",
        new_callable=PropertyMock(return_value=None),
    ):
        common.async_scan(hass, entity_id="image_processing.test")
        await hass.async_block_till_done()

    expect(
        "No camera entity id was set by the image processing entity" in caplog.text
    ).to_be_truthy()
