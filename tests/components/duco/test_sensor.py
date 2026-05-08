"""Tryke skip stubs for test_sensor - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_entities_state() -> None:
    """Stub for test_sensor_entities_state (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def iaq_sensor_entities_disabled_by_default() -> None:
    """Stub for test_iaq_sensor_entities_disabled_by_default (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def diagnostic_sensor_entities_disabled_by_default() -> None:
    """Stub for test_diagnostic_sensor_entities_disabled_by_default (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_update_marks_unavailable() -> None:
    """Stub for test_coordinator_update_marks_unavailable (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_update_duco_error_marks_unavailable() -> None:
    """Stub for test_coordinator_update_duco_error_marks_unavailable (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def lan_info_duco_error_marks_unavailable() -> None:
    """Stub for test_lan_info_duco_error_marks_unavailable (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def new_node_added_dynamically() -> None:
    """Stub for test_new_node_added_dynamically (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def deregistered_node_removes_device() -> None:
    """Stub for test_deregistered_node_removes_device (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unknown_node_type_logs_warning_and_creates_no_entities() -> None:
    """Stub for test_unknown_node_type_logs_warning_and_creates_no_entities (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def previously_unknown_node_gets_entities_after_type_becomes_known() -> None:
    """Stub for test_previously_unknown_node_gets_entities_after_type_becomes_known (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unknown_node_logged_at_debug() -> None:
    """Stub for test_unknown_node_logged_at_debug (port deferred)."""


