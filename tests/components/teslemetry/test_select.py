"""Tryke skip-stubs for teslemetry/test_select.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def select() -> None:
    """Stub for test_select."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def select_services() -> None:
    """Stub for test_select_services."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def select_invalid_data() -> None:
    """Stub for test_select_invalid_data."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def select_streaming() -> None:
    """Stub for test_select_streaming."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def export_rule_restore() -> None:
    """Stub for test_export_rule_restore."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def export_rule_update_attrs_logic() -> None:
    """Stub for test_export_rule_update_attrs_logic."""

