"""The tests for the Alexa component."""

from http import HTTPStatus
import json

from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant.components import alexa
from homeassistant.components.alexa import intent
from homeassistant.const import CONTENT_TYPE_JSON
from homeassistant.core import HomeAssistant, callback
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    ClientSessionGenerator,
    hass as hass_fixture,
    hass_client as hass_client_fixture,
    mock_network,
)

SESSION_ID = "amzn1.echo-api.session.0000000-0000-0000-0000-00000000000"
APPLICATION_ID = "amzn1.echo-sdk-ams.app.000000-d0ed-0000-ad00-000000d00ebe"
APPLICATION_ID_SESSION_OPEN = (
    "amzn1.echo-sdk-ams.app.000000-d0ed-0000-ad00-000000d00ebf"
)
REQUEST_ID = "amzn1.echo-api.request.0000000-0000-0000-0000-00000000000"
AUTHORITY_ID = "amzn1.er-authority.000000-d0ed-0000-ad00-000000d00ebe.ZODIAC"
BUILTIN_AUTH_ID = "amzn1.er-authority.000000-d0ed-0000-ad00-000000d00ebe.TEST"

calls = []

NPR_NEWS_MP3_URL = "https://pd.npr.org/anon.npr-mp3/npr/news/newscast.mp3"


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
async def alexa_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client: ClientSessionGenerator = Depends(hass_client_fixture),
) -> TestClient:
    """Initialize a Home Assistant server for testing this module."""

    @callback
    def mock_service(call):
        calls.append(call)

    hass.services.async_register("test", "alexa", mock_service)

    assert await async_setup_component(
        hass,
        alexa.DOMAIN,
        {
            # Key is here to verify we allow other keys in config too
            "homeassistant": {},
            "alexa": {},
        },
    )
    assert await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "WhereAreWeIntent": {
                    "speech": {
                        "type": "plain",
                        "text": """
                        {%- if is_state("device_tracker.paulus", "home")
                                and is_state("device_tracker.anne_therese",
                                            "home") -%}
                            You are both home, you silly
                        {%- else -%}
                            Anne Therese is at {{
                                states("device_tracker.anne_therese")
                            }} and Paulus is at {{
                                states("device_tracker.paulus")
                            }}
                        {% endif %}
                    """,
                    }
                },
                "GetZodiacHoroscopeIntent": {
                    "speech": {
                        "type": "plain",
                        "text": "You told us your sign is {{ ZodiacSign }}.",
                    }
                },
                "GetZodiacHoroscopeIDIntent": {
                    "speech": {
                        "type": "plain",
                        "text": "You told us your sign is {{ ZodiacSign_Id }}.",
                    }
                },
                "AMAZON.PlaybackAction<object@MusicCreativeWork>": {
                    "speech": {
                        "type": "plain",
                        "text": "Playing {{ object_byArtist_name }}.",
                    }
                },
                "CallServiceIntent": {
                    "speech": {
                        "type": "plain",
                        "text": "Service called for {{ ZodiacSign }}",
                    },
                    "card": {
                        "type": "simple",
                        "title": "Card title for {{ ZodiacSign }}",
                        "content": "Card content: {{ ZodiacSign }}",
                    },
                    "action": {
                        "service": "test.alexa",
                        "data_template": {"hello": "{{ ZodiacSign }}"},
                        "entity_id": "switch.test",
                    },
                },
                APPLICATION_ID: {
                    "speech": {
                        "type": "plain",
                        "text": "LaunchRequest has been received.",
                    }
                },
                APPLICATION_ID_SESSION_OPEN: {
                    "speech": {
                        "type": "plain",
                        "text": "LaunchRequest has been received.",
                    },
                    "reprompt": {
                        "type": "plain",
                        "text": "LaunchRequest has been received.",
                    },
                },
            }
        },
    )
    return await hass_client()


def _intent_req(client, data=None):
    return client.post(
        intent.INTENTS_API_ENDPOINT,
        data=json.dumps(data or {}),
        headers={"content-type": CONTENT_TYPE_JSON},
    )


@test
async def intent_launch_request(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test the launch of a request."""
    data = {
        "version": "1.0",
        "session": {
            "new": True,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
            "attributes": {},
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "LaunchRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
        },
    }
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    text = data.get("response", {}).get("outputSpeech", {}).get("text")
    expect(text).to_equal("LaunchRequest has been received.")
    expect(data.get("response", {}).get("shouldEndSession")).to_be_truthy()


@test
async def intent_launch_request_with_session_open(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test the launch of a request."""
    data = {
        "version": "1.0",
        "session": {
            "new": True,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID_SESSION_OPEN},
            "attributes": {},
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "LaunchRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
        },
    }
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    text = data.get("response", {}).get("outputSpeech", {}).get("text")
    expect(text).to_equal("LaunchRequest has been received.")
    text = (
        data.get("response", {}).get("reprompt", {}).get("outputSpeech", {}).get("text")
    )
    expect(text).to_equal("LaunchRequest has been received.")
    expect(data.get("response", {}).get("shouldEndSession")).to_be_falsy()


