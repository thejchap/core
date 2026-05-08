"""Tryke skip-stubs for openai_conversation ai_task tests.

Original tests use OpenAI API mocks + conversation pipeline; full port deferred.
"""

from tryke import test

@test.skip("OpenAI API mocks + conversation pipeline")
async def generate_data() -> None:
    """Test AI Task data generation."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def generate_structured_data() -> None:
    """Test AI Task structured data generation."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def generate_invalid_structured_data() -> None:
    """Test AI Task with invalid JSON response."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def generate_data_with_attachments() -> None:
    """Test AI Task data generation with attachments."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def generate_image() -> None:
    """Test AI Task image generation."""

@test.skip("OpenAI API mocks + conversation pipeline")
async def repair_issue() -> None:
    """Test that repair issue is raised when verification is required."""
