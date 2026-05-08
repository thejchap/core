"""Tryke skip-stubs for ollama config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def duplicate_entry() -> None:
    """Stub for test_duplicate_entry (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def subentry_options() -> None:
    """Stub for test_subentry_options (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def creating_new_conversation_subentry() -> None:
    """Stub for test_creating_new_conversation_subentry (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def creating_conversation_subentry_not_loaded() -> None:
    """Stub for test_creating_conversation_subentry_not_loaded (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def subentry_need_download() -> None:
    """Stub for test_subentry_need_download (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def subentry_download_error() -> None:
    """Stub for test_subentry_download_error (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def reauth_flow_success() -> None:
    """Stub for test_reauth_flow_success (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def reauth_flow_errors() -> None:
    """Stub for test_reauth_flow_errors (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def form_errors() -> None:
    """Stub for test_form_errors (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def form_errors_recovery() -> None:
    """Stub for test_form_errors_recovery (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def form_invalid_url() -> None:
    """Stub for test_form_invalid_url (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def subentry_connection_error() -> None:
    """Stub for test_subentry_connection_error (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def subentry_model_check_exception() -> None:
    """Stub for test_subentry_model_check_exception (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def subentry_reconfigure_with_download() -> None:
    """Stub for test_subentry_reconfigure_with_download (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def filter_invalid_llms() -> None:
    """Stub for test_filter_invalid_llms (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def creating_ai_task_subentry() -> None:
    """Stub for test_creating_ai_task_subentry (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def ai_task_subentry_not_loaded() -> None:
    """Stub for test_ai_task_subentry_not_loaded (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def user_step_async_client_headers() -> None:
    """Stub for test_user_step_async_client_headers (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def user_step_errors() -> None:
    """Stub for test_user_step_errors (port deferred)."""

@test.skip("requires ollama subentry chain + LLM API integration (not ported)")
async def user_step_trim_url() -> None:
    """Stub for test_user_step_trim_url (port deferred)."""
