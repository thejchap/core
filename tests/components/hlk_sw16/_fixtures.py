"""Tryke fixtures for the Hi-Link HLK-SW16 integration."""

from tryke import fixture


@fixture
def _module_marker() -> None:
    """Sentinel fixture to keep the module non-empty."""
    return None
