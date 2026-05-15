"""Tryke skip stub for QNAP QSW button tests."""

from tryke import test


@test.skip("requires translation injection for ButtonDeviceClass.RESTART entity_id slug")
async def qnap_buttons() -> None:
    """Stub for test_qnap_buttons (port deferred)."""
