"""Tryke skip stub for test_entity.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def format_structured_output() -> None:
    """Stub for test_format_structured_output."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def prepare_files_for_prompt() -> None:
    """Stub for test_prepare_files_for_prompt."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def prepare_files_for_prompt_invalid_type() -> None:
    """Stub for test_prepare_files_for_prompt_invalid_type."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def prepare_chat_for_generation_appends_attachments() -> None:
    """Stub for test_prepare_chat_for_generation_appends_attachments."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def prepare_chat_for_generation_passes_messages_through() -> None:
    """Stub for test_prepare_chat_for_generation_passes_messages_through."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_handle_chat_log_service_sets_structured_output_non_strict() -> None:
    """Stub for test_async_handle_chat_log_service_sets_structured_output_non_strict."""

