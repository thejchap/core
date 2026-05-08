"""Tryke skip stub for test_subscription.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def fetching_subscription_with_api_error() -> None:
    """Stub for test_fetching_subscription_with_api_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def fetching_subscription_with_timeout_error() -> None:
    """Stub for test_fetching_subscription_with_timeout_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrate_paypal_agreement_with_timeout_error() -> None:
    """Stub for test_migrate_paypal_agreement_with_timeout_error."""

