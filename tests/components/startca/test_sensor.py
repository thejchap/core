"""Tests for the Start.ca sensor platform."""

from http import HTTPStatus

from tryke import Depends, expect, fixture, test

from homeassistant.components.startca.sensor import StartcaData
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, PERCENTAGE, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    aioclient_mock,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def capped_setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test the default setup."""
    config = {
        "platform": "startca",
        "api_key": "NOTAKEY",
        "total_bandwidth": 400,
        "monitored_variables": [
            "usage",
            "usage_gb",
            "limit",
            "used_download",
            "used_upload",
            "used_total",
            "grace_download",
            "grace_upload",
            "grace_total",
            "total_download",
            "total_upload",
            "used_remaining",
        ],
    }

    result = (
        '<?xml version="1.0" encoding="ISO-8859-15"?>'
        "<usage>"
        "<version>1.1</version>"
        "<total> <!-- total actual usage -->"
        "<download>304946829777</download>"
        "<upload>6480700153</upload>"
        "</total>"
        "<used> <!-- part of usage that counts against quota -->"
        "<download>304946829777</download>"
        "<upload>6480700153</upload>"
        "</used>"
        "<grace> <!-- part of usage that is free -->"
        "<download>304946829777</download>"
        "<upload>6480700153</upload>"
        "</grace>"
        "</usage>"
    )
    aioclient_mock.get(
        "https://www.start.ca/support/usage/api?key=NOTAKEY", text=result
    )

    await async_setup_component(hass, "sensor", {"sensor": config})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.start_ca_usage_ratio")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(PERCENTAGE)
    expect(state.state).to_equal("76.24")

    state = hass.states.get("sensor.start_ca_usage")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("304.95")

    state = hass.states.get("sensor.start_ca_data_limit")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("400")

    state = hass.states.get("sensor.start_ca_used_download")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("304.95")

    state = hass.states.get("sensor.start_ca_used_upload")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("6.48")

    state = hass.states.get("sensor.start_ca_used_total")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("311.43")

    state = hass.states.get("sensor.start_ca_grace_download")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("304.95")

    state = hass.states.get("sensor.start_ca_grace_upload")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("6.48")

    state = hass.states.get("sensor.start_ca_grace_total")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("311.43")

    state = hass.states.get("sensor.start_ca_total_download")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("304.95")

    state = hass.states.get("sensor.start_ca_total_upload")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("6.48")

    state = hass.states.get("sensor.start_ca_remaining")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("95.05")


@test
async def unlimited_setup(
    hass: HomeAssistant = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test the default setup."""
    config = {
        "platform": "startca",
        "api_key": "NOTAKEY",
        "total_bandwidth": 0,
        "monitored_variables": [
            "usage",
            "usage_gb",
            "limit",
            "used_download",
            "used_upload",
            "used_total",
            "grace_download",
            "grace_upload",
            "grace_total",
            "total_download",
            "total_upload",
            "used_remaining",
        ],
    }

    result = (
        '<?xml version="1.0" encoding="ISO-8859-15"?>'
        "<usage>"
        "<version>1.1</version>"
        "<total> <!-- total actual usage -->"
        "<download>304946829777</download>"
        "<upload>6480700153</upload>"
        "</total>"
        "<used> <!-- part of usage that counts against quota -->"
        "<download>0</download>"
        "<upload>0</upload>"
        "</used>"
        "<grace> <!-- part of usage that is free -->"
        "<download>304946829777</download>"
        "<upload>6480700153</upload>"
        "</grace>"
        "</usage>"
    )
    aioclient_mock.get(
        "https://www.start.ca/support/usage/api?key=NOTAKEY", text=result
    )

    await async_setup_component(hass, "sensor", {"sensor": config})
    await hass.async_block_till_done()

    # These sensors should not be created for unlimited setups
    expect(hass.states.get("sensor.start_ca_usage_ratio") is None).to_be(True)
    expect(hass.states.get("sensor.start_ca_data_limit") is None).to_be(True)
    expect(hass.states.get("sensor.start_ca_remaining") is None).to_be(True)

    state = hass.states.get("sensor.start_ca_usage")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("0.0")

    state = hass.states.get("sensor.start_ca_used_download")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("0.0")

    state = hass.states.get("sensor.start_ca_used_upload")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("0.0")

    state = hass.states.get("sensor.start_ca_used_total")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("0.0")

    state = hass.states.get("sensor.start_ca_grace_download")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("304.95")

    state = hass.states.get("sensor.start_ca_grace_upload")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("6.48")

    state = hass.states.get("sensor.start_ca_grace_total")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("311.43")

    state = hass.states.get("sensor.start_ca_total_download")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("304.95")

    state = hass.states.get("sensor.start_ca_total_upload")
    expect(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)).to_equal(
        UnitOfInformation.GIGABYTES
    )
    expect(state.state).to_equal("6.48")


@test
async def bad_return_code(
    hass: HomeAssistant = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test handling a return code that isn't HTTP OK."""
    aioclient_mock.get(
        "https://www.start.ca/support/usage/api?key=NOTAKEY",
        status=HTTPStatus.NOT_FOUND,
    )

    scd = StartcaData(async_get_clientsession(hass), "NOTAKEY", 400)

    result = await scd.async_update()
    expect(result).to_be(False)


@test
async def bad_json_decode(
    hass: HomeAssistant = Depends(_trigger_executor),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test decoding invalid json result."""
    aioclient_mock.get(
        "https://www.start.ca/support/usage/api?key=NOTAKEY", text="this is not xml"
    )

    scd = StartcaData(async_get_clientsession(hass), "NOTAKEY", 400)

    result = await scd.async_update()
    expect(result).to_be(False)
