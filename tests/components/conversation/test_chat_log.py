"""Test the conversation session (tryke port)."""

from datetime import timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from freezegun import freeze_time
import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.components.conversation import (
    AssistantContent,
    ConversationInput,
    ToolResultContent,
    UserContent,
    async_get_chat_log,
)
from homeassistant.components.conversation.chat_log import (
    DATA_CHAT_LOGS,
    Attachment,
    ChatLogEventType,
    async_subscribe_chat_logs,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import chat_session, llm
from homeassistant.util import dt as dt_util

from ._fixtures import mock_conversation_input, mock_shopping_list_io

from tests.common import async_fire_time_changed
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import expect_raises_async


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _shopping: None = Depends(mock_shopping_list_io),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


@test
async def cleanup(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test cleanup of the chat log."""
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        conversation_id = session.conversation_id
        # Add message so it persists
        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="mock-agent-id",
                content="Hey!",
            )
        )

    expect(conversation_id in hass.data[DATA_CHAT_LOGS]).to_be(True)

    # Set the last updated to be older than the timeout
    hass.data[chat_session.DATA_CHAT_SESSION][conversation_id].last_updated = (
        dt_util.utcnow() + chat_session.CONVERSATION_TIMEOUT
    )

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + chat_session.CONVERSATION_TIMEOUT * 2 + timedelta(seconds=1),
    )

    expect(conversation_id not in hass.data[DATA_CHAT_LOGS]).to_be(True)


@test
async def default_content(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test filtering of messages."""
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log2,
    ):
        expect(chat_log is chat_log2).to_be(True)
        expect(len(chat_log.content)).to_equal(2)
        expect(chat_log.content[0].role).to_equal("system")
        expect(chat_log.content[0].content).to_equal("")
        expect(chat_log.content[1].role).to_equal("user")
        expect(chat_log.content[1].content).to_equal(mock_conversation_input.text)


@test
async def llm_api(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test when we reference an LLM API."""
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api="assist",
            user_llm_prompt=None,
        )

    expect(isinstance(chat_log.llm_api, llm.APIInstance)).to_be(True)
    expect(chat_log.llm_api.api.id).to_equal("assist")


@test.skip("snapshot test - tryke snapshot shim cannot resolve test frame")
async def unknown_llm_api() -> None:
    """Stub for test_unknown_llm_api (port deferred).

    Asserts against a snapshot. The tryke snapshot fixture's frame-walk
    lands on `<frozen runpy>` instead of the test function, so the
    snapshot lookup fails. Kept as a skip stub.
    """


@test
async def multiple_llm_apis(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test when we reference an LLM API."""

    class MyTool(llm.Tool):
        """Test tool."""

        name = "test_tool"
        description = "Test function"
        parameters = vol.Schema(
            {vol.Optional("param1", description="Test parameters"): str}
        )

    class MyAPI(llm.API):
        """Test API."""

        async def async_get_api_instance(
            self, llm_context: llm.LLMContext
        ) -> llm.APIInstance:
            """Return a list of tools."""
            return llm.APIInstance(self, "My API Prompt", llm_context, [MyTool()])

    api = MyAPI(hass=hass, id="my-api", name="Test")
    llm.async_register_api(hass, api)

    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=["assist", "my-api"],
            user_llm_prompt=None,
        )

    expect(chat_log.llm_api is not None).to_be(True)
    expect(chat_log.llm_api.api.id).to_equal("assist|my-api")


@test
async def dynamic_time_injection(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test that dynamic time injection works correctly."""

    class MyAPI(llm.API):
        """Test API."""

        async def async_get_api_instance(
            self, llm_context: llm.LLMContext
        ) -> llm.APIInstance:
            """Return a list of tools."""
            return llm.APIInstance(self, "My API Prompt", llm_context, [])

    not_assist_1_api = MyAPI(hass=hass, id="not-assist-1", name="Not Assist 1")
    llm.async_register_api(hass, not_assist_1_api)

    not_assist_2_api = MyAPI(hass=hass, id="not-assist-2", name="Not Assist 2")
    llm.async_register_api(hass, not_assist_2_api)

    # Helper to track which prompts are rendered
    rendered_prompts = []

    async def fake_expand_prompt_template(
        llm_context, prompt, language, user_name=None
    ):
        rendered_prompts.append(prompt)
        return prompt

    # Case 1: No API used -> prompt should contain the time
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        chat_log._async_expand_prompt_template = fake_expand_prompt_template
        rendered_prompts.clear()
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=None,
            user_llm_prompt=None,
        )
        expect(llm.DATE_TIME_PROMPT in rendered_prompts).to_be(True)

    # Case 2: Single API (not assist) -> prompt should contain the time
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        chat_log._async_expand_prompt_template = fake_expand_prompt_template
        rendered_prompts.clear()
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=["not-assist-1"],
            user_llm_prompt=None,
        )
        expect(llm.DATE_TIME_PROMPT in rendered_prompts).to_be(True)

    # Case 3: Single API (assist) -> prompt should NOT contain the time
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        chat_log._async_expand_prompt_template = fake_expand_prompt_template
        rendered_prompts.clear()
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=[llm.LLM_API_ASSIST],
            user_llm_prompt=None,
        )
        expect(llm.DATE_TIME_PROMPT not in rendered_prompts).to_be(True)

    # Case 4: Merged API (without assist) -> prompt should contain the time
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        chat_log._async_expand_prompt_template = fake_expand_prompt_template
        rendered_prompts.clear()
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=["not-assist-1", "not-assist-2"],
            user_llm_prompt=None,
        )
        expect(llm.DATE_TIME_PROMPT in rendered_prompts).to_be(True)

    # Case 5: Merged API (with assist) -> prompt should NOT contain the time
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        chat_log._async_expand_prompt_template = fake_expand_prompt_template
        rendered_prompts.clear()
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=[llm.LLM_API_ASSIST, "not-assist-1"],
            user_llm_prompt=None,
        )
        expect(llm.DATE_TIME_PROMPT not in rendered_prompts).to_be(True)


@test.skip("snapshot test - tryke snapshot shim cannot resolve test frame")
async def template_error() -> None:
    """Stub for test_template_error (port deferred).

    Asserts against a snapshot. The tryke snapshot fixture's frame-walk
    lands on `<frozen runpy>` instead of the test function, so the
    snapshot lookup fails. Kept as a skip stub.
    """


@test
async def template_variables(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test that template variables work."""
    mock_user = Mock()
    mock_user.id = "12345"
    mock_user.name = "Test User"
    mock_conversation_input.context = Context(user_id=mock_user.id)

    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
        patch("homeassistant.auth.AuthManager.async_get_user", return_value=mock_user),
    ):
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=None,
            user_llm_prompt=(
                "The instance name is {{ ha_name }}. "
                "The user name is {{ user_name }}. "
                "The user id is {{ llm_context.context.user_id }}."
                "The calling platform is {{ llm_context.platform }}."
            ),
        )

    expect("The instance name is test home." in chat_log.content[0].content).to_be(True)
    expect("The user name is Test User." in chat_log.content[0].content).to_be(True)
    expect("The user id is 12345." in chat_log.content[0].content).to_be(True)
    expect("The calling platform is test." in chat_log.content[0].content).to_be(True)


