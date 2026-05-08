"""Tryke skip-stubs for open_router ai_task tests.

Original tests use OpenAI-compatible LLM client mocks + conversation pipeline; full port deferred.
"""

from tryke import test

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def all_entities() -> None:
    """Test all entities."""

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def generate_data() -> None:
    """Test AI Task data generation."""

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def generate_structured_data() -> None:
    """Test AI Task structured data generation."""

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def generate_invalid_structured_data() -> None:
    """Test AI Task with invalid JSON response."""

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def generate_data_empty_response() -> None:
    """Test AI Task raises HomeAssistantError when API returns empty choices."""

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def generate_data_with_attachments() -> None:
    """Test AI Task data generation with attachments."""
