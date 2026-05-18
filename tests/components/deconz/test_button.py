"""deCONZ button platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.button import (
    DOMAIN as BUTTON_DOMAIN,
    SERVICE_PRESS,
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

STORE_SCENE_PAYLOAD = {
    "groups": {
        "1": {
            "id": "Light group id",
            "name": "Light group",
            "type": "LightGroup",
            "state": {"all_on": False, "any_on": True},
            "action": {},
            "scenes": [{"id": "1", "name": "Scene"}],
            "lights": [],
        }
    }
}

PRESENCE_RESET_PAYLOAD = {
    "sensors": {
        "1": {
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
    }
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture for tryke fixture-injection."""
    return 0


@test.cases(
    test.case(
        "store_scene",
        deconz_payload=STORE_SCENE_PAYLOAD,
        entity_id="button.light_group_scene_store_current_scene",
        request="/groups/1/scenes/1/store",
        request_data={},
    ),
    test.case(
        "presence_reset",
        deconz_payload=PRESENCE_RESET_PAYLOAD,
        entity_id="button.aqara_fp1_reset_presence",
        request="/sensors/1/config",
        request_data={"resetpresence": True},
    ),
)
async def button(
    deconz_payload: dict[str, Any],
    entity_id: str,
    request: str,
    request_data: dict[str, Any],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
) -> None:
    """Test successful creation of button entities and press behavior."""
    await setup_deconz(hass, aioclient, deconz_payload=deconz_payload)

    expect(hass.states.get(entity_id)).not_.to_be_none()

    aioclient_mock_put = put_request(request)

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal(request_data)