@test
async def intent_launch_request_not_configured(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test the launch of a request."""
    data = {
        "version": "1.0",
        "session": {
            "new": True,
            "sessionId": SESSION_ID,
            "application": {
                "applicationId": (
                    "amzn1.echo-sdk-ams.app.000000-d0ed-0000-ad00-000000d00000"
                ),
            },
            "attributes": {},
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "LaunchRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
        },
    }
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    text = data.get("response", {}).get("outputSpeech", {}).get("text")
    expect(text).to_equal("This intent is not yet configured within Home Assistant.")


@test
async def intent_request_with_slots(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test a request with slots."""
    data = {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
            "attributes": {
                "supportedHoroscopePeriods": {
                    "daily": True,
                    "weekly": False,
                    "monthly": False,
                }
            },
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "IntentRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
            "intent": {
                "name": "GetZodiacHoroscopeIntent",
                "slots": {"ZodiacSign": {"name": "ZodiacSign", "value": "virgo"}},
            },
        },
    }
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    text = data.get("response", {}).get("outputSpeech", {}).get("text")
    expect(text).to_equal("You told us your sign is virgo.")


@test
async def intent_request_with_slots_and_synonym_resolution(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test a request with slots and a name synonym."""
    data = {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
            "attributes": {
                "supportedHoroscopePeriods": {
                    "daily": True,
                    "weekly": False,
                    "monthly": False,
                }
            },
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "IntentRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
            "intent": {
                "name": "GetZodiacHoroscopeIntent",
                "slots": {
                    "ZodiacSign": {
                        "name": "ZodiacSign",
                        "value": "V zodiac",
                        "resolutions": {
                            "resolutionsPerAuthority": [
                                {
                                    "authority": AUTHORITY_ID,
                                    "status": {"code": "ER_SUCCESS_MATCH"},
                                    "values": [{"value": {"name": "Virgo"}}],
                                },
                                {
                                    "authority": BUILTIN_AUTH_ID,
                                    "status": {"code": "ER_SUCCESS_NO_MATCH"},
                                    "values": [{"value": {"name": "Test"}}],
                                },
                            ]
                        },
                    }
                },
            },
        },
    }
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    text = data.get("response", {}).get("outputSpeech", {}).get("text")
    expect(text).to_equal("You told us your sign is Virgo.")


@test
async def intent_request_with_slots_and_synonym_id_resolution(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test a request with slots, id and a name synonym."""
    data = {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
            "attributes": {
                "supportedHoroscopePeriods": {
                    "daily": True,
                    "weekly": False,
                    "monthly": False,
                }
            },
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "IntentRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
            "intent": {
                "name": "GetZodiacHoroscopeIDIntent",
                "slots": {
                    "ZodiacSign": {
                        "name": "ZodiacSign",
                        "value": "V zodiac",
                        "resolutions": {
                            "resolutionsPerAuthority": [
                                {
                                    "authority": AUTHORITY_ID,
                                    "status": {"code": "ER_SUCCESS_MATCH"},
                                    "values": [{"value": {"name": "Virgo", "id": "1"}}],
                                }
                            ]
                        },
                    }
                },
            },
        },
    }
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    text = data.get("response", {}).get("outputSpeech", {}).get("text")
    expect(text).to_equal("You told us your sign is 1.")


@test
async def intent_request_with_slots_and_multi_synonym_id_resolution(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test a request with slots and multiple name synonyms (id)."""
    data = {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
            "attributes": {
                "supportedHoroscopePeriods": {
                    "daily": True,
                    "weekly": False,
                    "monthly": False,
                }
            },
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "IntentRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
            "intent": {
                "name": "GetZodiacHoroscopeIDIntent",
                "slots": {
                    "ZodiacSign": {
                        "name": "ZodiacSign",
                        "value": "Virgio Test",
                        "resolutions": {
                            "resolutionsPerAuthority": [
                                {
                                    "authority": AUTHORITY_ID,
                                    "status": {"code": "ER_SUCCESS_MATCH"},
                                    "values": [
                                        {"value": {"name": "Virgio Test", "id": "2"}}
                                    ],
                                },
                                {
                                    "authority": AUTHORITY_ID,
                                    "status": {"code": "ER_SUCCESS_MATCH"},
                                    "values": [{"value": {"name": "Virgo", "id": "1"}}],
                                },
                            ]
                        },
                    }
                },
            },
        },
    }
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    text = data.get("response", {}).get("outputSpeech", {}).get("text")
    expect(text).to_equal("You told us your sign is 2.")


@test
async def intent_request_with_slots_and_multi_synonym_resolution(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test a request with slots and multiple name synonyms."""
    data = {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
            "attributes": {
                "supportedHoroscopePeriods": {
                    "daily": True,
                    "weekly": False,
                    "monthly": False,
                }
            },
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "IntentRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
            "intent": {
                "name": "GetZodiacHoroscopeIntent",
                "slots": {
                    "ZodiacSign": {
                        "name": "ZodiacSign",
                        "value": "V zodiac",
                        "resolutions": {
                            "resolutionsPerAuthority": [
                                {
                                    "authority": AUTHORITY_ID,
                                    "status": {"code": "ER_SUCCESS_MATCH"},
                                    "values": [{"value": {"name": "Virgo"}}],
                                },
                                {
                                    "authority": BUILTIN_AUTH_ID,
                                    "status": {"code": "ER_SUCCESS_MATCH"},
                                    "values": [{"value": {"name": "Test"}}],
                                },
                            ]
                        },
                    }
                },
            },
        },
    }
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    text = data.get("response", {}).get("outputSpeech", {}).get("text")
    expect(text).to_equal("You told us your sign is V zodiac.")


