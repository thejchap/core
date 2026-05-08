"""Tryke skip-stubs for mcp_server http tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def http_placeholder() -> None:
    """Placeholder skipped sibling tests for test_http.py."""
