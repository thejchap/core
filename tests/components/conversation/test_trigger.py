"""Test conversation triggers."""

import logging

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.components.conversation import HOME_ASSISTANT_AGENT, async_get_agent
from homeassistant.components.conversation.models import ConversationInput
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.helpers import trigger
from homeassistant.setup import async_setup_component

from ._fixtures import init_components, mock_shopping_list_io, service_calls

from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _shopping: None = Depends(mock_shopping_list_io),
    _init: None = Depends(init_components),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


@test
async def if_fires_on_event(
    hass: HomeAssistant = Depends(_trigger_executor),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the firing of events."""
    expect(
        await async_setup_component(
            hass,
            "automation",
            {
                "automation": {
                    "trigger": {
                        "platform": "conversation",
                        "command": [
                            "Hey yo",
                            "Ha ha ha",
                        ],
                    },
                    "action": {
                        "service": "test.automation",
                        "data": {
                            "data": {
                                "alias": "{{ trigger.alias }}",
                                "id": "{{ trigger.id }}",
                                "idx": "{{ trigger.idx }}",
                                "platform": "{{ trigger.platform }}",
                                "sentence": "{{ trigger.sentence }}",
                                "slots": "{{ trigger.slots }}",
                                "details": "{{ trigger.details }}",
                                "device_id": "{{ trigger.device_id }}",
                                "satellite_id": "{{ trigger.satellite_id }}",
                                "user_input": "{{ trigger.user_input }}",
                            }
                        },
                    },
                }
            },
        )
    ).to_be_truthy()
    context = Context()
    service_response = await hass.services.async_call(
        "conversation",
        "process",
        {"text": "Ha ha ha"},
        blocking=True,
        return_response=True,
        context=context,
    )
    expect(service_response["response"]["speech"]["plain"]["speech"]).to_equal("Done")

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].domain).to_equal("test")
    expect(service_calls[1].service).to_equal("automation")
    expect(service_calls[1].data["data"]).to_equal(
        {
            "alias": None,
            "id": 0,
            "idx": 0,
            "platform": "conversation",
            "sentence": "Ha ha ha",
            "slots": {},
            "details": {},
            "device_id": None,
            "satellite_id": None,
            "user_input": {
                "agent_id": HOME_ASSISTANT_AGENT,
                "context": context.as_dict(),
                "conversation_id": None,
                "device_id": None,
                "satellite_id": None,
                "language": "en",
                "text": "Ha ha ha",
                "extra_system_prompt": None,
            },
        }
    )


@test
async def response(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the conversation response action."""
    response = "I'm sorry, Dave. I'm afraid I can't do that"
    expect(
        await async_setup_component(
            hass,
            "automation",
            {
                "automation": {
                    "trigger": {
                        "platform": "conversation",
                        "command": ["Open the pod bay door Hal"],
                        "variables": {"name": "Dr. David Bowman"},
                    },
                    "action": {
                        "set_conversation_response": response,
                    },
                }
            },
        )
    ).to_be_truthy()

    service_response = await hass.services.async_call(
        "conversation",
        "process",
        {
            "text": "Open the pod bay door Hal",
        },
        blocking=True,
        return_response=True,
    )
    expect(service_response["response"]["speech"]["plain"]["speech"]).to_equal(
        response
    )


@test
async def empty_response(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the conversation response action with an empty response."""
    expect(
        await async_setup_component(
            hass,
            "automation",
            {
                "automation": {
                    "trigger": {
                        "platform": "conversation",
                        "command": ["Open the pod bay door Hal"],
                    },
                    "action": {
                        "set_conversation_response": "",
                    },
                }
            },
        )
    ).to_be_truthy()

    service_response = await hass.services.async_call(
        "conversation",
        "process",
        {
            "text": "Open the pod bay door Hal",
        },
        blocking=True,
        return_response=True,
    )
    expect(service_response["response"]["speech"]["plain"]["speech"]).to_equal("")


@test
async def response_same_sentence(
    hass: HomeAssistant = Depends(_trigger_executor),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test the conversation response action with multiple triggers using the same sentence."""
    expect(
        await async_setup_component(
            hass,
            "automation",
            {
                "automation": [
                    {
                        "trigger": {
                            "id": "trigger1",
                            "platform": "conversation",
                            "command": ["test sentence"],
                        },
                        "action": [
                            # Add delay so this response will not be the first
                            {"delay": "0:0:0.100"},
                            {
                                "service": "test.automation",
                                "data_template": {
                                    "data": {
                                        "alias": "{{ trigger.alias }}",
                                        "id": "{{ trigger.id }}",
                                        "idx": "{{ trigger.idx }}",
                                        "platform": "{{ trigger.platform }}",
                                        "sentence": "{{ trigger.sentence }}",
                                        "slots": "{{ trigger.slots }}",
                                        "details": "{{ trigger.details }}",
                                        "device_id": "{{ trigger.device_id }}",
                                        "satellite_id": "{{ trigger.satellite_id }}",
                                        "user_input": "{{ trigger.user_input }}",
                                    }
                                },
                            },
                            {"set_conversation_response": "response 2"},
                        ],
                    },
                    {
                        "trigger": {
                            "id": "trigger2",
                            "platform": "conversation",
                            "command": ["test sentence"],
                        },
                        "action": {"set_conversation_response": "response 1"},
                    },
                ]
            },
        )
    ).to_be_truthy()
    context = Context()
    service_response = await hass.services.async_call(
        "conversation",
        "process",
        {"text": "test sentence"},
        blocking=True,
        return_response=True,
        context=context,
    )
    await hass.async_block_till_done()

    # Should only get first response
    expect(service_response["response"]["speech"]["plain"]["speech"]).to_equal(
        "response 1"
    )

    # Service should still have been called
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].domain).to_equal("test")
    expect(service_calls[1].service).to_equal("automation")
    expect(service_calls[1].data["data"]).to_equal(
        {
            "alias": None,
            "id": "trigger1",
            "idx": 0,
            "platform": "conversation",
            "sentence": "test sentence",
            "slots": {},
            "details": {},
            "device_id": None,
            "satellite_id": None,
            "user_input": {
                "agent_id": HOME_ASSISTANT_AGENT,
                "context": context.as_dict(),
                "conversation_id": None,
                "device_id": None,
                "satellite_id": None,
                "language": "en",
                "text": "test sentence",
                "extra_system_prompt": None,
            },
        }
    )


