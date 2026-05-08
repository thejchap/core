"""Tryke skip-stubs for test_init.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def load_missing_scope() -> None:
    """Stub for test_load_missing_scope."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def expired_token_refresh_failure() -> None:
    """Stub for test_expired_token_refresh_failure."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def update_failed() -> None:
    """Stub for test_update_failed."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def websocket_not_available() -> None:
    """Stub for test_websocket_not_available."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def model_id_information() -> None:
    """Stub for test_model_id_information."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def device_info() -> None:
    """Stub for test_device_info."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def constant_polling() -> None:
    """Stub for test_constant_polling."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def coordinator_automatic_registry_cleanup() -> None:
    """Stub for test_coordinator_automatic_registry_cleanup."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def add_and_remove_work_area() -> None:
    """Stub for test_add_and_remove_work_area."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def dynamic_polling() -> None:
    """Stub for test_dynamic_polling."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def websocket_watchdog() -> None:
    """Stub for test_websocket_watchdog."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available."""
