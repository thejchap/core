"""Tryke skip-stubs for open_router config flow tests.

Original tests use pytest indirect parametrize; full port deferred.
"""

from tryke import test

@test.skip("pytest indirect parametrize")
async def full_flow() -> None:
    """Stub for test_full_flow (port deferred)."""

@test.skip("pytest indirect parametrize")
async def second_account() -> None:
    """Stub for test_second_account (port deferred)."""

@test.skip("pytest indirect parametrize")
async def form_errors() -> None:
    """Stub for test_form_errors (port deferred)."""

@test.skip("pytest indirect parametrize")
async def duplicate_entry() -> None:
    """Stub for test_duplicate_entry (port deferred)."""

@test.skip("pytest indirect parametrize")
async def create_conversation_agent() -> None:
    """Stub for test_create_conversation_agent (port deferred)."""

@test.skip("pytest indirect parametrize")
async def create_conversation_agent_no_control() -> None:
    """Stub for test_create_conversation_agent_no_control (port deferred)."""

@test.skip("pytest indirect parametrize")
async def create_ai_task() -> None:
    """Stub for test_create_ai_task (port deferred)."""

@test.skip("pytest indirect parametrize")
async def subentry_exceptions() -> None:
    """Stub for test_subentry_exceptions (port deferred)."""

@test.skip("pytest indirect parametrize")
async def reconfigure_conversation_agent() -> None:
    """Stub for test_reconfigure_conversation_agent (port deferred)."""

@test.skip("pytest indirect parametrize")
async def reconfigure_ai_task() -> None:
    """Stub for test_reconfigure_ai_task (port deferred)."""

@test.skip("pytest indirect parametrize")
async def reconfigure_entry_not_loaded() -> None:
    """Stub for test_reconfigure_entry_not_loaded (port deferred)."""

@test.skip("pytest indirect parametrize")
async def reconfigure_conversation_agent_abort() -> None:
    """Stub for test_reconfigure_conversation_agent_abort (port deferred)."""

@test.skip("pytest indirect parametrize")
async def reconfigure_ai_task_abort() -> None:
    """Stub for test_reconfigure_ai_task_abort (port deferred)."""

@test.skip("pytest indirect parametrize")
async def create_conversation_agent_web_search() -> None:
    """Stub for test_create_conversation_agent_web_search (port deferred)."""

@test.skip("pytest indirect parametrize")
async def reconfigure_conversation_subentry_web_search_default() -> None:
    """Stub for test_reconfigure_conversation_subentry_web_search_default (port deferred)."""

@test.skip("pytest indirect parametrize")
async def reconfigure_conversation_subentry_llm_api_schema() -> None:
    """Stub for test_reconfigure_conversation_subentry_llm_api_schema (port deferred)."""