@test
async def response_same_sentence_with_error(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test the conversation response action with multiple triggers using the same sentence and an error."""
    caplog.set_level(logging.ERROR)
    expect(
        await async_setup_component(
            hass,
            "automation",
            {
                "automation": [
                    {
                        "trigger": {
                            "id": "trigger1",
                            "platform": "conversation",
                            "command": ["test sentence"],
                        },
                        "action": [
                            # Add delay so this will not finish first
                            {"delay": "0:0:0.100"},
                            {"service": "fake_domain.fake_service"},
                        ],
                    },
                    {
                        "trigger": {
                            "id": "trigger2",
                            "platform": "conversation",
                            "command": ["test sentence"],
                        },
                        "action": {"set_conversation_response": "response 1"},
                    },
                ]
            },
        )
    ).to_be_truthy()
    context = Context()
    service_response = await hass.services.async_call(
        "conversation",
        "process",
        {"text": "test sentence"},
        blocking=True,
        return_response=True,
        context=context,
    )
    await hass.async_block_till_done()

    # Should still get first response
    expect(service_response["response"]["speech"]["plain"]["speech"]).to_equal(
        "response 1"
    )

    # Error should have been logged
    expect("Error executing script" in caplog.text).to_be(True)


@test
async def subscribe_trigger_does_not_interfere_with_responses(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client=Depends(hass_ws_client_fixture),
) -> None:
    """Test that subscribing to a trigger from the websocket API does not interfere with responses."""
    websocket_client = await hass_ws_client()
    await websocket_client.send_json_auto_id(
        {
            "type": "subscribe_trigger",
            "trigger": {"platform": "conversation", "command": ["test sentence"]},
        }
    )
    await websocket_client.receive_json()

    service_response = await hass.services.async_call(
        "conversation",
        "process",
        {
            "text": "test sentence",
        },
        blocking=True,
        return_response=True,
    )

    # Default response, since no automations with responses are registered
    expect(service_response["response"]["speech"]["plain"]["speech"]).to_equal("Done")

    # Now register a trigger with a response
    expect(
        await async_setup_component(
            hass,
            "automation",
            {
                "automation test1": {
                    "trigger": {
                        "platform": "conversation",
                        "command": ["test sentence"],
                    },
                    "action": {
                        "set_conversation_response": "test response",
                    },
                }
            },
        )
    ).to_be_truthy()

    service_response = await hass.services.async_call(
        "conversation",
        "process",
        {
            "text": "test sentence",
        },
        blocking=True,
        return_response=True,
    )

    # Response will now come through
    expect(service_response["response"]["speech"]["plain"]["speech"]).to_equal(
        "test response"
    )


@test
async def same_trigger_multiple_sentences(
    hass: HomeAssistant = Depends(_trigger_executor),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test matching of multiple sentences from the same trigger."""
    expect(
        await async_setup_component(
            hass,
            "automation",
            {
                "automation": {
                    "trigger": {
                        "platform": "conversation",
                        "command": ["hello", "hello[ world]"],
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "data": {
                                "alias": "{{ trigger.alias }}",
                                "id": "{{ trigger.id }}",
                                "idx": "{{ trigger.idx }}",
                                "platform": "{{ trigger.platform }}",
                                "sentence": "{{ trigger.sentence }}",
                                "slots": "{{ trigger.slots }}",
                                "details": "{{ trigger.details }}",
                                "device_id": "{{ trigger.device_id }}",
                                "satellite_id": "{{ trigger.satellite_id }}",
                                "user_input": "{{ trigger.user_input }}",
                            }
                        },
                    },
                }
            },
        )
    ).to_be_truthy()
    context = Context()
    await hass.services.async_call(
        "conversation",
        "process",
        {
            "text": "hello",
        },
        blocking=True,
        context=context,
    )

    # Only triggers once
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].domain).to_equal("test")
    expect(service_calls[1].service).to_equal("automation")
    expect(service_calls[1].data["data"]).to_equal(
        {
            "alias": None,
            "id": 0,
            "idx": 0,
            "platform": "conversation",
            "sentence": "hello",
            "slots": {},
            "details": {},
            "device_id": None,
            "satellite_id": None,
            "user_input": {
                "agent_id": HOME_ASSISTANT_AGENT,
                "context": context.as_dict(),
                "conversation_id": None,
                "device_id": None,
                "satellite_id": None,
                "language": "en",
                "text": "hello",
                "extra_system_prompt": None,
            },
        }
    )


