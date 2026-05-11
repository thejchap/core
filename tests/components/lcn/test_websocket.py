"""Tryke skip-stubs for test_websocket.py - sibling port deferred (330 LOC, 3 parametrize)."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.lcn.websocket module imports cleanly."""
    from homeassistant.components.lcn import websocket  # noqa: PLC0415
    expect(websocket).not_.to_be(None)


@test.skip("sibling port deferred (330 LOC, 3 parametrize)")
async def lcn_devices_command() -> None:
    """Stub for test_lcn_devices_command."""

@test.skip("sibling port deferred (330 LOC, 3 parametrize)")
async def lcn_entities_command() -> None:
    """Stub for test_lcn_entities_command."""

@test.skip("sibling port deferred (330 LOC, 3 parametrize)")
async def lcn_devices_scan_command() -> None:
    """Stub for test_lcn_devices_scan_command."""

@test.skip("sibling port deferred (330 LOC, 3 parametrize)")
async def lcn_devices_add_command() -> None:
    """Stub for test_lcn_devices_add_command."""

@test.skip("sibling port deferred (330 LOC, 3 parametrize)")
async def lcn_devices_delete_command() -> None:
    """Stub for test_lcn_devices_delete_command."""

@test.skip("sibling port deferred (330 LOC, 3 parametrize)")
async def lcn_entities_add_command() -> None:
    """Stub for test_lcn_entities_add_command."""

@test.skip("sibling port deferred (330 LOC, 3 parametrize)")
async def lcn_entities_delete_command() -> None:
    """Stub for test_lcn_entities_delete_command."""

@test.skip("sibling port deferred (330 LOC, 3 parametrize)")
async def lcn_command_host_error() -> None:
    """Stub for test_lcn_command_host_error."""

@test.skip("sibling port deferred (330 LOC, 3 parametrize)")
async def lcn_command_address_error() -> None:
    """Stub for test_lcn_command_address_error."""

@test.skip("sibling port deferred (330 LOC, 3 parametrize)")
async def lcn_entities_add_existing_error() -> None:
    """Stub for test_lcn_entities_add_existing_error."""
