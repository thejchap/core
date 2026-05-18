"""deCONZ select platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydeconz.models.sensor.air_purifier import AirPurifierFanMode
from pydeconz.models.sensor.presence import (
    PresenceConfigDeviceMode,
    PresenceConfigTriggerDistance,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.select import (
    ATTR_OPTION,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from tests.components.deconz._fixtures import (
    mock_put_request,
    setup_deconz,
)
from tests.hass_fixtures import (
    aioclient_mock,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

PRESENCE_SENSOR_PAYLOAD = {
    "config": {
        "devicemode": "undirected",
        "on": True,
        "reachable": True,
        "sensitivity": 3,
        "triggerdistance": "medium",
    },
    "etag": "13ff209f9401b317987d42506dd4cd79",
    "lastannounced": None,
    "lastseen": "2022-06-28T23:13Z",
    "manufacturername": "aqara",
    "modelid": "lumi.motion.ac01",
    "name": "Aqara FP1",
    "state": {
        "lastupdated": "2022-06-28T23:13:38.577",
        "presence": True,
        "presenceevent": "leave",
    },
    "swversion": "20210121",
    "type": "ZHAPresence",
    "uniqueid": "xx:xx:xx:xx:xx:xx:xx:xx-01-0406",
}

AIR_PURIFIER_SENSOR_PAYLOAD = {
    "config": {
        "filterlifetime": 259200,
        "ledindication": True,
        "locked": False,
        "mode": "speed_1",
        "on": True,
        "reachable": True,
    },
    "ep": 1,
    "etag": "de26d19d9e91b2db3ded6ee7ab6b6a4b",
    "lastannounced": None,
    "lastseen": "2024-08-07T18:27Z",
    "manufacturername": "IKEA of Sweden",
    "modelid": "STARKVIND Air purifier",
    "name": "IKEA Starkvind",
    "productid": "E2007",
    "state": {
        "deviceruntime": 73405,
        "filterruntime": 73405,
        "lastupdated": "2024-08-07T18:27:52.543",
        "replacefilter": False,
        "speed": 20,
    },
    "swversion": "1.1.001",
    "type": "ZHAAirPurifier",
    "uniqueid": "0c:43:14:ff:fe:6c:20:12-01-fc7d",
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture for tryke fixture-injection."""
    return 0


@test.cases(
    test.case(
        "presence_device_mode",
        sensor_payload=PRESENCE_SENSOR_PAYLOAD,
        entity_id="select.aqara_fp1_device_mode",
        option=PresenceConfigDeviceMode.LEFT_AND_RIGHT.value,
        request="/sensors/0/config",
        request_data={"devicemode": "leftright"},
    ),
    test.case(
        "presence_sensitivity",
        sensor_payload=PRESENCE_SENSOR_PAYLOAD,
        entity_id="select.aqara_fp1_sensitivity",
        option="Medium",
        request="/sensors/0/config",
        request_data={"sensitivity": 2},
    ),
    test.case(
        "presence_trigger_distance",
        sensor_payload=PRESENCE_SENSOR_PAYLOAD,
        entity_id="select.aqara_fp1_trigger_distance",
        option=PresenceConfigTriggerDistance.FAR.value,
        request="/sensors/0/config",
        request_data={"triggerdistance": "far"},
    ),
    test.case(
        "air_purifier_fan_mode",
        sensor_payload=AIR_PURIFIER_SENSOR_PAYLOAD,
        entity_id="select.ikea_starkvind_fan_mode",
        option=AirPurifierFanMode.AUTO.value,
        request="/sensors/0/config",
        request_data={"mode": "auto"},
    ),
)
async def select(
    sensor_payload: dict[str, Any],
    entity_id: str,
    option: str,
    request: str,
    request_data: dict[str, Any],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
) -> None:
    """Test successful creation of select entities and option selection."""
    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)

    expect(hass.states.get(entity_id)).not_.to_be_none()

    aioclient_mock_put = put_request(request)

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_OPTION: option,
        },
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal(request_data)
