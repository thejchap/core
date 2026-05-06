"""Tryke fixtures for the music_assistant integration."""

from tryke import fixture


@fixture
def _module_marker() -> None:
    """Sentinel fixture to keep the module non-empty."""
    return None
