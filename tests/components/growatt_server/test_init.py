"""Tryke port for the growatt_server integration init tests."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.growatt_server import async_migrate_entry
from homeassistant.components.growatt_server.const import (
    AUTH_PASSWORD,
    CONF_AUTH_TYPE,
    CONF_PLANT_ID,
    DOMAIN,
)
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level trigger fixture so tryke fully resolves Depends."""


@test
def domain_const_importable() -> None:
    """Smoke test: the growatt_server integration's DOMAIN constant imports cleanly."""
    expect(DOMAIN).to_equal("growatt_server")


@test
async def migrate_already_migrated(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migration is skipped for already migrated entries."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_AUTH_TYPE: AUTH_PASSWORD,
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
            CONF_URL: "https://server.growatt.com/",
            CONF_PLANT_ID: "specific_plant_123",
        },
        unique_id="plant_specific",
        version=1,
        minor_version=1,
    )

    mock_config_entry.add_to_hass(hass)

    migration_result = await async_migrate_entry(hass, mock_config_entry)
    expect(migration_result).to_be(True)

    # Verify version remains 1.1 (no change)
    expect(mock_config_entry.version).to_equal(1)
    expect(mock_config_entry.minor_version).to_equal(1)

    # Plant ID should remain unchanged
    expect(mock_config_entry.data[CONF_PLANT_ID]).to_equal("specific_plant_123")


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



