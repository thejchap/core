"""Tryke skip-stubs for open_router conversation tests.

Original tests use OpenAI-compatible LLM client mocks + conversation pipeline; full port deferred.
"""

from tryke import test

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def all_entities() -> None:
    """Test all entities."""

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def default_prompt() -> None:
    """Test that the default prompt works."""

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def web_search() -> None:
    """Test that web search adds :online suffix to model."""

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def empty_api_response() -> None:
    """Test that an empty choices response raises HomeAssistantError."""

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def function_call() -> None:
    """Test function call from the assistant."""
