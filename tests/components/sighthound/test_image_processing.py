"""Tests for the Sighthound integration."""

from copy import deepcopy
import os
from pathlib import Path
from unittest import mock

import simplehound.core as hound
from tryke import Depends, expect, fixture, test

from homeassistant.components.image_processing import DOMAIN as IP_DOMAIN, SERVICE_SCAN
from homeassistant.components.sighthound import image_processing as sh
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_API_KEY,
    CONF_ENTITY_ID,
    CONF_SOURCE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.setup import async_setup_component

from tests.components.sighthound._fixtures import (
    mock_bad_image_data,
    mock_detections,
    mock_image,
    mock_now,
    setup_homeassistant,
)
from tests.hass_fixtures import LogCapture, caplog, hass as hass_fixture, mock_network

TEST_DIR = os.path.dirname(__file__)

VALID_CONFIG = {
    IP_DOMAIN: {
        "platform": "sighthound",
        CONF_API_KEY: "abc123",
        CONF_SOURCE: {CONF_ENTITY_ID: "camera.demo_camera"},
    },
    "camera": {"platform": "demo"},
}

VALID_ENTITY_ID = "image_processing.sighthound_demo_camera"


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(setup_homeassistant),
) -> HomeAssistant:
    return hass


@test
async def bad_api_key(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Catch bad api key."""
    with mock.patch(
        "simplehound.core.cloud.detect", side_effect=hound.SimplehoundException
    ):
        await async_setup_component(hass, IP_DOMAIN, VALID_CONFIG)
        await hass.async_block_till_done()
        expect("Sighthound error" in caplog.text).to_be(True)
        expect(hass.states.get(VALID_ENTITY_ID) is None).to_be(True)


@test
async def setup_platform(
    hass: HomeAssistant = Depends(_trigger_executor),
    _detections: mock.MagicMock = Depends(mock_detections),
) -> None:
    """Set up platform with one entity."""
    await async_setup_component(hass, IP_DOMAIN, VALID_CONFIG)
    await hass.async_block_till_done()
    expect(hass.states.get(VALID_ENTITY_ID) is not None).to_be(True)


@test
async def process_image(
    hass: HomeAssistant = Depends(_trigger_executor),
    _image: mock.MagicMock = Depends(mock_image),
    _detections: mock.MagicMock = Depends(mock_detections),
) -> None:
    """Process an image."""
    await async_setup_component(hass, IP_DOMAIN, VALID_CONFIG)
    await hass.async_block_till_done()
    expect(hass.states.get(VALID_ENTITY_ID) is not None).to_be(True)

    person_events = []

    @callback
    def capture_person_event(event):
        """Mock event."""
        person_events.append(event)

    hass.bus.async_listen(sh.EVENT_PERSON_DETECTED, capture_person_event)

    data = {ATTR_ENTITY_ID: VALID_ENTITY_ID}
    await hass.services.async_call(IP_DOMAIN, SERVICE_SCAN, service_data=data)
    await hass.async_block_till_done()

    state = hass.states.get(VALID_ENTITY_ID)
    expect(state.state).to_equal("2")
    expect(len(person_events)).to_equal(2)


@test
async def catch_bad_image(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog),
    _image: mock.MagicMock = Depends(mock_image),
    _detections: mock.MagicMock = Depends(mock_detections),
    _bad_image: mock.MagicMock = Depends(mock_bad_image_data),
) -> None:
    """Process an image."""
    valid_config_save_file = deepcopy(VALID_CONFIG)
    valid_config_save_file[IP_DOMAIN].update({sh.CONF_SAVE_FILE_FOLDER: TEST_DIR})
    await async_setup_component(hass, IP_DOMAIN, valid_config_save_file)
    await hass.async_block_till_done()
    expect(hass.states.get(VALID_ENTITY_ID) is not None).to_be(True)

    data = {ATTR_ENTITY_ID: VALID_ENTITY_ID}
    await hass.services.async_call(IP_DOMAIN, SERVICE_SCAN, service_data=data)
    await hass.async_block_till_done()
    expect("Sighthound unable to process image" in caplog.text).to_be(True)


@test
async def save_image(
    hass: HomeAssistant = Depends(_trigger_executor),
    _image: mock.MagicMock = Depends(mock_image),
    _detections: mock.MagicMock = Depends(mock_detections),
) -> None:
    """Save a processed image."""
    valid_config_save_file = deepcopy(VALID_CONFIG)
    valid_config_save_file[IP_DOMAIN].update({sh.CONF_SAVE_FILE_FOLDER: TEST_DIR})
    await async_setup_component(hass, IP_DOMAIN, valid_config_save_file)
    await hass.async_block_till_done()
    expect(hass.states.get(VALID_ENTITY_ID) is not None).to_be(True)

    with mock.patch(
        "homeassistant.components.sighthound.image_processing.Image.open"
    ) as pil_img_open:
        pil_img = pil_img_open.return_value
        pil_img = pil_img.convert.return_value
        data = {ATTR_ENTITY_ID: VALID_ENTITY_ID}
        await hass.services.async_call(IP_DOMAIN, SERVICE_SCAN, service_data=data)
        await hass.async_block_till_done()
        state = hass.states.get(VALID_ENTITY_ID)
        expect(state.state).to_equal("2")
        expect(pil_img.save.call_count).to_equal(1)

        directory = Path(TEST_DIR)
        latest_save_path = directory / "sighthound_demo_camera_latest.jpg"
        expect(pil_img.save.call_args_list[0]).to_equal(mock.call(latest_save_path))


@test
async def save_timestamped_image(
    hass: HomeAssistant = Depends(_trigger_executor),
    _image: mock.MagicMock = Depends(mock_image),
    _detections: mock.MagicMock = Depends(mock_detections),
    _now: mock.MagicMock = Depends(mock_now),
) -> None:
    """Save a processed image."""
    valid_config_save_ts_file = deepcopy(VALID_CONFIG)
    valid_config_save_ts_file[IP_DOMAIN].update({sh.CONF_SAVE_FILE_FOLDER: TEST_DIR})
    valid_config_save_ts_file[IP_DOMAIN].update({sh.CONF_SAVE_TIMESTAMPTED_FILE: True})
    await async_setup_component(hass, IP_DOMAIN, valid_config_save_ts_file)
    await hass.async_block_till_done()
    expect(hass.states.get(VALID_ENTITY_ID) is not None).to_be(True)

    with mock.patch(
        "homeassistant.components.sighthound.image_processing.Image.open"
    ) as pil_img_open:
        pil_img = pil_img_open.return_value
        pil_img = pil_img.convert.return_value
        data = {ATTR_ENTITY_ID: VALID_ENTITY_ID}
        await hass.services.async_call(IP_DOMAIN, SERVICE_SCAN, service_data=data)
        await hass.async_block_till_done()
        state = hass.states.get(VALID_ENTITY_ID)
        expect(state.state).to_equal("2")
        expect(pil_img.save.call_count).to_equal(2)

        directory = Path(TEST_DIR)
        timestamp_save_path = (
            directory / "sighthound_demo_camera_2020-02-20_10:05:03.jpg"
        )
        expect(pil_img.save.call_args_list[1]).to_equal(mock.call(timestamp_save_path))
