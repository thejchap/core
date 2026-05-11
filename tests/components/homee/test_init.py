"""Tryke skip-stubs for test_init.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.homee module imports cleanly."""
    from homeassistant.components import homee  # noqa: PLC0415
    expect(homee).not_.to_be(None)


@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def connection_errors() -> None:
    """Stub for test_connection_errors."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def connection_listener() -> None:
    """Stub for test_connection_listener."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def general_data() -> None:
    """Stub for test_general_data."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def software_version() -> None:
    """Stub for test_software_version."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def invalid_profile() -> None:
    """Stub for test_invalid_profile."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def remove_stale_device_on_startup() -> None:
    """Stub for test_remove_stale_device_on_startup."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def remove_node_callback() -> None:
    """Stub for test_remove_node_callback."""