@test
async def same_sentence_multiple_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test use of the same sentence in multiple triggers."""
    expect(
        await async_setup_component(
            hass,
            "automation",
            {
                "automation": [
                    {
                        "trigger": {
                            "id": "trigger1",
                            "platform": "conversation",
                            "command": [
                                "hello",
                            ],
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "data": {
                                    "alias": "{{ trigger.alias }}",
                                    "id": "{{ trigger.id }}",
                                    "idx": "{{ trigger.idx }}",
                                    "platform": "{{ trigger.platform }}",
                                    "sentence": "{{ trigger.sentence }}",
                                    "slots": "{{ trigger.slots }}",
                                    "details": "{{ trigger.details }}",
                                    "device_id": "{{ trigger.device_id }}",
                                    "satellite_id": "{{ trigger.satellite_id }}",
                                    "user_input": "{{ trigger.user_input }}",
                                }
                            },
                        },
                    },
                    {
                        "trigger": {
                            "id": "trigger2",
                            "platform": "conversation",
                            "command": [
                                "hello[ world]",
                            ],
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "data": {
                                    "alias": "{{ trigger.alias }}",
                                    "id": "{{ trigger.id }}",
                                    "idx": "{{ trigger.idx }}",
                                    "platform": "{{ trigger.platform }}",
                                    "sentence": "{{ trigger.sentence }}",
                                    "slots": "{{ trigger.slots }}",
                                    "details": "{{ trigger.details }}",
                                    "device_id": "{{ trigger.device_id }}",
                                    "satellite_id": "{{ trigger.satellite_id }}",
                                    "user_input": "{{ trigger.user_input }}",
                                }
                            },
                        },
                    },
                ],
            },
        )
    ).to_be_truthy()

    await hass.services.async_call(
        "conversation",
        "process",
        {
            "text": "hello",
        },
        blocking=True,
    )

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)

    # The calls may come in any order
    call_datas: set[tuple[str, str, str]] = set()
    service_calls.pop(0)  # First call is the call to conversation.process
    for call in service_calls:
        call_data = call.data["data"]
        call_datas.add((call_data["id"], call_data["platform"], call_data["sentence"]))

    expect(call_datas).to_equal(
        {
            ("trigger1", "conversation", "hello"),
            ("trigger2", "conversation", "hello"),
        }
    )


@test.cases(
    test.case("question_mark", command="hello?"),
    test.case("exclamation", command="hello!"),
    test.case("period", command="4 a.m."),
)
async def fails_on_punctuation(
    command: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that validation fails when sentences contain punctuation."""
    async with expect_raises_async(vol.Invalid):
        await trigger.async_validate_trigger_config(
            hass,
            [
                {
                    "id": "trigger1",
                    "platform": "conversation",
                    "command": [
                        command,
                    ],
                },
            ],
        )


