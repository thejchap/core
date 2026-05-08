"""Tryke skip-stubs for open_router init tests.

Original tests use OpenAI-compatible LLM client mocks + conversation pipeline; full port deferred.
"""

from tryke import test

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def migrate_entry_from_v1_1_to_v1_2() -> None:
    """Test migration from version 1.1 to 1.2."""

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def migrate_entry_already_migrated() -> None:
    """Test migration is skipped when already on version 1.2."""

@test.skip("OpenAI-compatible LLM client mocks + conversation pipeline")
async def migrate_entry_from_future_version_fails() -> None:
    """Test migration fails for future versions."""
