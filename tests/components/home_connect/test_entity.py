"""Tryke skip-stubs for test_entity.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def program_options_retrieval() -> None:
    """Stub for test_program_options_retrieval."""

@test.skip("indirect parametrize unsupported")
async def no_options_retrieval_on_unknown_program() -> None:
    """Stub for test_no_options_retrieval_on_unknown_program."""

@test.skip("indirect parametrize unsupported")
async def program_options_retrieval_after_appliance_connection() -> None:
    """Stub for test_program_options_retrieval_after_appliance_connection."""

@test.skip("indirect parametrize unsupported")
async def option_entity_functionality_exception() -> None:
    """Stub for test_option_entity_functionality_exception."""
