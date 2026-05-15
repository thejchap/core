"""The tests for the openalpr cloud platform."""

from unittest.mock import PropertyMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import camera, image_processing as ip
from homeassistant.components.openalpr_cloud.image_processing import OPENALPR_API_URL
from homeassistant.core import Event, HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import (
    assert_setup_component,
    async_capture_events,
    async_load_fixture,
)
from tests.components.image_processing import common
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture; also sets up the homeassistant integration (autouse)."""
    await async_setup_component(hass, "homeassistant", {})
    return hass


@fixture
async def setup_openalpr_cloud(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Set up openalpr cloud."""
    config = {
        ip.DOMAIN: {
            "platform": "openalpr_cloud",
            "source": {"entity_id": "camera.demo_camera", "name": "test local"},
            "region": "eu",
            "api_key": "sk_abcxyz123456",
        },
        "camera": {"platform": "demo"},
    }

    with patch(
        "homeassistant.components.openalpr_cloud.image_processing."
        "OpenAlprCloudEntity.should_poll",
        new_callable=PropertyMock(return_value=False),
    ):
        await async_setup_component(hass, ip.DOMAIN, config)
        await hass.async_block_till_done()


@fixture
async def alpr_events(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> list[Event]:
    """Listen for events."""
    return async_capture_events(hass, "image_processing.found_plate")


PARAMS = {
    "secret_key": "sk_abcxyz123456",
    "tasks": "plate",
    "return_image": 0,
    "country": "eu",
}


@test.skip("demo camera platform setup is no longer supported (YAML deprecated)")
async def setup_platform() -> None:
    """Set up platform with one entity."""


@test.skip("demo camera platform setup is no longer supported (YAML deprecated)")
async def setup_platform_name() -> None:
    """Set up platform with one entity and set name."""


@test
async def setup_platform_without_api_key(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Set up platform with one entity without api_key."""
    config = {
        ip.DOMAIN: {
            "platform": "openalpr_cloud",
            "source": {"entity_id": "camera.demo_camera"},
            "region": "eu",
        },
        "camera": {"platform": "demo"},
    }

    with assert_setup_component(0, ip.DOMAIN):
        await async_setup_component(hass, ip.DOMAIN, config)
        await hass.async_block_till_done()


@test
async def setup_platform_without_region(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Set up platform with one entity without region."""
    config = {
        ip.DOMAIN: {
            "platform": "openalpr_cloud",
            "source": {"entity_id": "camera.demo_camera"},
            "api_key": "sk_abcxyz123456",
        },
        "camera": {"platform": "demo"},
    }

    with assert_setup_component(0, ip.DOMAIN):
        await async_setup_component(hass, ip.DOMAIN, config)
        await hass.async_block_till_done()


@test
async def openalpr_process_image(
    hass: HomeAssistant = Depends(_trigger_executor),
    events: list[Event] = Depends(alpr_events),
    _setup: None = Depends(setup_openalpr_cloud),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up and scan a picture and test plates from event."""
    aioclient_mock.post(
        OPENALPR_API_URL,
        params=PARAMS,
        text=await async_load_fixture(hass, "alpr_cloud.json", "openalpr_cloud"),
        status=200,
    )

    with patch(
        "homeassistant.components.camera.async_get_image",
        return_value=camera.Image("image/jpeg", b"image"),
    ):
        common.async_scan(hass, entity_id="image_processing.test_local")
        await hass.async_block_till_done()

    state = hass.states.get("image_processing.test_local")

    expect(len(aioclient_mock.mock_calls)).to_be(1)
    expect(len(events)).to_be(5)
    expect(state.attributes.get("vehicles")).to_equal(1)
    expect(state.state).to_equal("H786P0J")

    event_data = [
        event.data for event in events if event.data.get("plate") == "H786P0J"
    ]
    expect(len(event_data)).to_equal(1)
    expect(event_data[0]["plate"]).to_equal("H786P0J")
    expect(event_data[0]["confidence"]).to_equal(90.436699)
    expect(event_data[0]["entity_id"]).to_equal("image_processing.test_local")


@test
async def openalpr_process_image_api_error(
    hass: HomeAssistant = Depends(_trigger_executor),
    events: list[Event] = Depends(alpr_events),
    _setup: None = Depends(setup_openalpr_cloud),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up and scan a picture and test api error."""
    aioclient_mock.post(
        OPENALPR_API_URL,
        params=PARAMS,
        text="{'error': 'error message'}",
        status=400,
    )

    with patch(
        "homeassistant.components.camera.async_get_image",
        return_value=camera.Image("image/jpeg", b"image"),
    ):
        common.async_scan(hass, entity_id="image_processing.test_local")
        await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_be(1)
    expect(len(events)).to_be(0)


@test
async def openalpr_process_image_api_timeout(
    hass: HomeAssistant = Depends(_trigger_executor),
    events: list[Event] = Depends(alpr_events),
    _setup: None = Depends(setup_openalpr_cloud),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Set up and scan a picture and test api error."""
    aioclient_mock.post(OPENALPR_API_URL, params=PARAMS, exc=TimeoutError())

    with patch(
        "homeassistant.components.camera.async_get_image",
        return_value=camera.Image("image/jpeg", b"image"),
    ):
        common.async_scan(hass, entity_id="image_processing.test_local")
        await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_be(1)
    expect(len(events)).to_be(0)
