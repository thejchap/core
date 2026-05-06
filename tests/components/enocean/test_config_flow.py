"""Tryke skip-stubs for enocean config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_cannot_create_multiple_instances() -> None:
    """Stub for test_user_flow_cannot_create_multiple_instances (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_with_detected_dongle() -> None:
    """Stub for test_user_flow_with_detected_dongle (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_with_no_detected_dongle() -> None:
    """Stub for test_user_flow_with_no_detected_dongle (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def detection_flow_with_valid_path() -> None:
    """Stub for test_detection_flow_with_valid_path (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def detection_flow_with_custom_path() -> None:
    """Stub for test_detection_flow_with_custom_path (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def detection_flow_with_invalid_path() -> None:
    """Stub for test_detection_flow_with_invalid_path (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def manual_flow_with_valid_path() -> None:
    """Stub for test_manual_flow_with_valid_path (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def manual_flow_with_invalid_path() -> None:
    """Stub for test_manual_flow_with_invalid_path (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def import_flow_with_valid_path() -> None:
    """Stub for test_import_flow_with_valid_path (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def import_flow_with_invalid_path() -> None:
    """Stub for test_import_flow_with_invalid_path (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def usb_discovery() -> None:
    """Stub for test_usb_discovery (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def usb_discovery_already_configured_updates_path() -> None:
    """Stub for test_usb_discovery_already_configured_updates_path (port deferred)."""
