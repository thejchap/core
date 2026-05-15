"""Tests for conversation utility functions."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import conversation
from homeassistant.core import HomeAssistant
from homeassistant.helpers import chat_session, intent, llm

from ._fixtures import mock_conversation_input, mock_shopping_list_io

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _shopping: None = Depends(mock_shopping_list_io),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


@test
async def async_get_result_from_chat_log(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: conversation.ConversationInput = Depends(
        mock_conversation_input
    ),
) -> None:
    """Test getting result from chat log."""
    intent_response = intent.IntentResponse(language="en")
    tool_result = llm.IntentResponseDict(intent_response)
    with (
        chat_session.async_get_chat_session(hass) as session,
        conversation.async_get_chat_log(
            hass, session, mock_conversation_input
        ) as chat_log,
    ):
        chat_log.content.extend(
            [
                conversation.ToolResultContent(
                    agent_id="mock-agent-id",
                    tool_call_id="mock-tool-call-id",
                    tool_name="mock-tool-name",
                    tool_result=tool_result,
                ),
                conversation.AssistantContent(
                    agent_id="mock-agent-id",
                    content="This is a response.",
                ),
            ]
        )
        result = conversation.async_get_result_from_chat_log(
            mock_conversation_input, chat_log
        )
    expect(result.response is intent_response).to_be(True)
    expect(result.response.speech["plain"]["speech"]).to_equal("This is a response.")
    expect(tool_result["speech"] != result.response.speech).to_be(True)
