"""Tests for the sigfox sensor."""

from http import HTTPStatus
import re

import requests_mock
from tryke import Depends, expect, fixture, test

from homeassistant.components.sigfox.sensor import (
    API_URL,
    CONF_API_LOGIN,
    CONF_API_PASSWORD,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass

TEST_API_LOGIN = "foo"
TEST_API_PASSWORD = "ebcd1234"

VALID_CONFIG = {
    "sensor": {
        "platform": "sigfox",
        CONF_API_LOGIN: TEST_API_LOGIN,
        CONF_API_PASSWORD: TEST_API_PASSWORD,
    }
}

VALID_MESSAGE = """
{"data":[{
"time":1521879720,
"data":"7061796c6f6164",
"rinfos":[{"lat":"0.0","lng":"0.0"}],
"snr":"50.0"}]}
"""


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def invalid_credentials(hass: HomeAssistant = Depends(hass)) -> None:
    """Test for invalid credentials."""
    with requests_mock.Mocker() as mock_req:
        url = re.compile(API_URL + "devicetypes")
        mock_req.get(url, text="{}", status_code=HTTPStatus.UNAUTHORIZED)
        result = await async_setup_component(hass, "sensor", VALID_CONFIG)
        expect(result).to_be(True)
        await hass.async_block_till_done()
    expect(len(hass.states.async_entity_ids())).to_equal(0)


@test
async def valid_credentials(hass: HomeAssistant = Depends(hass)) -> None:
    """Test for valid credentials."""
    with requests_mock.Mocker() as mock_req:
        url1 = re.compile(API_URL + "devicetypes")
        mock_req.get(
            url1, text='{"data":[{"id":"fake_type"}]}', status_code=HTTPStatus.OK
        )

        url2 = re.compile(API_URL + "devicetypes/fake_type/devices")
        mock_req.get(url2, text='{"data":[{"id":"fake_id"}]}')

        url3 = re.compile(API_URL + "devices/fake_id/messages*")
        mock_req.get(url3, text=VALID_MESSAGE)

        result = await async_setup_component(hass, "sensor", VALID_CONFIG)
        expect(result).to_be(True)
        await hass.async_block_till_done()

        expect(len(hass.states.async_entity_ids())).to_equal(1)
        state = hass.states.get("sensor.sigfox_fake_id")
        expect(state is not None).to_be(True)
        expect(state.state).to_equal("payload")
        expect(state.attributes.get("snr")).to_equal("50.0")
