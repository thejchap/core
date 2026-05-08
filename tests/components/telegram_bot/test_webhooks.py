"""Tryke skip stub for test_webhooks.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("telegram_bot: sibling test pending tryke port — needs: hass_client")
async def webhooks() -> None:
    """Placeholder skipped sibling tests."""
