"""Tryke skip stub for test_conversation.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_generative_ai_conversation.conversation module imports cleanly."""
    from homeassistant.components.google_generative_ai_conversation import conversation  # noqa: PLC0415
    expect(conversation).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def error_handling() -> None:
    """Stub for test_error_handling."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def function_call() -> None:
    """Stub for test_function_call."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def google_search_tool_is_sent() -> None:
    """Stub for test_google_search_tool_is_sent."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def blocked_response() -> None:
    """Stub for test_blocked_response."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def empty_response() -> None:
    """Stub for test_empty_response."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def none_response() -> None:
    """Stub for test_none_response."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def converse_error() -> None:
    """Stub for test_converse_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def conversation_agent() -> None:
    """Stub for test_conversation_agent."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def escape_decode() -> None:
    """Stub for test_escape_decode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def format_schema() -> None:
    """Stub for test_format_schema."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def empty_content_in_chat_history() -> None:
    """Stub for test_empty_content_in_chat_history."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def history_always_user_first_turn() -> None:
    """Stub for test_history_always_user_first_turn."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def token_stats_reported() -> None:
    """Stub for test_token_stats_reported."""

