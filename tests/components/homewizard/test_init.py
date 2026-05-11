"""Tryke skip-stubs for test_init.py - sibling port deferred (256 LOC, 1 parametrize)."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.homewizard module imports cleanly."""
    from homeassistant.components import homewizard  # noqa: PLC0415
    expect(homewizard).not_.to_be(None)


@test.skip("sibling port deferred (256 LOC, 1 parametrize)")
async def load_unload_v1() -> None:
    """Stub for test_load_unload_v1."""

@test.skip("sibling port deferred (256 LOC, 1 parametrize)")
async def load_unload_v2() -> None:
    """Stub for test_load_unload_v2."""

@test.skip("sibling port deferred (256 LOC, 1 parametrize)")
async def load_failed_host_unavailable() -> None:
    """Stub for test_load_failed_host_unavailable."""

@test.skip("sibling port deferred (256 LOC, 1 parametrize)")
async def load_detect_api_disabled() -> None:
    """Stub for test_load_detect_api_disabled."""

@test.skip("sibling port deferred (256 LOC, 1 parametrize)")
async def load_detect_invalid_token() -> None:
    """Stub for test_load_detect_invalid_token."""

@test.skip("sibling port deferred (256 LOC, 1 parametrize)")
async def load_creates_repair_issue() -> None:
    """Stub for test_load_creates_repair_issue."""

@test.skip("sibling port deferred (256 LOC, 1 parametrize)")
async def load_creates_repair_issue_when_name_is_updated() -> None:
    """Stub for test_load_creates_repair_issue_when_name_is_updated."""

@test.skip("sibling port deferred (256 LOC, 1 parametrize)")
async def load_removes_reauth_flow() -> None:
    """Stub for test_load_removes_reauth_flow."""

@test.skip("sibling port deferred (256 LOC, 1 parametrize)")
async def disablederror_reloads_integration() -> None:
    """Stub for test_disablederror_reloads_integration."""
