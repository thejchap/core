"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires mqtt_mock (not in tryke shim)")
async def fails_with_no_base() -> None:
    """Stub for test_fails_with_no_base (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def setup_succeeds_without_attributes() -> None:
    """Stub for test_setup_succeeds_without_attributes (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def setup_and_stop_waits_for_ha() -> None:
    """Stub for test_setup_and_stop_waits_for_ha (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def startup_no_mqtt() -> None:
    """Stub for test_startup_no_mqtt (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def setup_succeeds_with_attributes() -> None:
    """Stub for test_setup_succeeds_with_attributes (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_sends_message() -> None:
    """Stub for test_state_changed_event_sends_message (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_sends_message_and_timestamp() -> None:
    """Stub for test_state_changed_event_sends_message_and_timestamp (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_attr_sends_message() -> None:
    """Stub for test_state_changed_attr_sends_message (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_include_domain() -> None:
    """Stub for test_state_changed_event_include_domain (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_include_entity() -> None:
    """Stub for test_state_changed_event_include_entity (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_exclude_domain() -> None:
    """Stub for test_state_changed_event_exclude_domain (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_exclude_entity() -> None:
    """Stub for test_state_changed_event_exclude_entity (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_exclude_domain_include_entity() -> None:
    """Stub for test_state_changed_event_exclude_domain_include_entity (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_include_domain_exclude_entity() -> None:
    """Stub for test_state_changed_event_include_domain_exclude_entity (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_include_globs() -> None:
    """Stub for test_state_changed_event_include_globs (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_exclude_globs() -> None:
    """Stub for test_state_changed_event_exclude_globs (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_exclude_domain_globs_include_entity() -> None:
    """Stub for test_state_changed_event_exclude_domain_globs_include_entity (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def state_changed_event_include_domain_globs_exclude_entity() -> None:
    """Stub for test_state_changed_event_include_domain_globs_exclude_entity (port deferred)."""
