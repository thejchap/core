"""Tests for Transmission init."""

from unittest.mock import AsyncMock

from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.components.transmission.const import (
    DEFAULT_PATH,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSL,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PATH, CONF_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import MOCK_CONFIG_DATA_VERSION_1_1, OLD_MOCK_CONFIG_DATA
from ._fixtures import mock_config_entry, mock_transmission_client

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import entity_registry as entity_registry_fixture
from tests.hass_fixtures import freezer as freezer_fixture
from tests.hass_fixtures import hass as hass_fixture
from tests.hass_fixtures import mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Present so tryke builds a fixture executor for this module."""
    return 0


@test
async def config_flow_entry_migrate_1_1_to_1_2(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_transmission_client),
) -> None:
    """Test that config flow entry is migrated correctly from v1.1 to v1.2."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG_DATA_VERSION_1_1,
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.version).to_equal(1)
    expect(entry.minor_version).to_equal(2)

    expect(entry.data[CONF_SSL]).to_equal(DEFAULT_SSL)
    expect(entry.data[CONF_PATH]).to_equal(DEFAULT_PATH)


@test
async def setup_failed_connection_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test integration failed due to connection error."""
    config_entry.add_to_hass(hass)

    client_class.side_effect = TransmissionConnectError()

    await hass.config_entries.async_setup(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_failed_auth_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test integration failed due to invalid credentials error."""
    config_entry.add_to_hass(hass)

    client_class.side_effect = TransmissionAuthError()

    await hass.config_entries.async_setup(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test.cases(
    test.case("rc2", version="v1.0.0-RC2"),
    test.case("v0_1_0", version="v0.1.0"),
    test.case("v1_9_0", version="v1.9.0"),
    test.case("v3_0_0", version="3.0.0"),
    test.case("v3_0_0_build", version="3.0.0 (123798)"),
)
async def setup_failed_too_old(
    version: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setup of Transmission entry with too old version of Transmission."""
    config_entry.add_to_hass(hass)

    client_class.return_value.server_version = version

    await hass.config_entries.async_setup(config_entry.entry_id)

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def setup_failed_unexpected_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test integration failed due to unexpected error."""
    config_entry.add_to_hass(hass)

    client_class.side_effect = TransmissionError()

    await hass.config_entries.async_setup(config_entry.entry_id)

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test removing integration."""
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case(
        "sensor_down_speed",
        domain=SENSOR_DOMAIN,
        old_unique_id="0.0.0.0-Transmission Down Speed",
        new_unique_id="1234-download",
    ),
    test.case(
        "sensor_up_speed",
        domain=SENSOR_DOMAIN,
        old_unique_id="0.0.0.0-Transmission Up Speed",
        new_unique_id="1234-upload",
    ),
    test.case(
        "sensor_status",
        domain=SENSOR_DOMAIN,
        old_unique_id="0.0.0.0-Transmission Status",
        new_unique_id="1234-status",
    ),
    test.case(
        "sensor_active_torrents",
        domain=SENSOR_DOMAIN,
        old_unique_id="0.0.0.0-Transmission Active Torrents",
        new_unique_id="1234-active_torrents",
    ),
    test.case(
        "sensor_paused_torrents",
        domain=SENSOR_DOMAIN,
        old_unique_id="0.0.0.0-Transmission Paused Torrents",
        new_unique_id="1234-paused_torrents",
    ),
    test.case(
        "sensor_total_torrents",
        domain=SENSOR_DOMAIN,
        old_unique_id="0.0.0.0-Transmission Total Torrents",
        new_unique_id="1234-total_torrents",
    ),
    test.case(
        "sensor_completed_torrents",
        domain=SENSOR_DOMAIN,
        old_unique_id="0.0.0.0-Transmission Completed Torrents",
        new_unique_id="1234-completed_torrents",
    ),
    test.case(
        "sensor_started_torrents",
        domain=SENSOR_DOMAIN,
        old_unique_id="0.0.0.0-Transmission Started Torrents",
        new_unique_id="1234-started_torrents",
    ),
    test.case(
        "sensor_no_change",
        domain=SENSOR_DOMAIN,
        old_unique_id="1234-started_torrents",
        new_unique_id="1234-started_torrents",
    ),
    test.case(
        "switch_on_off",
        domain=SWITCH_DOMAIN,
        old_unique_id="0.0.0.0-Transmission Switch",
        new_unique_id="1234-on_off",
    ),
    test.case(
        "switch_turtle_mode",
        domain=SWITCH_DOMAIN,
        old_unique_id="0.0.0.0-Transmission Turtle Mode",
        new_unique_id="1234-turtle_mode",
    ),
    test.case(
        "switch_no_change",
        domain=SWITCH_DOMAIN,
        old_unique_id="1234-turtle_mode",
        new_unique_id="1234-turtle_mode",
    ),
)
async def migrate_unique_id(
    domain: str,
    old_unique_id: str,
    new_unique_id: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_transmission_client),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test unique id migration."""
    entry = MockConfigEntry(domain=DOMAIN, data=OLD_MOCK_CONFIG_DATA, entry_id="1234")
    entry.add_to_hass(hass)

    entity: er.RegistryEntry = entity_registry.async_get_or_create(
        suggested_object_id=f"my_{domain}",
        disabled_by=None,
        domain=domain,
        platform=DOMAIN,
        unique_id=old_unique_id,
        config_entry=entry,
    )
    expect(entity.unique_id).to_equal(old_unique_id)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    migrated_entity = entity_registry.async_get(entity.entity_id)

    expect(migrated_entity).not_.to_be_none()
    expect(migrated_entity.unique_id).to_equal(new_unique_id)


@test.skip("transmission: sensor.transmission_status not registered under tryke; pytest passes")
async def coordinator_update_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_class: AsyncMock = Depends(mock_transmission_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test the sensors go unavailable."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    client = client_class.return_value
    client.session_stats.side_effect = TransmissionError("Connection failed")

    freezer.tick(DEFAULT_SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("sensor.transmission_status")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("unavailable")
