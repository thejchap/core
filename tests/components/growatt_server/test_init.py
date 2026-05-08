"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the growatt_server integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.growatt_server.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("growatt_server")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_info() -> None:
    """Stub for test_device_info."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_error_on_api_failure() -> None:
    """Stub for test_setup_error_on_api_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_update_failed() -> None:
    """Stub for test_coordinator_update_failed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_update_json_error() -> None:
    """Stub for test_coordinator_update_json_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_total_non_auth_api_error() -> None:
    """Stub for test_coordinator_total_non_auth_api_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_auth_failed_on_permission_denied() -> None:
    """Stub for test_setup_auth_failed_on_permission_denied."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_auth_failed_triggers_reauth() -> None:
    """Stub for test_coordinator_auth_failed_triggers_reauth."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def classic_api_coordinator_auth_failed_triggers_reauth() -> None:
    """Stub for test_classic_api_coordinator_auth_failed_triggers_reauth."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def classic_api_setup() -> None:
    """Stub for test_classic_api_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_config_without_auth_type() -> None:
    """Stub for test_migrate_config_without_auth_type."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_legacy_config_no_auth_fields() -> None:
    """Stub for test_migrate_legacy_config_no_auth_fields."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def classic_api_login_exceptions() -> None:
    """Stub for test_classic_api_login_exceptions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def classic_api_login_failures() -> None:
    """Stub for test_classic_api_login_failures."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def classic_api_device_list_exceptions() -> None:
    """Stub for test_classic_api_device_list_exceptions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def classic_api_device_list_no_devices() -> None:
    """Stub for test_classic_api_device_list_no_devices."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def classic_api_device_list_errors() -> None:
    """Stub for test_classic_api_device_list_errors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unknown_api_version() -> None:
    """Stub for test_unknown_api_version."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def classic_api_auto_select_plant() -> None:
    """Stub for test_classic_api_auto_select_plant."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def v1_api_unsupported_device_type() -> None:
    """Stub for test_v1_api_unsupported_device_type."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_version_bump() -> None:
    """Stub for test_migrate_version_bump."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_reuses_cached_api_from_migration() -> None:
    """Stub for test_setup_reuses_cached_api_from_migration."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_failure_returns_false() -> None:
    """Stub for test_migrate_failure_returns_false."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_already_migrated() -> None:
    """Stub for test_migrate_already_migrated."""

