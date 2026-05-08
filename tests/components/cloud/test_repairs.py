"""Tryke skip stub for test_repairs.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def do_not_create_repair_issues_at_startup_if_not_logged_in() -> None:
    """Stub for test_do_not_create_repair_issues_at_startup_if_not_logged_in."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def create_repair_issues_at_startup_if_logged_in() -> None:
    """Stub for test_create_repair_issues_at_startup_if_logged_in."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def legacy_subscription_delete_issue_if_no_longer_legacy() -> None:
    """Stub for test_legacy_subscription_delete_issue_if_no_longer_legacy."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def legacy_subscription_repair_flow() -> None:
    """Stub for test_legacy_subscription_repair_flow."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def legacy_subscription_repair_flow_timeout() -> None:
    """Stub for test_legacy_subscription_repair_flow_timeout."""

