"""Tryke skip-stubs for onvif event_manager tests.

Original tests use ONVIF camera mocks + zeroconf discovery; full port deferred.
"""

from tryke import test

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def motion_alarm_event() -> None:
    """Test that a motion alarm event creates a binary sensor."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def motion_alarm_event_off() -> None:
    """Test that a motion alarm event with false value is off."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def diagnostic_event_entity_category() -> None:
    """Test that a diagnostic event gets the correct entity category."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def timestamp_event_conversion() -> None:
    """Test that timestamp sensor events get string values converted to datetime."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def timestamp_event_invalid_value() -> None:
    """Test that invalid timestamp values result in unknown state."""

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def multiple_events_same_topic() -> None:
    """Test that multiple events with the same topic are all processed."""
