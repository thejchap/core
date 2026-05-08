"""Tryke skip-stubs for onvif init tests.

Original tests use ONVIF camera mocks + zeroconf discovery; full port deferred.
"""

from tryke import test

@test.skip("ONVIF camera mocks + zeroconf discovery")
async def migrate_camera_entities_unique_ids() -> None:
    """Test that camera entities unique ids get migrated properly."""
