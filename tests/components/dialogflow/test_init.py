"""The tests for the Dialogflow component."""

import copy
from http import HTTPStatus
import json

from tryke import Depends, expect, fixture, test

from homeassistant.components import dialogflow
from homeassistant.core import HomeAssistant, ServiceCall

from ._fixtures import calls as calls_fixture, dialogflow_fixture

from tests.hass_fixtures import hass as hass_fixture

SESSION_ID = "a9b84cec-46b6-484e-8f31-f65dba03ae6d"
INTENT_ID = "c6a74079-a8f0-46cd-b372-5a934d23591c"
INTENT_NAME = "tests"
REQUEST_ID = "19ef7e78-fe15-4e94-99dd-0c0b1e8753c3"
REQUEST_TIMESTAMP = "2017-01-21T17:54:18.952Z"
CONTEXT_NAME = "78a5db95-b7d6-4d50-9c9b-2fc73a5e34c3_id_dialog_context"


class _Data:
    _v1 = {
        "id": REQUEST_ID,
        "timestamp": REQUEST_TIMESTAMP,
        "result": {
            "source": "agent",
            "resolvedQuery": "my zodiac sign is virgo",
            "action": "GetZodiacHoroscopeIntent",
            "actionIncomplete": False,
            "parameters": {"ZodiacSign": "virgo"},
            "metadata": {
                "intentId": INTENT_ID,
                "webhookUsed": "true",
                "webhookForSlotFillingUsed": "false",
                "intentName": INTENT_NAME,
            },
            "fulfillment": {"speech": "", "messages": [{"type": 0, "speech": ""}]},
            "score": 1,
        },
        "status": {"code": 200, "errorType": "success"},
        "sessionId": SESSION_ID,
        "originalRequest": None,
    }

    _v2 = {
        "responseId": REQUEST_ID,
        "timestamp": REQUEST_TIMESTAMP,
        "queryResult": {
            "queryText": "my zodiac sign is virgo",
            "action": "GetZodiacHoroscopeIntent",
            "allRequiredParamsPresent": True,
            "parameters": {"ZodiacSign": "virgo"},
            "intent": {
                "name": INTENT_ID,
                "webhookState": "true",
                "displayName": INTENT_NAME,
            },
            "fulfillment": {"text": "", "messages": [{"type": 0, "speech": ""}]},
            "intentDetectionConfidence": 1,
        },
        "status": {"code": 200, "errorType": "success"},
        "session": SESSION_ID,
        "originalDetectIntentRequest": None,
    }

    @property
    def v1(self):
        return copy.deepcopy(self._v1)

    @property
    def v2(self):
        return copy.deepcopy(self._v2)


