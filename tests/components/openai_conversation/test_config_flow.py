"""Tryke skip-stubs for openai_conversation config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def duplicate_entry() -> None:
    """Stub for test_duplicate_entry (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def creating_conversation_subentry() -> None:
    """Stub for test_creating_conversation_subentry (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def creating_conversation_subentry_not_loaded() -> None:
    """Stub for test_creating_conversation_subentry_not_loaded (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def subentry_recommended() -> None:
    """Stub for test_subentry_recommended (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def subentry_unsupported_model() -> None:
    """Stub for test_subentry_unsupported_model (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def subentry_reasoning_effort_list() -> None:
    """Stub for test_subentry_reasoning_effort_list (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def subentry_reasoning_summary_visibility() -> None:
    """Stub for test_subentry_reasoning_summary_visibility (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def subentry_reasoning_summary_options() -> None:
    """Stub for test_subentry_reasoning_summary_options (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def subentry_reasoning_summary_default_sanitized_on_model_switch() -> None:
    """Stub for test_subentry_reasoning_summary_default_sanitized_on_model_switch (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def subentry_service_tier_list() -> None:
    """Stub for test_subentry_service_tier_list (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def subentry_unsupported_reasoning_effort() -> None:
    """Stub for test_subentry_unsupported_reasoning_effort (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def form_invalid_auth() -> None:
    """Stub for test_form_invalid_auth (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def subentry_switching() -> None:
    """Stub for test_subentry_switching (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def subentry_web_search_user_location() -> None:
    """Stub for test_subentry_web_search_user_location (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def creating_ai_task_subentry() -> None:
    """Stub for test_creating_ai_task_subentry (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def ai_task_subentry_not_loaded() -> None:
    """Stub for test_ai_task_subentry_not_loaded (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def creating_ai_task_subentry_advanced() -> None:
    """Stub for test_creating_ai_task_subentry_advanced (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def creating_stt_subentry() -> None:
    """Stub for test_creating_stt_subentry (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def stt_subentry_not_loaded() -> None:
    """Stub for test_stt_subentry_not_loaded (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def stt_reconfigure() -> None:
    """Stub for test_stt_reconfigure (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def creating_tts_subentry() -> None:
    """Stub for test_creating_tts_subentry (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def tts_subentry_not_loaded() -> None:
    """Stub for test_tts_subentry_not_loaded (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def tts_reconfigure() -> None:
    """Stub for test_tts_reconfigure (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def reauth() -> None:
    """Stub for test_reauth (port deferred)."""

@test.skip("requires OpenAI subentry chain + multiple subentry types (not ported)")
async def reconfigure_conversation_subentry_llm_api_schema() -> None:
    """Stub for test_reconfigure_conversation_subentry_llm_api_schema (port deferred)."""
