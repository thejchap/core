"""Tryke skip stub for test_stt.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def demo_settings() -> None:
    """Stub for test_demo_settings."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def demo_speech_no_metadata() -> None:
    """Stub for test_demo_speech_no_metadata."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def demo_speech_wrong_metadata() -> None:
    """Stub for test_demo_speech_wrong_metadata."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def demo_speech() -> None:
    """Stub for test_demo_speech."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_demo_speech() -> None:
    """Stub for test_config_entry_demo_speech."""

