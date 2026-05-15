"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires mqtt_mock (not in tryke shim)")
async def setup_fails_without_mqtt_being_setup() -> None:
    """Stub for test_setup_fails_without_mqtt_being_setup (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def ensure_device_tracker_platform_validation() -> None:
    """Stub for test_ensure_device_tracker_platform_validation (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def json_message() -> None:
    """Stub for test_json_message (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def non_json_message() -> None:
    """Stub for test_non_json_message (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def incomplete_message() -> None:
    """Stub for test_incomplete_message (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def single_level_wildcard_topic() -> None:
    """Stub for test_single_level_wildcard_topic (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def multi_level_wildcard_topic() -> None:
    """Stub for test_multi_level_wildcard_topic (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def single_level_wildcard_topic_not_matching() -> None:
    """Stub for test_single_level_wildcard_topic_not_matching (port deferred)."""

@test.skip("requires mqtt_mock (not in tryke shim)")
async def multi_level_wildcard_topic_not_matching() -> None:
    """Stub for test_multi_level_wildcard_topic_not_matching (port deferred)."""