@test.cases(
    test.case("empty_string", command=""),
)
async def fails_on_empty(
    command: str,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that validation fails when sentences are empty."""
    async with expect_raises_async(vol.Invalid):
        await trigger.async_validate_trigger_config(
            hass,
            [
                {
                    "id": "trigger1",
                    "platform": "conversation",
                    "command": [
                        command,
                    ],
                },
            ],
        )


@test
async def fails_on_no_sentences(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that validation fails when no sentences are provided."""
    async with expect_raises_async(vol.Invalid):
        await trigger.async_validate_trigger_config(
            hass,
            [
                {
                    "id": "trigger1",
                    "platform": "conversation",
                    "command": [],
                },
            ],
        )


@test
async def wildcards(
    hass: HomeAssistant = Depends(_trigger_executor),
    service_calls: list[ServiceCall] = Depends(service_calls),
) -> None:
    """Test wildcards in trigger sentences."""
    expect(
        await async_setup_component(
            hass,
            "automation",
            {
                "automation": {
                    "trigger": {
                        "platform": "conversation",
                        "command": [
                            "play {album} by {artist}",
                        ],
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "data": {
                                "alias": "{{ trigger.alias }}",
                                "id": "{{ trigger.id }}",
                                "idx": "{{ trigger.idx }}",
                                "platform": "{{ trigger.platform }}",
                                "sentence": "{{ trigger.sentence }}",
                                "slots": "{{ trigger.slots }}",
                                "details": "{{ trigger.details }}",
                                "device_id": "{{ trigger.device_id }}",
                                "satellite_id": "{{ trigger.satellite_id }}",
                                "user_input": "{{ trigger.user_input }}",
                            }
                        },
                    },
                }
            },
        )
    ).to_be_truthy()

    context = Context()
    await hass.services.async_call(
        "conversation",
        "process",
        {
            "text": "play the white album by the beatles",
        },
        blocking=True,
        context=context,
    )

    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].domain).to_equal("test")
    expect(service_calls[1].service).to_equal("automation")
    expect(service_calls[1].data["data"]).to_equal(
        {
            "alias": None,
            "id": 0,
            "idx": 0,
            "platform": "conversation",
            "sentence": "play the white album by the beatles",
            "slots": {
                "album": "the white album",
                "artist": "the beatles",
            },
            "details": {
                "album": {
                    "name": "album",
                    "text": "the white album",
                    "value": "the white album",
                },
                "artist": {
                    "name": "artist",
                    "text": "the beatles",
                    "value": "the beatles",
                },
            },
            "device_id": None,
            "satellite_id": None,
            "user_input": {
                "agent_id": HOME_ASSISTANT_AGENT,
                "context": context.as_dict(),
                "conversation_id": None,
                "device_id": None,
                "satellite_id": None,
                "language": "en",
                "text": "play the white album by the beatles",
                "extra_system_prompt": None,
            },
        }
    )


@test
async def trigger_with_device_id(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that a trigger receives a device_id."""
    expect(
        await async_setup_component(
            hass,
            "automation",
            {
                "automation": {
                    "trigger": {
                        "platform": "conversation",
                        "command": ["test sentence"],
                    },
                    "action": {
                        "set_conversation_response": "{{ trigger.device_id }} - {{ trigger.satellite_id }}",
                    },
                }
            },
        )
    ).to_be_truthy()

    agent = async_get_agent(hass)

    result = await agent.async_process(
        ConversationInput(
            text="test sentence",
            context=Context(),
            conversation_id=None,
            device_id="my_device",
            satellite_id="assist_satellite.my_satellite",
            language=hass.config.language,
            agent_id=None,
        )
    )
    expect(result.response.speech["plain"]["speech"]).to_equal(
        "my_device - assist_satellite.my_satellite"
    )