@test
async def extra_systen_prompt(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test that extra system prompt works."""
    extra_system_prompt = "Garage door cover.garage_door has been left open for 30 minutes. We asked the user if they want to close it."
    extra_system_prompt2 = (
        "User person.paulus came home. Asked him what he wants to do."
    )
    mock_conversation_input.extra_system_prompt = extra_system_prompt

    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=None,
            user_llm_prompt=None,
            user_extra_system_prompt=mock_conversation_input.extra_system_prompt,
        )
        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="mock-agent-id",
                content="Hey!",
            )
        )

    expect(chat_log.extra_system_prompt).to_equal(extra_system_prompt)
    expect(chat_log.content[0].content.endswith(extra_system_prompt)).to_be(True)

    # Verify that follow-up conversations with no system prompt take previous one
    conversation_id = chat_log.conversation_id
    mock_conversation_input.extra_system_prompt = None

    with (
        chat_session.async_get_chat_session(hass, conversation_id) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=None,
            user_llm_prompt=None,
            user_extra_system_prompt=mock_conversation_input.extra_system_prompt,
        )

    expect(chat_log.extra_system_prompt).to_equal(extra_system_prompt)
    expect(chat_log.content[0].content.endswith(extra_system_prompt)).to_be(True)

    # Verify that we take new system prompts
    mock_conversation_input.extra_system_prompt = extra_system_prompt2

    with (
        chat_session.async_get_chat_session(hass, conversation_id) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=None,
            user_llm_prompt=None,
            user_extra_system_prompt=mock_conversation_input.extra_system_prompt,
        )
        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="mock-agent-id",
                content="Hey!",
            )
        )

    expect(chat_log.extra_system_prompt).to_equal(extra_system_prompt2)
    expect(chat_log.content[0].content.endswith(extra_system_prompt2)).to_be(True)
    expect(extra_system_prompt not in chat_log.content[0].content).to_be(True)

    # Verify that follow-up conversations with no system prompt take previous one
    mock_conversation_input.extra_system_prompt = None

    with (
        chat_session.async_get_chat_session(hass, conversation_id) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=None,
            user_llm_prompt=None,
            user_extra_system_prompt=mock_conversation_input.extra_system_prompt,
        )

    expect(chat_log.extra_system_prompt).to_equal(extra_system_prompt2)
    expect(chat_log.content[0].content.endswith(extra_system_prompt2)).to_be(True)


@test.cases(
    test.case("no_prerun", prerun_tool_tasks=()),
    test.case("one_prerun", prerun_tool_tasks=("mock-tool-call-id",)),
    test.case(
        "two_prerun",
        prerun_tool_tasks=("mock-tool-call-id", "mock-tool-call-id-2"),
    ),
)
async def tool_call(
    prerun_tool_tasks: tuple[str, ...],
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test using the session tool calling API."""
    with freeze_time("2025-10-31 18:00:00"):
        mock_tool = AsyncMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test function"
        mock_tool.parameters = vol.Schema(
            {vol.Optional("param1", description="Test parameters"): str}
        )
        mock_tool.async_call.return_value = "Test response"

        with patch(
            "homeassistant.helpers.llm.AssistAPI._async_get_tools", return_value=[]
        ) as mock_get_tools:
            mock_get_tools.return_value = [mock_tool]

            with (
                chat_session.async_get_chat_session(hass) as session,
                async_get_chat_log(
                    hass, session, mock_conversation_input
                ) as chat_log,
            ):
                await chat_log.async_provide_llm_data(
                    mock_conversation_input.as_llm_context("test"),
                    user_llm_hass_api="assist",
                    user_llm_prompt=None,
                )
                content = AssistantContent(
                    agent_id=mock_conversation_input.agent_id,
                    content="",
                    tool_calls=[
                        llm.ToolInput(
                            id="mock-tool-call-id",
                            tool_name="test_tool",
                            tool_args={"param1": "Test Param"},
                        ),
                        llm.ToolInput(
                            id="mock-tool-call-id-2",
                            tool_name="test_tool",
                            tool_args={"param1": "Test Param"},
                        ),
                    ],
                )

                tool_call_tasks = {
                    tool_call_id: hass.async_create_task(
                        chat_log.llm_api.async_call_tool(content.tool_calls[0]),
                        tool_call_id,
                    )
                    for tool_call_id in prerun_tool_tasks
                }

                async with expect_raises_async(ValueError):
                    chat_log.async_add_assistant_content_without_tools(content)

                results = [
                    tool_result_content
                    async for tool_result_content in chat_log.async_add_assistant_content(
                        content, tool_call_tasks=tool_call_tasks or None
                    )
                ]

                expect(
                    results[0]
                    == ToolResultContent(
                        agent_id=mock_conversation_input.agent_id,
                        tool_call_id="mock-tool-call-id",
                        tool_result="Test response",
                        tool_name="test_tool",
                    )
                ).to_be(True)
                expect(
                    results[1]
                    == ToolResultContent(
                        agent_id=mock_conversation_input.agent_id,
                        tool_call_id="mock-tool-call-id-2",
                        tool_result="Test response",
                        tool_name="test_tool",
                    )
                ).to_be(True)


@test
async def tool_call_exception(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test using the session tool calling API."""
    with freeze_time("2025-10-31 12:00:00"):
        mock_tool = AsyncMock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test function"
        mock_tool.parameters = vol.Schema(
            {vol.Optional("param1", description="Test parameters"): str}
        )
        mock_tool.async_call.side_effect = HomeAssistantError("Test error")

        with (
            patch(
                "homeassistant.helpers.llm.AssistAPI._async_get_tools",
                return_value=[],
            ) as mock_get_tools,
            chat_session.async_get_chat_session(hass) as session,
            async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
        ):
            mock_get_tools.return_value = [mock_tool]
            await chat_log.async_provide_llm_data(
                mock_conversation_input.as_llm_context("test"),
                user_llm_hass_api="assist",
                user_llm_prompt=None,
            )
            result = None
            async for tool_result_content in chat_log.async_add_assistant_content(
                AssistantContent(
                    agent_id=mock_conversation_input.agent_id,
                    content="",
                    tool_calls=[
                        llm.ToolInput(
                            id="mock-tool-call-id",
                            tool_name="test_tool",
                            tool_args={"param1": "Test Param"},
                        )
                    ],
                )
            ):
                expect(result is None).to_be(True)
                result = tool_result_content

        # Build expected value inside the frozen-time block so the
        # `created` timestamp matches the result built above.
        expected = ToolResultContent(
            agent_id=mock_conversation_input.agent_id,
            tool_call_id="mock-tool-call-id",
            tool_result={"error": "HomeAssistantError", "error_text": "Test error"},
            tool_name="test_tool",
        )

    expect(result == expected).to_be(True)


@test.skip("parametrized snapshot test - tryke cannot reconstruct [deltasN] index")
async def add_delta_content_stream() -> None:
    """Stub for test_add_delta_content_stream (port deferred).

    The original test is parametrized over 12 `deltas` cases and asserts
    against snapshots keyed `test_add_delta_content_stream[deltasN]`. The
    tryke snapshot shim cannot reproduce the `[deltasN]` index, so snapshot
    lookups would fail. Kept as a skip stub.
    """


@test
async def add_delta_content_stream_errors(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test streaming deltas error handling."""

    async def stream(deltas):
        """Yield deltas."""
        for d in deltas:
            yield d

    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        # Stream content without LLM API set
        async with expect_raises_async(ValueError):
            async for _tool_result_content in chat_log.async_add_delta_content_stream(
                "mock-agent-id",
                stream(
                    [
                        {"role": "assistant"},
                        {
                            "tool_calls": [
                                llm.ToolInput(
                                    id="mock-tool-call-id",
                                    tool_name="test_tool",
                                    tool_args={},
                                )
                            ]
                        },
                    ]
                ),
            ):
                pass

        # Non assistant role
        for role in ("system", "user"):
            async with expect_raises_async(ValueError):
                async for (
                    _tool_result_content
                ) in chat_log.async_add_delta_content_stream(
                    "mock-agent-id",
                    stream([{"role": role}]),
                ):
                    pass

        # Second native content
        async with expect_raises_async(RuntimeError):
            async for _tool_result_content in chat_log.async_add_delta_content_stream(
                "mock-agent-id",
                stream(
                    [
                        {"role": "assistant"},
                        {"native": "Test Native"},
                        {"native": "Test Native 2"},
                    ]
                ),
            ):
                pass


@test
async def chat_log_reuse(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test that we can reuse a chat log."""
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session) as chat_log,
    ):
        expect(chat_log.conversation_id).to_equal(session.conversation_id)
        expect(len(chat_log.content)).to_equal(1)

        with async_get_chat_log(hass, session) as chat_log2:
            expect(chat_log2 is chat_log).to_be(True)
            expect(len(chat_log.content)).to_equal(1)

        with async_get_chat_log(hass, session, mock_conversation_input) as chat_log2:
            expect(chat_log2 is chat_log).to_be(True)
            expect(len(chat_log.content)).to_equal(2)
            expect(chat_log.content[1].role).to_equal("user")
            expect(chat_log.content[1].content).to_equal(mock_conversation_input.text)


@test
async def chat_log_continue_conversation(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test continue conversation."""
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session) as chat_log,
    ):
        expect(chat_log.continue_conversation).to_be(False)
        chat_log.async_add_user_content(UserContent(mock_conversation_input.text))
        expect(chat_log.continue_conversation).to_be(False)
        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="mock-agent-id",
                content="Hey? ",
            )
        )
        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="mock-agent-id",
                content="Ποιο είναι το αγαπημένο σου χρώμα στα ελληνικά;",
            )
        )
        expect(chat_log.continue_conversation).to_be(True)


