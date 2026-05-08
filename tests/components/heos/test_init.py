"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the heos integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.heos.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("heos")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry_loads_platforms() -> None:
    """Stub for test_async_setup_entry_loads_platforms."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry_with_options_loads_platforms() -> None:
    """Stub for test_async_setup_entry_with_options_loads_platforms."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry_auth_failure_starts_reauth() -> None:
    """Stub for test_async_setup_entry_auth_failure_starts_reauth."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry_not_signed_in_loads_platforms() -> None:
    """Stub for test_async_setup_entry_not_signed_in_loads_platforms."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry_connect_failure() -> None:
    """Stub for test_async_setup_entry_connect_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry_player_failure() -> None:
    """Stub for test_async_setup_entry_player_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry_favorites_failure() -> None:
    """Stub for test_async_setup_entry_favorites_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry_inputs_failure() -> None:
    """Stub for test_async_setup_entry_inputs_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_info() -> None:
    """Stub for test_device_info."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_id_migration() -> None:
    """Stub for test_device_id_migration."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_id_migration_both_present() -> None:
    """Stub for test_device_id_migration_both_present."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remove_config_entry_device() -> None:
    """Stub for test_remove_config_entry_device."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reconnected_new_entities_created() -> None:
    """Stub for test_reconnected_new_entities_created."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reconnected_failover_updates_host() -> None:
    """Stub for test_reconnected_failover_updates_host."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def players_changed_new_entities_created() -> None:
    """Stub for test_players_changed_new_entities_created."""

