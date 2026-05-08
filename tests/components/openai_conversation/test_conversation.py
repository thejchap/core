"""Tryke skip-stubs for openai_conversation conversation tests.

Original tests use OpenAI API mocks + conversation pipeline; full port deferred.
"""

from tryke import test

@test.skip("OpenAI API mocks + conversation pipeline")
async def entity() -> None:
    """Test entity properties."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def error_handling() -> None:
    """Test that we handle errors when calling completion API."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def incomplete_response() -> None:
    """Test handling early model stop."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def failed_response() -> None:
    """Test handling failed and error responses."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def conversation_agent() -> None:
    """Test OpenAIAgent."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def function_call() -> None:
    """Test function call from the assistant."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def function_call_without_reasoning() -> None:
    """Test function call from the assistant."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def reasoning_summary_off_omits_summary_key() -> None:
    """Test that reasoning summary 'off' omits the summary key from the API call."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def function_call_invalid() -> None:
    """Test function call containing invalid data."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def assist_api_tools_conversion() -> None:
    """Test that we are able to convert actual tools from Assist API."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def store_responses_forwarded_for_conversation_agent() -> None:
    """Test store_responses is forwarded for the conversation agent."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def web_search() -> None:
    """Test web_search_tool."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def code_interpreter() -> None:
    """Test code_interpreter tool."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def flex_tier_retry() -> None:
    """Test retry with default tier if flex tier unavailable."""
