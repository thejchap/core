"""Tests for the Switch as X."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.switch_as_x.config_flow import SwitchAsXConfigFlowHandler
from homeassistant.components.switch_as_x.const import (
    CONF_INVERT,
    CONF_TARGET_DOMAIN,
    DOMAIN,
)
from homeassistant.const import CONF_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test.cases(
    test.case("cover", target_domain=Platform.COVER),
    test.case("fan", target_domain=Platform.FAN),
    test.case("light", target_domain=Platform.LIGHT),
    test.case("lock", target_domain=Platform.LOCK),
    test.case("siren", target_domain=Platform.SIREN),
    test.case("valve", target_domain=Platform.VALVE),
)
async def config_entry_unregistered_uuid(
    target_domain: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test light switch setup from config entry with unknown entity registry id."""
    fake_uuid = "a266a680b608c32770e6c45bfe6b8411"

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: fake_uuid,
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        },
        title="ABC",
        version=SwitchAsXConfigFlowHandler.VERSION,
        minor_version=SwitchAsXConfigFlowHandler.MINOR_VERSION,
    )

    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(False)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)


@test.skip("conftest fixtures need migration to _fixtures.py")
async def entity_registry_events() -> None:
    """Stub for test_entity_registry_events (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def device_registry_config_entry_1() -> None:
    """Stub for test_device_registry_config_entry_1 (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def device_registry_config_entry_2() -> None:
    """Stub for test_device_registry_config_entry_2 (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def device_registry_config_entry_3() -> None:
    """Stub for test_device_registry_config_entry_3 (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def config_entry_entity_id() -> None:
    """Stub for test_config_entry_entity_id (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def config_entry_uuid() -> None:
    """Stub for test_config_entry_uuid (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def device() -> None:
    """Stub for test_device (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_and_remove_config_entry() -> None:
    """Stub for test_setup_and_remove_config_entry (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def reset_hidden_by() -> None:
    """Stub for test_reset_hidden_by (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def entity_category_inheritance() -> None:
    """Stub for test_entity_category_inheritance (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def entity_options() -> None:
    """Stub for test_entity_options (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def entity_name() -> None:
    """Stub for test_entity_name (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def custom_name_1() -> None:
    """Stub for test_custom_name_1 (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def custom_name_2() -> None:
    """Stub for test_custom_name_2 (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def import_expose_settings_1() -> None:
    """Stub for test_import_expose_settings_1 (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def import_expose_settings_2() -> None:
    """Stub for test_import_expose_settings_2 (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def restore_expose_settings() -> None:
    """Stub for test_restore_expose_settings (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate() -> None:
    """Stub for test_migrate (port deferred)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_from_future() -> None:
    """Stub for test_migrate_from_future (port deferred)."""
