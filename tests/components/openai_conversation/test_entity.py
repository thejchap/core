"""Tryke skip-stubs for openai_conversation entity tests.

Original tests use OpenAI API mocks + conversation pipeline; full port deferred.
"""

from tryke import test

@test.skip("OpenAI API mocks + conversation pipeline")
async def format_structured_output() -> None:
    """Test the format_structured_output function."""
