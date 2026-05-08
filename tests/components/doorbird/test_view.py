"""Tryke skip stub for test_view.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def non_webhook_with_wrong_token() -> None:
    """Stub for test_non_webhook_with_wrong_token."""