Data = _Data()


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def v1_data(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test for version 1 api based on message."""
    expect(dialogflow.get_api_version(Data.v1)).to_equal(1)


@test
async def v2_data(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test for version 2 api based on message."""
    expect(dialogflow.get_api_version(Data.v2)).to_equal(2)


@test
async def intent_action_incomplete_v1(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test when action is not completed."""
    mock_client, webhook_id = fixture
    data = Data.v1
    data["result"]["actionIncomplete"] = True

    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.text()).to_equal("")


@test
async def intent_action_incomplete_v2(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test when action is not completed."""
    mock_client, webhook_id = fixture
    data = Data.v2
    data["queryResult"]["allRequiredParamsPresent"] = False

    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.text()).to_equal("")


@test
async def intent_slot_filling_v1(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test when Dialogflow asks for slot-filling return none."""
    mock_client, webhook_id = fixture

    data = Data.v1
    data["result"].update(
        resolvedQuery="my zodiac sign is",
        speech="",
        actionIncomplete=True,
        parameters={"ZodiacSign": ""},
        contexts=[
            {
                "name": CONTEXT_NAME,
                "parameters": {"ZodiacSign.original": "", "ZodiacSign": ""},
                "lifespan": 2,
            },
            {
                "name": "tests_ha_dialog_context",
                "parameters": {"ZodiacSign.original": "", "ZodiacSign": ""},
                "lifespan": 2,
            },
            {
                "name": "tests_ha_dialog_params_zodiacsign",
                "parameters": {"ZodiacSign.original": "", "ZodiacSign": ""},
                "lifespan": 1,
            },
        ],
        fulfillment={
            "speech": "What is the ZodiacSign?",
            "messages": [{"type": 0, "speech": "What is the ZodiacSign?"}],
        },
        score=0.77,
    )
    data["result"]["metadata"].update(webhookForSlotFillingUsed="true")

    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(await response.text()).to_equal("")


@test
async def intent_request_with_parameters_v1(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test a request with parameters."""
    mock_client, webhook_id = fixture
    data = Data.v1
    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("speech")
    expect(text).to_equal("You told us your sign is virgo.")


@test
async def intent_request_with_parameters_v2(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test a request with parameters."""
    mock_client, webhook_id = fixture
    data = Data.v2
    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("fulfillmentText")
    expect(text).to_equal("You told us your sign is virgo.")


@test
async def intent_request_with_parameters_but_empty_v1(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test a request with parameters but empty value."""
    mock_client, webhook_id = fixture
    data = Data.v1
    data["result"].update(parameters={"ZodiacSign": ""})
    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("speech")
    expect(text).to_equal("You told us your sign is .")


@test
async def intent_request_with_parameters_but_empty_v2(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test a request with parameters but empty value."""
    mock_client, webhook_id = fixture
    data = Data.v2
    data["queryResult"].update(parameters={"ZodiacSign": ""})
    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("fulfillmentText")
    expect(text).to_equal("You told us your sign is .")


@test
async def intent_request_without_slots_v1(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test a request without slots."""
    mock_client, webhook_id = fixture
    data = Data.v1
    data["result"].update(
        resolvedQuery="where are we",
        action="WhereAreWeIntent",
        parameters={},
        contexts=[],
    )

    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("speech")

    expect(text).to_equal("Anne Therese is at unknown and Paulus is at unknown")

    hass.states.async_set("device_tracker.paulus", "home")
    hass.states.async_set("device_tracker.anne_therese", "home")

    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("speech")
    expect(text).to_equal("You are both home, you silly")


@test
async def intent_request_without_slots_v2(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test a request without slots."""
    mock_client, webhook_id = fixture
    data = Data.v2
    data["queryResult"].update(
        queryText="where are we",
        action="WhereAreWeIntent",
        parameters={},
        outputContexts=[],
    )

    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("fulfillmentText")

    expect(text).to_equal("Anne Therese is at unknown and Paulus is at unknown")

    hass.states.async_set("device_tracker.paulus", "home")
    hass.states.async_set("device_tracker.anne_therese", "home")

    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("fulfillmentText")
    expect(text).to_equal("You are both home, you silly")


@test
async def intent_request_calling_service_v1(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
    calls: list[ServiceCall] = Depends(calls_fixture),
) -> None:
    """Test a request for calling a service."""
    mock_client, webhook_id = fixture
    data = Data.v1
    data["result"]["action"] = "CallServiceIntent"
    call_count = len(calls)
    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(len(calls)).to_equal(call_count + 1)
    call = calls[-1]
    expect(call.domain).to_equal("test")
    expect(call.service).to_equal("dialogflow")
    expect(call.data.get("entity_id")).to_equal(["switch.test"])
    expect(call.data.get("hello")).to_equal("virgo")


@test
async def intent_request_calling_service_v2(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
    calls: list[ServiceCall] = Depends(calls_fixture),
) -> None:
    """Test a request for calling a service."""
    mock_client, webhook_id = fixture
    data = Data.v2
    data["queryResult"]["action"] = "CallServiceIntent"
    call_count = len(calls)
    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    expect(len(calls)).to_equal(call_count + 1)
    call = calls[-1]
    expect(call.domain).to_equal("test")
    expect(call.service).to_equal("dialogflow")
    expect(call.data.get("entity_id")).to_equal(["switch.test"])
    expect(call.data.get("hello")).to_equal("virgo")


@test
async def intent_with_no_action_v1(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test an intent with no defined action."""
    mock_client, webhook_id = fixture
    data = Data.v1
    del data["result"]["action"]
    expect("action" in data["result"]).to_be(False)
    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("speech")
    expect(text).to_equal("You have not defined an action in your Dialogflow intent.")


@test
async def intent_with_no_action_v2(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test an intent with no defined action."""
    mock_client, webhook_id = fixture
    data = Data.v2
    del data["queryResult"]["action"]
    expect("action" in data["queryResult"]).to_be(False)
    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("fulfillmentText")
    expect(text).to_equal("You have not defined an action in your Dialogflow intent.")


@test
async def intent_with_unknown_action_v1(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test an intent with an action not defined in the conf."""
    mock_client, webhook_id = fixture
    data = Data.v1
    data["result"]["action"] = "unknown"
    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("speech")
    expect(text).to_equal("This intent is not yet configured within Home Assistant.")


@test
async def intent_with_unknown_action_v2(
    hass: HomeAssistant = Depends(_trigger_executor),
    fixture: tuple[object, str] = Depends(dialogflow_fixture),
) -> None:
    """Test an intent with an action not defined in the conf."""
    mock_client, webhook_id = fixture
    data = Data.v2
    data["queryResult"]["action"] = "unknown"
    response = await mock_client.post(
        f"/api/webhook/{webhook_id}", data=json.dumps(data)
    )
    expect(response.status).to_equal(HTTPStatus.OK)
    text = (await response.json()).get("fulfillmentText")
    expect(text).to_equal("This intent is not yet configured within Home Assistant.")
