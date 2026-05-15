"""Test agent manager."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.conversation import ConversationResult, async_converse
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers.intent import IntentResponse

from ._fixtures import init_components, mock_shopping_list_io

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _shopping: None = Depends(mock_shopping_list_io),
    _init: None = Depends(init_components),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


@test
async def async_converse_test(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the async_converse method."""
    context = Context()
    with patch(
        "homeassistant.components.conversation.default_agent.DefaultAgent.async_process",
        return_value=ConversationResult(response=IntentResponse(language="test lang")),
    ) as mock_process:
        await async_converse(
            hass,
            text="test command",
            conversation_id="test id",
            context=context,
            language="test lang",
            agent_id="conversation.home_assistant",
            device_id="test device id",
            extra_system_prompt="test extra prompt",
        )

    expect(mock_process.called).to_be(True)
    conversation_input = mock_process.call_args[0][0]
    expect(conversation_input.text).to_equal("test command")
    expect(conversation_input.conversation_id).to_equal("test id")
    expect(conversation_input.context is context).to_be(True)
    expect(conversation_input.language).to_equal("test lang")
    expect(conversation_input.agent_id).to_equal("conversation.home_assistant")
    expect(conversation_input.device_id).to_equal("test device id")
    expect(conversation_input.extra_system_prompt).to_equal("test extra prompt")
