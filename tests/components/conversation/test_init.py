"""The tests for the Conversation component (tryke port)."""

from unittest.mock import patch

from tryke import Depends, fixture, test
import voluptuous as vol

from homeassistant.components import conversation
from homeassistant.components.conversation import (
    ConversationInput,
    async_get_agent,
    async_get_chat_log,
    async_handle_intents,
    default_agent,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import chat_session, intent
from homeassistant.setup import async_setup_component

from ._fixtures import init_components, mock_shopping_list_io

from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(
    _shopping: None = Depends(mock_shopping_list_io),
) -> int:
    """Force tryke fixture resolution before each test."""
    return 0


async def _expect_raises(exc_type, coro) -> None:
    """Run *coro* and assert it raises *exc_type*."""
    try:
        await coro
    except exc_type:
        return
    raise AssertionError(f"Expected {exc_type.__name__}")


@test
async def service_fails(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_components),
) -> None:
    """Test calling the turn on intent service that fails."""
    with patch(
        "homeassistant.components.conversation.async_converse",
        side_effect=intent.IntentHandleError,
    ):
        await _expect_raises(
            HomeAssistantError,
            hass.services.async_call(
                "conversation",
                "process",
                {"text": "bla"},
                blocking=True,
            ),
        )


@test
async def reload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_components),
) -> None:
    """Test calling the reload service."""
    language = hass.config.language
    agent = async_get_agent(hass)

    # Load intents
    await agent.async_prepare(language)

    # Confirm intents are loaded
    assert agent._lang_intents.get(language)
    # Confirm config intents are empty
    assert not agent._config_intents_config["intents"]

    # Try to clear for a different language
    await hass.services.async_call(
        "conversation", "reload", {"language": "elvish"}, blocking=True
    )

    # Confirm intents are still loaded
    assert agent._lang_intents.get(language)
    assert not agent._config_intents_config["intents"]

    # Reload from a changed configuration file
    hass_config_new = {
        "conversation": {
            "intents": {
                "TestIntent": [
                    "Test intent phrase",
                    "Another test intent phrase",
                ]
            }
        }
    }
    with patch(
        "homeassistant.config.load_yaml_config_file", return_value=hass_config_new
    ):
        await hass.services.async_call("conversation", "reload", {}, blocking=True)

    # Confirm intent cache is cleared
    assert not agent._lang_intents.get(language)
    # Confirm new config intents are loaded
    assert agent._config_intents_config["intents"]


@test
async def prepare_fail(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_components),
) -> None:
    """Test calling prepare with a non-existent language."""
    agent = async_get_agent(hass)

    await agent.async_prepare("not-a-language")

    # Confirm no intents were loaded
    assert agent._lang_intents.get("not-a-language") is default_agent.ERROR_SENTINEL


@test
async def agent_id_validator_invalid_agent(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: None = Depends(init_components),
) -> None:
    """Test validating agent id."""
    try:
        conversation.agent_id_validator("invalid_agent")
    except vol.Invalid:
        pass
    else:
        raise AssertionError("Expected vol.Invalid")

    conversation.agent_id_validator(conversation.HOME_ASSISTANT_AGENT)
    conversation.agent_id_validator("conversation.home_assistant")


@test
async def handle_intents(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test handling registered intents with async_handle_intents."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})

    class OrderBeerIntentHandler(intent.IntentHandler):
        intent_type = "OrderBeer"

        def __init__(self) -> None:
            super().__init__()
            self.was_handled = False

        async def async_handle(
            self, intent_obj: intent.Intent
        ) -> intent.IntentResponse:
            self.was_handled = True
            return intent_obj.create_response()

    handler = OrderBeerIntentHandler()
    intent.async_register(hass, handler)

    user_input = ConversationInput(
        text="I'd like to order a stout",
        context=Context(),
        agent_id=conversation.HOME_ASSISTANT_AGENT,
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
    )
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, user_input) as chat_log,
    ):
        result = await async_handle_intents(hass, user_input, chat_log)
    assert result is not None
    assert result.intent is not None
    assert result.intent.intent_type == handler.intent_type
    assert handler.was_handled

    # No matching sentence — None as a result
    user_input2 = ConversationInput(
        text="this sentence does not exist",
        agent_id=conversation.HOME_ASSISTANT_AGENT,
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
    )
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, user_input2) as chat_log,
    ):
        result = await async_handle_intents(hass, user_input2, chat_log)
    assert result is None


# Snapshot- and parametrize-based tests are deferred until matching tryke
# helpers land.
@test.skip("snapshot + parametrize: requires SnapshotAssertion and parametrize")
async def turn_on_intent() -> None:
    """Skipped: requires snapshot + parametrize."""


@test.skip("snapshot + parametrize: requires parametrize over sentences")
async def turn_off_intent() -> None:
    """Skipped: requires parametrize."""


@test.skip("snapshot: requires SnapshotAssertion + hass_client fixture wiring")
async def custom_agent() -> None:
    """Skipped: requires snapshot + hass_client."""


@test.skip("snapshot: requires SnapshotAssertion + mock_conversation_agent fixture")
async def get_agent_info() -> None:
    """Skipped: requires snapshot."""


@test.skip("requires parametrize over agent_id options")
async def prepare_agent() -> None:
    """Skipped: requires parametrize."""


@test.skip("requires parametrize over response_template values")
async def handle_sentence_triggers() -> None:
    """Skipped: requires parametrize."""
