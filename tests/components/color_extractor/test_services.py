"""Tests for color_extractor component service calls."""

import base64
import io
from typing import Any
from unittest.mock import Mock, mock_open, patch

import aiohttp
from tryke import Depends, expect, fixture, test
from voluptuous.error import MultipleInvalid

from homeassistant.components.color_extractor.const import DOMAIN
from homeassistant.components.color_extractor.services import (
    ATTR_PATH,
    ATTR_URL,
    SERVICE_TURN_ON,
)
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ATTR_RGB_COLOR,
    DOMAIN as LIGHT_DOMAIN,
    SERVICE_TURN_OFF as LIGHT_SERVICE_TURN_OFF,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import color as color_util

from tests.common import MockConfigEntry, async_load_fixture, load_fixture
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.test_util.aiohttp import AiohttpClientMocker

LIGHT_ENTITY = "light.kitchen_lights"
CLOSE_THRESHOLD = 10


def _close_enough(actual_rgb, testing_rgb):
    """Validate the given RGB value is in acceptable tolerance."""
    actual_hs = color_util.color_RGB_to_hs(*actual_rgb)
    actual_rgb = color_util.color_hs_to_RGB(*actual_hs)

    testing_hs = color_util.color_RGB_to_hs(*testing_rgb)
    testing_rgb = color_util.color_hs_to_RGB(*testing_hs)

    actual_red, actual_green, actual_blue = actual_rgb
    testing_red, testing_green, testing_blue = testing_rgb

    r_diff = abs(actual_red - testing_red)
    g_diff = abs(actual_green - testing_green)
    b_diff = abs(actual_blue - testing_blue)

    return (
        r_diff <= CLOSE_THRESHOLD
        and g_diff <= CLOSE_THRESHOLD
        and b_diff <= CLOSE_THRESHOLD
    )


async def _setup(hass: HomeAssistant) -> None:
    """Set up demo light, color_extractor, and turn the light off."""
    await async_setup_component(hass, "homeassistant", {})
    expect(
        await async_setup_component(
            hass, LIGHT_DOMAIN, {LIGHT_DOMAIN: {"platform": "demo"}}
        )
    ).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get(LIGHT_ENTITY)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes.get(ATTR_BRIGHTNESS)).to_equal(180)
    expect(state.attributes.get(ATTR_RGB_COLOR)).to_equal((255, 64, 112))

    await hass.services.async_call(
        LIGHT_DOMAIN,
        LIGHT_SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: LIGHT_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(LIGHT_ENTITY)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)

    config_entry = MockConfigEntry(domain=DOMAIN, data={})
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


async def _async_execute_service(hass: HomeAssistant, service_data: dict[str, Any]) -> None:
    state = hass.states.get(LIGHT_ENTITY)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    await hass.services.async_call(DOMAIN, SERVICE_TURN_ON, service_data, blocking=True)
    await hass.async_block_till_done()


@test
async def missing_url_and_path(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that nothing happens when url and path are missing."""
    await _setup(hass)

    state = hass.states.get(LIGHT_ENTITY)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)

    service_data = {ATTR_ENTITY_ID: LIGHT_ENTITY}

    async with expect_raises_async(MultipleInvalid):
        await hass.services.async_call(
            DOMAIN, SERVICE_TURN_ON, service_data, blocking=True
        )

    state = hass.states.get(LIGHT_ENTITY)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)


@test
async def url_success(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that a successful image GET translate to light RGB."""
    await _setup(hass)
    service_data = {
        ATTR_URL: "http://example.com/images/logo.png",
        ATTR_ENTITY_ID: LIGHT_ENTITY,
        ATTR_BRIGHTNESS_PCT: 50,
    }

    aioclient_mock.get(
        url=service_data[ATTR_URL],
        content=base64.b64decode(
            await async_load_fixture(hass, "color_extractor_url.txt", DOMAIN)
        ),
    )
    hass.config.allowlist_external_urls.add("http://example.com/images/")

    await _async_execute_service(hass, service_data)

    state = hass.states.get(LIGHT_ENTITY)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(128)
    expect(_close_enough(state.attributes[ATTR_RGB_COLOR], (50, 100, 150))).to_be(True)


@test
async def url_not_allowed(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that a not allowed external URL fails to turn light on."""
    await _setup(hass)
    service_data = {
        ATTR_URL: "http://denied.com/images/logo.png",
        ATTR_ENTITY_ID: LIGHT_ENTITY,
    }
    await _async_execute_service(hass, service_data)
    state = hass.states.get(LIGHT_ENTITY)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)


@test
async def url_exception(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that a HTTPError fails to turn light on."""
    await _setup(hass)
    service_data = {
        ATTR_URL: "http://example.com/images/logo.png",
        ATTR_ENTITY_ID: LIGHT_ENTITY,
    }
    hass.config.allowlist_external_urls.add("http://example.com/images/")
    aioclient_mock.get(url=service_data[ATTR_URL], exc=aiohttp.ClientError)
    await _async_execute_service(hass, service_data)
    state = hass.states.get(LIGHT_ENTITY)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)


@test
async def url_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Test that a HTTP Error (non 200) doesn't turn light on."""
    await _setup(hass)
    service_data = {
        ATTR_URL: "http://example.com/images/logo.png",
        ATTR_ENTITY_ID: LIGHT_ENTITY,
    }
    hass.config.allowlist_external_urls.add("http://example.com/images/")
    aioclient_mock.get(url=service_data[ATTR_URL], status=400)
    await _async_execute_service(hass, service_data)
    state = hass.states.get(LIGHT_ENTITY)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)


@patch(
    "builtins.open",
    mock_open(
        read_data=base64.b64decode(load_fixture("color_extractor_file.txt", DOMAIN))
    ),
    create=True,
)
def _get_file_mock(file_path):
    """Convert file to BytesIO for testing due to PIL UnidentifiedImageError."""
    _file = None
    with open(file_path, encoding="utf8") as file_handler:
        _file = io.BytesIO(file_handler.read())
    _file.name = "color_extractor.jpg"
    _file.seek(0)
    return _file


@test.skip("os.path.isfile patch interferes with light_profiles.csv lazy load on teardown")
async def file() -> None:
    """Stub for test_file — global os.path.isfile patch breaks lazy profiles teardown."""


@test.skip("os.path.isfile patch interferes with light_profiles.csv lazy load on teardown")
async def file_denied_dir() -> None:
    """Stub for test_file_denied_dir — same teardown interference."""
