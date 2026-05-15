"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires mqtt_mock (not in tryke shim)")
async def setup_succeeds() -> None:
    """Stub for test_setup_succeeds (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def setup_no_mqtt() -> None:
    """Stub for test_setup_no_mqtt (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def setup_with_pub() -> None:
    """Stub for test_setup_with_pub (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def subscribe() -> None:
    """Stub for test_subscribe (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_sends_message() -> None:
    """Stub for test_state_changed_event_sends_message (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def time_event_does_not_send_message() -> None:
    """Stub for test_time_event_does_not_send_message (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def receiving_remote_event_fires_hass_event() -> None:
    """Stub for test_receiving_remote_event_fires_hass_event (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def receiving_blocked_event_fires_hass_event() -> None:
    """Stub for test_receiving_blocked_event_fires_hass_event (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def ignored_event_doesnt_send_over_stream() -> None:
    """Stub for test_ignored_event_doesnt_send_over_stream (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def wrong_ignored_event_sends_over_stream() -> None:
    """Stub for test_wrong_ignored_event_sends_over_stream (port deferred)."""
