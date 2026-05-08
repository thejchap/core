"""Tryke skip-stubs for onvif util tests.

Original tests use ONVIF camera mocks + zeroconf discovery; full port deferred.
"""

from tryke import test

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def build_event_entity_names_unique_names() -> None:
    """Test build_event_entity_names with unique event names."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def build_event_entity_names_duplicated() -> None:
    """Test with multiple motion detection zones (realistic camera scenario)."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def build_event_entity_names_mixed_events() -> None:
    """Test realistic mix of unique and duplicate event names."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def build_event_entity_names_empty() -> None:
    """Test build_event_entity_names with empty list."""
