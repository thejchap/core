"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_auth_failed_triggers_reauth() -> None:
    """Stub for test_config_entry_auth_failed_triggers_reauth."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_setup_errors() -> None:
    """Stub for test_config_entry_setup_errors."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_dhw_config_update_error() -> None:
    """Stub for test_coordinator_dhw_config_update_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_slow_first_fetch_failure() -> None:
    """Stub for test_coordinator_slow_first_fetch_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_timeout_error() -> None:
    """Stub for test_config_entry_timeout_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_fast_no_dhw_support() -> None:
    """Stub for test_coordinator_fast_no_dhw_support."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_fast_dhw_fails_on_refresh_preserves_state() -> None:
    """Stub for test_coordinator_fast_dhw_fails_on_refresh_preserves_state."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_slow_no_dhw_support() -> None:
    """Stub for test_coordinator_slow_no_dhw_support."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def configuration_url_default_port() -> None:
    """Stub for test_configuration_url_default_port."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def configuration_url_non_default_port() -> None:
    """Stub for test_configuration_url_non_default_port."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrate_entry_discovers_circuits() -> None:
    """Stub for test_migrate_entry_discovers_circuits."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrate_entry_discovery_failure_falls_back() -> None:
    """Stub for test_migrate_entry_discovery_failure_falls_back."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrate_entry_discovery_timeout_falls_back() -> None:
    """Stub for test_migrate_entry_discovery_timeout_falls_back."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrate_entry_future_version_aborts() -> None:
    """Stub for test_migrate_entry_future_version_aborts."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrate_entry_already_current() -> None:
    """Stub for test_migrate_entry_already_current."""