@test
async def chat_log_subscription(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_conversation_input: ConversationInput = Depends(mock_conversation_input),
) -> None:
    """Test comprehensive chat log subscription functionality."""
    with freeze_time("2025-10-31 12:00:00"):
        # Track all events received
        received_events = []

        def event_callback(
            conversation_id: str, event_type: ChatLogEventType, data: dict[str, Any]
        ) -> None:
            """Track received events."""
            received_events.append((conversation_id, event_type, data))

        # Subscribe to chat log events
        unsubscribe = async_subscribe_chat_logs(hass, event_callback)

        with (
            chat_session.async_get_chat_session(hass) as session,
            async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
        ):
            conversation_id = session.conversation_id

            # Test adding different types of content and verify events are sent
            chat_log.async_add_user_content(
                UserContent(
                    content="Check this image",
                    attachments=[
                        Attachment(
                            mime_type="image/jpeg",
                            media_content_id="media-source://bla",
                            path=Path("test_image.jpg"),
                        )
                    ],
                )
            )
            # Check user content with attachments event
            expect(received_events[-1][1]).to_equal(ChatLogEventType.CONTENT_ADDED)
            user_event = received_events[-1][2]["content"]
            expect(user_event["content"]).to_equal("Check this image")
            expect(len(user_event["attachments"])).to_equal(1)
            expect(user_event["attachments"][0]["mime_type"]).to_equal("image/jpeg")

            chat_log.async_add_assistant_content_without_tools(
                AssistantContent(
                    agent_id="test-agent", content="Hello! How can I help you?"
                )
            )
            # Check basic assistant content event
            expect(received_events[-1][1]).to_equal(ChatLogEventType.CONTENT_ADDED)
            basic_event = received_events[-1][2]["content"]
            expect(basic_event["content"]).to_equal("Hello! How can I help you?")
            expect(basic_event["agent_id"]).to_equal("test-agent")

            chat_log.async_add_assistant_content_without_tools(
                AssistantContent(
                    agent_id="test-agent",
                    content="Let me think about that...",
                    thinking_content="I need to analyze the user's request carefully.",
                )
            )
            # Check assistant content with thinking event
            expect(received_events[-1][1]).to_equal(ChatLogEventType.CONTENT_ADDED)
            thinking_event = received_events[-1][2]["content"]
            expect(thinking_event["thinking_content"]).to_equal(
                "I need to analyze the user's request carefully."
            )

            chat_log.async_add_assistant_content_without_tools(
                AssistantContent(
                    agent_id="test-agent",
                    content="Here's some data:",
                    native={"type": "chart", "data": [1, 2, 3, 4, 5]},
                )
            )
            # Check assistant content with native event
            expect(received_events[-1][1]).to_equal(ChatLogEventType.CONTENT_ADDED)
            native_event = received_events[-1][2]["content"]
            expect(native_event["content"]).to_equal("Here's some data:")
            expect(native_event["agent_id"]).to_equal("test-agent")

            chat_log.async_add_assistant_content_without_tools(
                ToolResultContent(
                    agent_id="test-agent",
                    tool_call_id="test-tool-call-123",
                    tool_name="test_tool",
                    tool_result="Tool execution completed successfully",
                )
            )
            # Check tool result content event
            expect(received_events[-1][1]).to_equal(ChatLogEventType.CONTENT_ADDED)
            tool_result_event = received_events[-1][2]["content"]
            expect(tool_result_event["tool_name"]).to_equal("test_tool")
            expect(tool_result_event["tool_result"]).to_equal(
                "Tool execution completed successfully"
            )

            chat_log.async_add_assistant_content_without_tools(
                AssistantContent(
                    agent_id="test-agent",
                    content="I'll call an external service",
                    tool_calls=[
                        llm.ToolInput(
                            id="external-tool-call-123",
                            tool_name="external_api_call",
                            tool_args={"endpoint": "https://api.example.com/data"},
                            external=True,
                        )
                    ],
                )
            )
            # Check external tool call event
            expect(received_events[-1][1]).to_equal(ChatLogEventType.CONTENT_ADDED)
            external_tool_event = received_events[-1][2]["content"]
            expect(len(external_tool_event["tool_calls"])).to_equal(1)
            expect(external_tool_event["tool_calls"][0].tool_name).to_equal(
                "external_api_call"
            )

        # Verify we received the expected events
        # Should have: 1 CREATED event + 7 CONTENT_ADDED events
        expect(len(received_events)).to_equal(8)

        # Check the first event is CREATED
        expect(received_events[0][1]).to_equal(ChatLogEventType.CREATED)
        expect(received_events[0][2]["chat_log"]["conversation_id"]).to_equal(
            conversation_id
        )

        # Check the second event is CONTENT_ADDED (from mock_conversation_input)
        expect(received_events[1][1]).to_equal(ChatLogEventType.CONTENT_ADDED)
        expect(received_events[1][0]).to_equal(conversation_id)

        # Test cleanup functionality
        expect(
            conversation_id in hass.data[chat_session.DATA_CHAT_SESSION]
        ).to_be(True)

        # Set the last updated to be older than the timeout
        hass.data[chat_session.DATA_CHAT_SESSION][conversation_id].last_updated = (
            dt_util.utcnow() + chat_session.CONVERSATION_TIMEOUT
        )

        async_fire_time_changed(
            hass,
            dt_util.utcnow()
            + chat_session.CONVERSATION_TIMEOUT * 2
            + timedelta(seconds=1),
        )

        # Check that DELETED event was sent
        expect(received_events[-1][1]).to_equal(ChatLogEventType.DELETED)
        expect(received_events[-1][0]).to_equal(conversation_id)

        # Test that unsubscribing stops receiving events
        events_before_unsubscribe = len(received_events)
        unsubscribe()

        # Create a new session and add content - should not receive events
        with (
            chat_session.async_get_chat_session(hass) as session2,
            async_get_chat_log(hass, session2, mock_conversation_input) as chat_log2,
        ):
            chat_log2.async_add_assistant_content_without_tools(
                AssistantContent(
                    agent_id="test-agent", content="This should not be received"
                )
            )

        # Verify no new events were received after unsubscribing
        expect(len(received_events)).to_equal(events_before_unsubscribe)
