"""Tryke skip stub for test_event.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_doorbell() -> None:
    """Stub for test_create_doorbell."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_doorbell_offline() -> None:
    """Stub for test_create_doorbell_offline."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_doorbell_with_motion() -> None:
    """Stub for test_create_doorbell_with_motion."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def doorbell_update_via_pubnub() -> None:
    """Stub for test_doorbell_update_via_pubnub."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_lock_with_doorbell() -> None:
    """Stub for test_create_lock_with_doorbell."""