@test
async def intent_request_with_slots_but_no_value(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test a request with slots but no value."""
    data = {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
            "attributes": {
                "supportedHoroscopePeriods": {
                    "daily": True,
                    "weekly": False,
                    "monthly": False,
                }
            },
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "IntentRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
            "intent": {
                "name": "GetZodiacHoroscopeIntent",
                "slots": {"ZodiacSign": {"name": "ZodiacSign"}},
            },
        },
    }
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    text = data.get("response", {}).get("outputSpeech", {}).get("text")
    expect(text).to_equal("You told us your sign is .")


@test
async def intent_request_without_slots(
    hass: HomeAssistant = Depends(hass_fixture),
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test a request without slots."""
    data = {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
            "attributes": {
                "supportedHoroscopePeriods": {
                    "daily": True,
                    "weekly": False,
                    "monthly": False,
                }
            },
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "IntentRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
            "intent": {"name": "WhereAreWeIntent"},
        },
    }
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    json_data = await req.json()
    text = json_data.get("response", {}).get("outputSpeech", {}).get("text")

    expect(text).to_equal("Anne Therese is at unknown and Paulus is at unknown")

    hass.states.async_set("device_tracker.paulus", "home")
    hass.states.async_set("device_tracker.anne_therese", "home")

    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    json_data = await req.json()
    text = json_data.get("response", {}).get("outputSpeech", {}).get("text")
    expect(text).to_equal("You are both home, you silly")


@test
async def intent_request_calling_service(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test a request for calling a service."""
    data = {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
            "attributes": {},
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "IntentRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
            "intent": {
                "name": "CallServiceIntent",
                "slots": {"ZodiacSign": {"name": "ZodiacSign", "value": "virgo"}},
            },
        },
    }
    call_count = len(calls)
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    expect(call_count + 1).to_equal(len(calls))
    call = calls[-1]
    expect(call.domain).to_equal("test")
    expect(call.service).to_equal("alexa")
    expect(call.data.get("entity_id")).to_equal(["switch.test"])
    expect(call.data.get("hello")).to_equal("virgo")

    data = await req.json()
    expect(data["response"]["card"]["title"]).to_equal("Card title for virgo")
    expect(data["response"]["card"]["content"]).to_equal("Card content: virgo")
    expect(data["response"]["outputSpeech"]["type"]).to_equal("PlainText")
    expect(data["response"]["outputSpeech"]["text"]).to_equal(
        "Service called for virgo"
    )


@test
async def intent_session_ended_request(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test the request for ending the session."""
    data = {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
            "attributes": {
                "supportedHoroscopePeriods": {
                    "daily": True,
                    "weekly": False,
                    "monthly": False,
                }
            },
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "SessionEndedRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
            "reason": "USER_INITIATED",
        },
    }

    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    expect(data["response"]["outputSpeech"]["text"]).to_equal(
        "This intent is not yet configured within Home Assistant."
    )


@test
async def intent_from_built_in_intent_library(
    alexa_client: TestClient = Depends(alexa_client),
) -> None:
    """Test intents from the Built-in Intent Library."""
    data = {
        "request": {
            "intent": {
                "name": "AMAZON.PlaybackAction<object@MusicCreativeWork>",
                "slots": {
                    "object.byArtist.name": {
                        "name": "object.byArtist.name",
                        "value": "the shins",
                    },
                    "object.composer.name": {"name": "object.composer.name"},
                    "object.contentSource": {"name": "object.contentSource"},
                    "object.era": {"name": "object.era"},
                    "object.genre": {"name": "object.genre"},
                    "object.name": {"name": "object.name"},
                    "object.owner.name": {"name": "object.owner.name"},
                    "object.select": {"name": "object.select"},
                    "object.sort": {"name": "object.sort"},
                    "object.type": {"name": "object.type", "value": "music"},
                },
            },
            "timestamp": "2016-12-14T23:23:37Z",
            "type": "IntentRequest",
            "requestId": REQUEST_ID,
        },
        "session": {
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
        },
    }
    req = await _intent_req(alexa_client, data)
    expect(req.status).to_equal(HTTPStatus.OK)
    data = await req.json()
    text = data.get("response", {}).get("outputSpeech", {}).get("text")
    expect(text).to_equal("Playing the shins.")
